"""Client Open-Meteo : le seul module qui parle à api.open-meteo.com (skill open-meteo).

Trois jeux de données par cellule, chacun normalisé puis mis en cache (`cache.py`) :

- `forecast`  : API prévision, `past_days=92&forecast_days=8` (J inclus → J+7), séries journalières + humidité du
  sol (moyenne journalière pondérée des couches 0–1, 1–3 et 3–9 cm, poids 1/2/6 : c'est la
  couche 0–9 cm, l'équivalent prévision du 0–7 cm ERA5-Land). Seau de 6 h.
- `archive_rain` : API archive (ERA5-Land), `rain_sum` de J−200 à J−93 pour la mémoire estivale.
  Un seau par jour.
- `soil_clim` : API archive, humidité du sol 0–7 cm horaire sur 10 ans, réduite en 11 quantiles
  par mois ; sert à exprimer l'humidité du jour en percentile. Permanent (seau `v1`).

Si Open-Meteo est injoignable, on sert la dernière réponse connue avec `stale=True` ; sans
aucune réponse connue, `WeatherUnavailableError`.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

import httpx
import numpy as np

from .cache import WeatherCache, bucket_now
from .grid import Cell

log = logging.getLogger(__name__)

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
TIMEZONE = "Europe/Paris"
PAST_DAYS = 92
FORECAST_DAYS = 8  # J inclus : J+1 … J+7
ARCHIVE_START_OFFSET = 200  # J−200 : couvre mémoire (90) + pluie (28) + persistance (12) + J−3
CLIMATOLOGY_YEARS = 10
QUANTILES = [i / 10 for i in range(11)]
BATCH_POINTS = 100
BATCH_CLIMATOLOGY = 10
SOIL_LAYER_WEIGHTS = {
    "soil_moisture_0_to_1cm": 1,
    "soil_moisture_1_to_3cm": 2,
    "soil_moisture_3_to_9cm": 6,
}

DAILY_VARS = [
    "temperature_2m_mean",
    "temperature_2m_min",
    "temperature_2m_max",
    "rain_sum",
    "snowfall_sum",
    "et0_fao_evapotranspiration",
]


class WeatherUnavailableError(Exception):
    """Open-Meteo injoignable et aucune réponse en cache pour cette cellule."""


@dataclass
class CellRaw:
    forecast: dict[str, Any]
    archive_rain: dict[str, Any]
    soil_clim: dict[str, Any]
    stale: bool


class OpenMeteoClient:
    def __init__(
        self,
        http: httpx.AsyncClient,
        cache: WeatherCache,
        now: Callable[[], datetime] | None = None,
    ):
        self.http = http
        self.cache = cache
        self.now = now or (lambda: datetime.now().astimezone())

    def today(self) -> date:
        return self.now().date()

    # ------------------------------------------------------------------ public

    async def fetch_cells(self, cells: Iterable[Cell]) -> dict[str, CellRaw]:
        cells = list(cells)
        now = self.now()
        today = now.date()
        buckets = {
            "forecast": bucket_now(now),
            "archive_rain": today.isoformat(),
            "soil_clim": "v1",
        }
        out: dict[str, dict[str, Any]] = {c.id: {"stale": False} for c in cells}
        for kind, bucket in buckets.items():
            missing: list[Cell] = []
            for c in cells:
                cached = self.cache.get(c.id, kind, bucket)
                if cached is None:
                    missing.append(c)
                else:
                    out[c.id][kind] = cached
            size = BATCH_CLIMATOLOGY if kind == "soil_clim" else BATCH_POINTS
            for i in range(0, len(missing), size):
                batch = missing[i : i + size]
                try:
                    payloads = await self._fetch(kind, batch, today)
                except (httpx.HTTPError, ValueError) as e:
                    log.warning("Open-Meteo %s injoignable (%s) : cache périmé", kind, e)
                    for c in batch:
                        last = self.cache.latest(c.id, kind)
                        if last is None:
                            raise WeatherUnavailableError(f"{kind} indisponible pour {c.id}") from e
                        out[c.id][kind] = last[0]
                        out[c.id]["stale"] = True
                    continue
                for c, p in zip(batch, payloads, strict=True):
                    self.cache.put(c.id, kind, bucket, p, now)
                    out[c.id][kind] = p
        return {cid: CellRaw(**v) for cid, v in out.items()}

    # ------------------------------------------------------------------ requêtes

    async def _fetch(self, kind: str, batch: list[Cell], today: date) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "latitude": ",".join(f"{c.lat:.4f}" for c in batch),
            "longitude": ",".join(f"{c.lon:.4f}" for c in batch),
            "timezone": TIMEZONE,
        }
        if kind == "forecast":
            params |= {
                "daily": ",".join(DAILY_VARS),
                "hourly": ",".join(SOIL_LAYER_WEIGHTS),
                "past_days": PAST_DAYS,
                "forecast_days": FORECAST_DAYS,
            }
            url, norm = FORECAST_URL, _normalize_forecast
        elif kind == "archive_rain":
            params |= {
                "daily": "rain_sum",
                "start_date": (today - timedelta(days=ARCHIVE_START_OFFSET)).isoformat(),
                "end_date": (today - timedelta(days=PAST_DAYS + 1)).isoformat(),
            }
            url, norm = ARCHIVE_URL, _normalize_archive_rain
        else:
            params |= {
                "hourly": "soil_moisture_0_to_7cm",
                "start_date": f"{today.year - CLIMATOLOGY_YEARS}-01-01",
                "end_date": f"{today.year - 1}-12-31",
            }
            url, norm = ARCHIVE_URL, _normalize_soil_climatology
        r = await self.http.get(url, params=params, timeout=60.0)
        r.raise_for_status()
        body = r.json()
        items = body if isinstance(body, list) else [body]
        if len(items) != len(batch):
            raise ValueError(f"{len(items)} réponses pour {len(batch)} points")
        return [norm(it) for it in items]


# ---------------------------------------------------------------------- normalisation


def _normalize_forecast(body: dict[str, Any]) -> dict[str, Any]:
    d = body["daily"]
    h = body["hourly"]
    soil_by_day: dict[str, list[float]] = {}
    for i, ts in enumerate(h["time"]):
        vals = [h[k][i] for k in SOIL_LAYER_WEIGHTS]
        if any(v is None for v in vals):
            continue
        w = sum(SOIL_LAYER_WEIGHTS.values())
        v = sum(SOIL_LAYER_WEIGHTS[k] * h[k][i] for k in SOIL_LAYER_WEIGHTS) / w
        soil_by_day.setdefault(ts[:10], []).append(v)
    soil = [
        (sum(soil_by_day[day]) / len(soil_by_day[day])) if soil_by_day.get(day) else None
        for day in d["time"]
    ]
    return {
        "elevation": float(body["elevation"]),
        "dates": d["time"],
        "t_mean": d["temperature_2m_mean"],
        "t_min": d["temperature_2m_min"],
        "t_max": d["temperature_2m_max"],
        "rain": d["rain_sum"],
        "snow": d["snowfall_sum"],
        "et0": d["et0_fao_evapotranspiration"],
        "soil": soil,
    }


def _normalize_archive_rain(body: dict[str, Any]) -> dict[str, Any]:
    d = body["daily"]
    return {"dates": d["time"], "rain": d["rain_sum"]}


def _normalize_soil_climatology(body: dict[str, Any]) -> dict[str, Any]:
    """11 quantiles (0, 10, … 100 %) de l'humidité 0–7 cm par mois civil."""
    h = body["hourly"]
    by_month: dict[int, list[float]] = {m: [] for m in range(1, 13)}
    for ts, v in zip(h["time"], h["soil_moisture_0_to_7cm"], strict=True):
        if v is not None:
            by_month[int(ts[5:7])].append(v)
    months = {}
    for m, vals in by_month.items():
        if len(vals) < 24 * 28:  # moins d'un mois d'heures : climatologie inexploitable
            raise ValueError(f"climatologie du sol trop courte pour le mois {m}")
        months[str(m)] = [float(q) for q in np.quantile(vals, QUANTILES)]
    return {"months": months}


def soil_percentile(value: float | None, clim: dict[str, Any], day: date) -> float | None:
    """Percentile 0–1 de `value` dans la climatologie du mois de `day` (interpolation linéaire)."""
    if value is None:
        return None
    q = clim["months"][str(day.month)]
    if value <= q[0]:
        return 0.0
    if value >= q[-1]:
        return 1.0
    for i in range(1, len(q)):
        if value <= q[i]:
            lo, hi = q[i - 1], q[i]
            frac = 0.0 if hi == lo else (value - lo) / (hi - lo)
            return QUANTILES[i - 1] + frac * (QUANTILES[i] - QUANTILES[i - 1])
    return 1.0
