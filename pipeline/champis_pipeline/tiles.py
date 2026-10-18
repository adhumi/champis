"""Étape « tiles » : mosaïque → Web Mercator → PMTiles de données (T × 254 en gris 8 bits).

Chaîne 100 % Python : rasterio (mosaïque + reprojection par tuile) → PNG 256 px, niveaux 6–15,
plus proche voisin → MBTiles (sqlite) → pmtiles.convert. Les tuiles sont des PNG de données,
non colorisées : la palette est appliquée par les clients. 255 = nodata (alpha 0).

Deuxième couche, commune à toutes les espèces : `A` = classe d'altitude du pixel (gris = indice
k de la classe [300k, 300k+300[ m, centre 300k+150 = la classe que l'API renvoie), produite
depuis `alt.tif` sur toute l'emprise. Les clients y lisent la classe du pixel pour choisir
M_eff et Φ (spec : Points ouverts › classe d'altitude du pixel).
"""

from __future__ import annotations

import hashlib
import io
import logging
import sqlite3
from pathlib import Path

import mercantile
import numpy as np
import rasterio
import rasterio.errors
from PIL import Image
from rasterio.enums import Resampling
from rasterio.merge import merge
from rasterio.transform import from_bounds as transform_from_bounds
from rasterio.warp import reproject, transform_bounds
from rasterio.windows import Window, from_bounds

from . import SCORING_VERSION
from .config import CRS_TILES, T_DIR, TILES_DIR, dept_dirs
from .progress import tqdm
from .scoring import NODATA_U16
from .species import species_hash
from .weather_grid import ALT_CLASS_M

log = logging.getLogger(__name__)

MIN_ZOOM = 6
MAX_ZOOM = 15
TILE = 256
NODATA = 255


def _depts_hash(depts: list[str]) -> str:
    return hashlib.sha256(",".join(sorted(depts)).encode()).hexdigest()[:6]


def build(species_id: str, depts: list[str], force: bool = False) -> Path:
    """`T-<espèce>-<hash espèce>-p<version>-d<hash départements>.pmtiles` : T × 254 en gris."""
    h = species_hash(species_id)
    tag = f"{species_id}-{h}-p{SCORING_VERSION}-d{_depts_hash(depts)}"
    srcs = [T_DIR / species_id / f"{d}-{h}.tif" for d in depts]
    return _build(
        "T",
        tag,
        srcs,
        f"T {species_id}",
        "Champis — potentiel terrain, gris 8 bits = T × 254, alpha 0 = hors forêt",
        force,
    )


def build_alt(depts: list[str], force: bool = False) -> Path:
    """`A-<largeur>m-d<hash départements>.pmtiles` : indice de classe d'altitude, toutes espèces."""
    tag = f"{ALT_CLASS_M}m-d{_depts_hash(depts)}"
    srcs = [dept_dirs(d)["grid"] / "alt.tif" for d in depts]
    return _build(
        "A",
        tag,
        srcs,
        "A classes d'altitude",
        f"Champis — classe d'altitude, gris 8 bits = indice k de [{ALT_CLASS_M}k, "
        f"{ALT_CLASS_M}(k+1)[ m, alpha 0 = altitude inconnue",
        force,
    )


def _build(kind: str, tag: str, srcs: list[Path], name: str, description: str, force: bool) -> Path:
    TILES_DIR.mkdir(parents=True, exist_ok=True)
    out = TILES_DIR / f"{kind}-{tag}.pmtiles"
    if out.exists() and not force:
        return out
    missing = [p for p in srcs if not p.exists()]
    if missing:
        raise FileNotFoundError(f"{kind} manquants : {missing}")

    work = TILES_DIR / "_work" / f"{kind}-{tag}"
    work.mkdir(parents=True, exist_ok=True)
    mosaic = work / f"{kind}_2154.tif"
    mbt = work / f"{kind}.mbtiles"
    (_mosaic if kind == "T" else _mosaic_alt)(srcs, mosaic)
    _mbtiles(mosaic, mbt, name, description)
    from pmtiles.convert import mbtiles_to_pmtiles

    out.unlink(missing_ok=True)
    mbtiles_to_pmtiles(str(mbt), str(out), MAX_ZOOM)
    log.info("écrit %s", out)
    return out


def _mosaic(srcs: list[Path], out: Path) -> None:
    handles = [rasterio.open(p) for p in srcs]
    data, tr = merge(handles, nodata=NODATA, dtype="uint8")
    profile = handles[0].profile.copy()
    for h in handles:
        h.close()
    _write_mosaic(out, data[0], tr, profile)


def _mosaic_alt(srcs: list[Path], out: Path) -> None:
    """alt.tif (uint16 m) → indice de classe uint8 ; altitude inconnue → NODATA."""
    handles = [rasterio.open(p) for p in srcs]
    data, tr = merge(handles, nodata=NODATA_U16, dtype="uint16")
    profile = handles[0].profile.copy()
    for h in handles:
        h.close()
    alt = data[0]
    cls = np.where(alt == NODATA_U16, NODATA, np.minimum(alt // ALT_CLASS_M, NODATA - 1))
    profile["dtype"] = "uint8"
    _write_mosaic(out, cls.astype(np.uint8), tr, profile)


def alt_class_center(index: int) -> int:
    """Centre (m) de la classe d'indice k, tel que `weather_grid` et l'API le nomment."""
    return index * ALT_CLASS_M + ALT_CLASS_M // 2


def _write_mosaic(out: Path, data: np.ndarray, tr, profile: dict) -> None:
    profile.update(
        width=data.shape[1],
        height=data.shape[0],
        transform=tr,
        nodata=NODATA,
        compress="DEFLATE",
        tiled=True,
    )
    with rasterio.open(out, "w", **profile) as d:
        d.write(data, 1)


def _png(arr: np.ndarray) -> bytes:
    """Gris 8 bits + alpha (0 sur nodata) → PNG."""
    alpha = np.where(arr == NODATA, 0, 255).astype(np.uint8)
    img = Image.fromarray(np.dstack([arr, alpha]), mode="LA")
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=False, compress_level=6)
    return buf.getvalue()


def _render_tile(src: rasterio.DatasetReader, t: mercantile.Tile) -> np.ndarray | None:
    """Lit la fenêtre source couvrant la tuile, la reprojette en 256×256 Web Mercator."""
    b = mercantile.xy_bounds(t)
    sw, ss, se, sn = transform_bounds(CRS_TILES, src.crs, b.left, b.bottom, b.right, b.top)
    win = from_bounds(sw, ss, se, sn, src.transform).round_offsets().round_lengths()
    full = Window(0, 0, src.width, src.height)
    try:
        win = win.intersection(full)
    except (ValueError, rasterio.errors.WindowError):  # pas de recouvrement
        return None
    if win.width < 1 or win.height < 1:
        return None
    data = src.read(1, window=win)
    if np.all(data == NODATA):
        return None
    dst = np.full((TILE, TILE), NODATA, dtype=np.uint8)
    reproject(
        data,
        dst,
        src_transform=src.window_transform(win),
        src_crs=src.crs,
        dst_transform=transform_from_bounds(b.left, b.bottom, b.right, b.top, TILE, TILE),
        dst_crs=CRS_TILES,
        resampling=Resampling.nearest,
        src_nodata=NODATA,
        dst_nodata=NODATA,
    )
    return None if np.all(dst == NODATA) else dst


def _mbtiles(src_path: Path, out: Path, name: str, description: str) -> None:
    out.unlink(missing_ok=True)
    db = sqlite3.connect(out)
    db.executescript(
        """
        CREATE TABLE metadata (name TEXT, value TEXT);
        CREATE TABLE tiles (zoom_level INTEGER, tile_column INTEGER, tile_row INTEGER, tile_data BLOB);
        CREATE UNIQUE INDEX tile_index ON tiles (zoom_level, tile_column, tile_row);
        """
    )
    with rasterio.open(src_path) as src:
        w, south, e, n = transform_bounds(src.crs, "EPSG:4326", *src.bounds)
        db.executemany(
            "INSERT INTO metadata VALUES (?, ?)",
            [
                ("name", name),
                ("format", "png"),
                ("type", "overlay"),
                ("version", "1"),
                ("minzoom", str(MIN_ZOOM)),
                ("maxzoom", str(MAX_ZOOM)),
                ("bounds", f"{w},{south},{e},{n}"),
                ("description", description),
            ],
        )
        for z in range(MIN_ZOOM, MAX_ZOOM + 1):
            rows: list[tuple[int, int, int, bytes]] = []
            count = 0
            tiles = list(mercantile.tiles(w, south, e, n, [z]))
            for t in tqdm(tiles, desc=f"z{z}", unit="tuile", leave=False):
                arr = _render_tile(src, t)
                if arr is None:
                    continue
                rows.append((z, t.x, (2**z - 1) - t.y, _png(arr)))  # schéma TMS : ligne inversée
                if len(rows) >= 2000:  # jamais tout un niveau en RAM (France z15 ≈ 1,8 M tuiles)
                    db.executemany("INSERT INTO tiles VALUES (?, ?, ?, ?)", rows)
                    db.commit()
                    count += len(rows)
                    rows = []
            db.executemany("INSERT INTO tiles VALUES (?, ?, ?, ?)", rows)
            db.commit()
            count += len(rows)
            log.info("z%d : %d tuiles", z, count)
    db.close()
