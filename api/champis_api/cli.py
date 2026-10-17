"""CLI : `champis-api warm [--interval 2]` — pré-chauffe du cache météo (cron)."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

import httpx

from .cache import WeatherCache
from .grid import WeatherGrid
from .settings import Settings
from .warm import WARM_INTERVAL_S, warm
from .weather_client import OpenMeteoClient


async def _warm(interval: float) -> int:
    settings = Settings()
    grid = WeatherGrid.load(settings.weather_grid)
    settings.cache_db.parent.mkdir(parents=True, exist_ok=True)
    cache = WeatherCache(settings.cache_db)
    try:
        async with httpx.AsyncClient(headers={"User-Agent": "champis-api warm"}) as http:
            client = OpenMeteoClient(
                http, cache, min_interval_s=interval, api_key=settings.open_meteo_api_key
            )
            report = await warm(grid, client)
    finally:
        cache.close()
    print(
        f"{report.cells} cellules, {len(report.unavailable)} indisponibles, "
        f"{report.stale} servies depuis un cache périmé"
    )
    for cid, reason in sorted(report.unavailable.items()):
        print(f"  {cid}: {reason}")
    return 0 if report.ok else 1


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser(prog="champis-api")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("warm", help="remplit le cache météo pour toute la grille")
    p.add_argument(
        "--interval", type=float, default=WARM_INTERVAL_S, help="secondes entre requêtes"
    )
    args = ap.parse_args(argv)
    return asyncio.run(_warm(args.interval))


if __name__ == "__main__":
    sys.exit(main())
