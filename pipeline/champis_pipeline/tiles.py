"""Étape « tiles » : mosaïque → Web Mercator → PMTiles de données (T × 254 en gris 8 bits).

Chaîne 100 % Python : rasterio (mosaïque + reprojection par tuile) → PNG 256 px, niveaux 6–15,
plus proche voisin → MBTiles (sqlite) → pmtiles.convert. Les tuiles sont des PNG de données,
non colorisées : la palette est appliquée par les clients. 255 = nodata (alpha 0).
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
from tqdm import tqdm

from . import SCORING_VERSION
from .config import CRS_TILES, T_DIR, TILES_DIR
from .species import species_hash

log = logging.getLogger(__name__)

MIN_ZOOM = 6
MAX_ZOOM = 15
TILE = 256
NODATA = 255


def build(species_id: str, depts: list[str], force: bool = False) -> Path:
    TILES_DIR.mkdir(parents=True, exist_ok=True)
    h = species_hash(species_id)
    dh = hashlib.sha256(",".join(sorted(depts)).encode()).hexdigest()[:6]
    tag = f"{species_id}-{h}-p{SCORING_VERSION}-d{dh}"
    out = TILES_DIR / f"T-{tag}.pmtiles"
    if out.exists() and not force:
        return out

    srcs = [T_DIR / species_id / f"{d}-{h}.tif" for d in depts]
    missing = [p for p in srcs if not p.exists()]
    if missing:
        raise FileNotFoundError(f"T manquants : {missing}")

    work = TILES_DIR / "_work" / tag
    work.mkdir(parents=True, exist_ok=True)
    mosaic = work / "T_2154.tif"
    mbt = work / "T.mbtiles"
    _mosaic(srcs, mosaic)
    _mbtiles(mosaic, mbt, species_id)
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
    profile.update(
        width=data.shape[2],
        height=data.shape[1],
        transform=tr,
        nodata=NODATA,
        compress="DEFLATE",
        tiled=True,
    )
    with rasterio.open(out, "w", **profile) as d:
        d.write(data[0], 1)


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


def _mbtiles(src_path: Path, out: Path, name: str) -> None:
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
                ("name", f"T {name}"),
                ("format", "png"),
                ("type", "overlay"),
                ("version", "1"),
                ("minzoom", str(MIN_ZOOM)),
                ("maxzoom", str(MAX_ZOOM)),
                ("bounds", f"{w},{south},{e},{n}"),
                (
                    "description",
                    "Champis — potentiel terrain, gris 8 bits = T × 254, alpha 0 = hors forêt",
                ),
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
