"""Amorçage : historique J−200 → J−1 et climatologie du sol depuis l'archive ERA5-Land gratuite.

À lancer **hors Railway** (`champis-api seed`, depuis un poste dont l'IP n'est pas bridée), une fois
par grille. Le résultat, `data/weather_seed.json`, est versionné et embarqué dans l'image ; l'API
l'importe au démarrage dans SQLite (`history` source `seed`, jamais par-dessus la prévision ;
`soil_clim`). Reprise : les cellules déjà présentes dans le fichier ne sont pas refaites.
"""

from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path
from typing import Any

from .cache import WeatherCache
from .grid import WeatherGrid
from .weather_client import OpenMeteoClient

log = logging.getLogger(__name__)

SEED_VERSION = 1


def load_seed(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": SEED_VERSION, "generated": None, "cells": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != SEED_VERSION:
        raise ValueError(f"weather_seed.json version {data.get('version')!r} inconnue")
    return data


def save_seed(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.part")
    tmp.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    tmp.replace(path)


async def seed(
    grid: WeatherGrid, client: OpenMeteoClient, out: Path, today: date | None = None
) -> dict[str, Any]:
    """Complète `out` avec les cellules de la grille qui y manquent ; écrit après chaque cellule."""
    today = today or client.today()
    data = load_seed(out)
    todo = [c for c in grid.cells.values() if c.id not in data["cells"]]
    log.info("amorçage : %d cellules à faire, %d déjà présentes", len(todo), len(data["cells"]))
    for i, cell in enumerate(todo, 1):
        rows, clim = await client.fetch_seed(cell, today)
        data["cells"][cell.id] = {"history": rows, "soil_clim": clim["months"]}
        data["generated"] = today.isoformat()
        save_seed(out, data)
        log.info("amorçage %d/%d : %s (%d jours)", i, len(todo), cell.id, len(rows))
    return data


def import_seed(cache: WeatherCache, path: Path) -> int:
    """Charge le fichier d'amorçage dans SQLite. Renvoie le nombre de cellules importées."""
    data = load_seed(path)
    for cid, c in data["cells"].items():
        cache.put_history(cid, c["history"], "seed")
        cache.put_soil_clim(cid, c["soil_clim"])
    return len(data["cells"])
