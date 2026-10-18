"""CLI : `champis-pipeline <étape> --dept 25 [--species boletus_edulis] [--force]`.

Étapes : download · grid · terrain · tiles · weather-grid · all · summary · check
"""

from __future__ import annotations

import argparse
import json
import logging
import sys

from . import download, rasterize, terrain, tiles, weather_grid
from .species import list_species


def _species(args) -> list[str]:
    return args.species or list_species()


def cmd_download(args) -> None:
    shp = download.bdforet(args.dept)
    grid = rasterize.dept_grid(shp)
    bbox = rasterize.grid_bbox_4326(grid)
    download.soilgrids_ph(bbox)
    download.copernicus_dem_tiles(bbox)
    print(f"{args.dept}: BD Forêt {shp.name}, grille {grid.width}×{grid.height} px, bbox {bbox}")


def cmd_grid(args) -> None:
    shp = download.bdforet(args.dept)
    grid = rasterize.dept_grid(shp)
    bbox = rasterize.grid_bbox_4326(grid)
    rasterize.host_cover(args.dept, shp, grid, args.force)
    rasterize.ph(args.dept, download.soilgrids_ph(bbox), grid, args.force)
    rasterize.dem_products(args.dept, download.copernicus_dem_tiles(bbox), grid, args.force)
    print(f"{args.dept}: rasters grid prêts")


def cmd_terrain(args) -> None:
    for sid in _species(args):
        print(terrain.compute(args.dept, sid, args.force))


def cmd_tiles(args) -> None:
    for sid in _species(args):
        print(tiles.build(sid, args.depts, args.force))
    print(tiles.build_alt(args.depts, args.force))  # couche A, commune à toutes les espèces


def cmd_weather_grid(args) -> None:
    print(weather_grid.build(args.depts, args.species))


def cmd_summary(args) -> None:
    from .config import T_DIR
    from .species import species_hash

    for sid in _species(args):
        p = T_DIR / sid / f"{args.dept}-{species_hash(sid)}.tif"
        print(sid, json.dumps(terrain.summary(p), indent=1))


def cmd_check(args) -> None:
    """Contrôle GBIF : rapport HTML + JSON par espèce dans reports/ (réseau : api.gbif.org)."""
    import httpx
    import rasterio
    from rasterio.warp import transform_bounds

    from .check import gbif, report
    from .config import T_DIR
    from .species import load_species, species_hash

    with httpx.Client(timeout=60.0, headers={"User-Agent": "champis-pipeline check"}) as http:
        for sid in _species(args):
            t_path = T_DIR / sid / f"{args.dept}-{species_hash(sid)}.tif"
            with rasterio.open(t_path) as s:
                bbox = transform_bounds(s.crs, "EPSG:4326", *s.bounds)
            occ, rejected = gbif.occurrences(
                sid, load_species(sid)["names"]["la"], bbox, http, force=args.force
            )
            result = report.evaluate(args.dept, sid, occ, rejected=rejected)
            path = report.write_report(result, occ)
            print(
                f"{sid}: AUC {result['auc']:.3f} ({result['n_in_forest']}/{result['n_occurrences']} occ. en forêt) → {path}"
            )


def cmd_all(args) -> None:
    cmd_download(args)
    cmd_grid(args)
    cmd_terrain(args)
    args.depts = [args.dept]
    cmd_tiles(args)
    cmd_weather_grid(args)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser(prog="champis-pipeline")
    ap.add_argument("--species", action="append", help="id d'espèce (répétable) ; défaut : toutes")
    ap.add_argument("--force", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (
        ("download", cmd_download),
        ("grid", cmd_grid),
        ("terrain", cmd_terrain),
        ("summary", cmd_summary),
        ("check", cmd_check),
        ("all", cmd_all),
    ):
        p = sub.add_parser(name)
        p.add_argument("--dept", required=True)
        p.set_defaults(fn=fn)
    for name, fn in (("tiles", cmd_tiles), ("weather-grid", cmd_weather_grid)):
        p = sub.add_parser(name)
        p.add_argument("--depts", nargs="+", required=True)
        p.set_defaults(fn=fn)
    args = ap.parse_args(argv)
    args.fn(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
