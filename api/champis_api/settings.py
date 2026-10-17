"""Configuration par variables d'environnement (préfixe CHAMPIS_)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from champis_pipeline.config import DATA_DIR, ROOT


def _hours(value: str) -> tuple[int, ...]:
    return tuple(int(h) for h in value.split(",") if h.strip())


@dataclass(frozen=True)
class Settings:
    weather_grid: Path = Path(
        os.environ.get("CHAMPIS_WEATHER_GRID", DATA_DIR / "weather_grid.json")
    )
    cache_db: Path = Path(os.environ.get("CHAMPIS_CACHE_DB", DATA_DIR / "weather_cache.db"))
    # Amorçage (historique J−200 → J−1 + climatologie du sol), produit par `champis-api seed`
    weather_seed: Path = Path(
        os.environ.get("CHAMPIS_WEATHER_SEED", DATA_DIR / "weather_seed.json")
    )
    cors_origins: tuple[str, ...] = tuple(
        o for o in os.environ.get("CHAMPIS_CORS_ORIGINS", "*").split(",") if o
    )
    # Heures locales (Europe/Paris) de la pré-chauffe intégrée ; vide = aucune (cron externe)
    warm_hours: tuple[int, ...] = _hours(os.environ.get("CHAMPIS_WARM_HOURS", ""))
    # Pré-chauffer au démarrage (déploiement avec cache vide) ; attention au quota
    warm_on_start: bool = os.environ.get("CHAMPIS_WARM_ON_START", "") == "1"
    # Servir la carte web statique (web/, shared/, species/) sous /web, /shared, /species
    serve_web: bool = os.environ.get("CHAMPIS_SERVE_WEB", "1") == "1"
    repo_root: Path = ROOT
    # Clé API Open-Meteo (plan payant) : hôtes customer-*, quota dédié. Vide = gratuit.
    open_meteo_api_key: str = os.environ.get("CHAMPIS_OPEN_METEO_API_KEY", "")
