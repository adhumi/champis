"""Configuration par variables d'environnement (préfixe CHAMPIS_)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from champis_pipeline.config import DATA_DIR


@dataclass(frozen=True)
class Settings:
    weather_grid: Path = Path(
        os.environ.get("CHAMPIS_WEATHER_GRID", DATA_DIR / "weather_grid.json")
    )
    cache_db: Path = Path(os.environ.get("CHAMPIS_CACHE_DB", DATA_DIR / "weather_cache.db"))
    cors_origins: tuple[str, ...] = tuple(
        o for o in os.environ.get("CHAMPIS_CORS_ORIGINS", "*").split(",") if o
    )
