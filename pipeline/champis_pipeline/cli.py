"""CLI : `champis-pipeline <étape> --dept 25 [--species boletus_edulis] [--force]`.

Étapes : download · grid · terrain · tiles · all · summary
"""

from __future__ import annotations

import argparse
import json
import logging
import sys

from . import download, rasterize, terrain, tiles
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


def cmd_summary(args) -> None:
    from .config import T_DIR
    from .species import species_hash

    for sid in _species(args):
        p = T_DIR / sid / f"{args.dept}-{species_hash(sid)}.tif"
        print(sid, json.dumps(terrain.summary(p), indent=1))


def cmd_all(args) -> None:
    cmd_download(args)
    cmd_grid(args)
    cmd_terrain(args)
    args.depts = [args.dept]
    cmd_tiles(args)


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
        ("all", cmd_all),
    ):
        p = sub.add_parser(name)
        p.add_argument("--dept", required=True)
        p.set_defaults(fn=fn)
    p = sub.add_parser("tiles")
    p.add_argument("--depts", nargs="+", required=True)
    p.set_defaults(fn=cmd_tiles)
    args = ap.parse_args(argv)
    args.fn(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
