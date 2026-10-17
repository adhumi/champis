"""Fausses réponses Open-Meteo, dans la forme exacte de l'API, sans réseau.

Un `Scenario` décrit la météo d'une cellule jour par jour ; `transport(scenario, today)` renvoie
un `httpx.MockTransport` qui répond aux trois requêtes du client (prévision, archive pluie,
climatologie du sol) pour n'importe quel nombre de points.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, timedelta
from urllib.parse import parse_qs, urlparse

import httpx

Daily = Callable[[date], float]


def const(v: float) -> Callable[[], Daily]:
    return lambda: lambda _d: v


@dataclass
class Scenario:
    t_mean: Daily = field(default_factory=const(13.0))
    t_min: Daily = field(default_factory=const(8.0))
    t_max: Daily = field(default_factory=const(18.0))
    rain: Daily = field(default_factory=const(2.5))
    snow: Daily = field(default_factory=const(0.0))
    et0: Daily = field(default_factory=const(1.5))
    soil: Daily = field(
        default_factory=const(0.25)
    )  # m³/m³, le médian de la climatologie ci-dessous → percentile 0,5
    elevation: float = 700.0
    # climatologie : 11 quantiles identiques tous les mois, 0,05 → 0,45 par pas de 0,04
    clim_quantiles: list[float] = field(
        default_factory=lambda: [0.05 + 0.04 * i for i in range(11)]
    )
    fail: set[str] = field(default_factory=set)  # {"forecast", "archive", "climatology"}
    calls: list[str] = field(default_factory=list)
    # jours de prévision renvoyés `null` (toutes variables) : le modèle ne remonte que ~60 j
    forecast_null_before: date | None = None

    def override(self, **per_date: dict[date, float]) -> Scenario:
        for name, table in per_date.items():
            base = getattr(self, name)
            setattr(self, name, lambda d, base=base, table=table: table.get(d, base(d)))
        return self


def _days(start: date, end: date) -> list[date]:
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]


def _daily_body(
    sc: Scenario, days: list[date], soil_layers: list[str], null_before: date | None
) -> dict:
    def col(fn: Daily) -> list[float | None]:
        return [None if null_before and d < null_before else fn(d) for d in days]

    hourly_time, soil_vals = [], []
    for d in days:
        v = None if null_before and d < null_before else sc.soil(d)
        for h in range(24):
            hourly_time.append(f"{d.isoformat()}T{h:02d}:00")
            soil_vals.append(v)
    return {
        "elevation": sc.elevation,
        "daily": {
            "time": [d.isoformat() for d in days],
            "temperature_2m_mean": col(sc.t_mean),
            "temperature_2m_min": col(sc.t_min),
            "temperature_2m_max": col(sc.t_max),
            "rain_sum": col(sc.rain),
            "snowfall_sum": col(sc.snow),
            "et0_fao_evapotranspiration": col(sc.et0),
        },
        "hourly": {"time": hourly_time, **{k: list(soil_vals) for k in soil_layers}},
    }


def _forecast_body(sc: Scenario, today: date, past: int, ahead: int) -> dict:
    days = _days(today - timedelta(days=past), today + timedelta(days=ahead - 1))
    layers = ["soil_moisture_0_to_1cm", "soil_moisture_1_to_3cm", "soil_moisture_3_to_9cm"]
    return _daily_body(sc, days, layers, sc.forecast_null_before)


def _archive_body(sc: Scenario, start: date, end: date) -> dict:
    return _daily_body(sc, _days(start, end), ["soil_moisture_0_to_7cm"], None)


def _climatology_body(sc: Scenario, start: date, end: date) -> dict:
    # Une valeur horaire par quantile, répétée : les quantiles empiriques retombent dessus.
    # 28 j × 24 h minimum par mois → on remplit chaque mois de la période avec le cycle.
    time, vals = [], []
    q = sc.clim_quantiles
    d = start
    i = 0
    while d <= end:
        for h in range(24):
            time.append(f"{d.isoformat()}T{h:02d}:00")
            vals.append(q[i % len(q)])
            i += 1
        d += timedelta(days=1)
    return {"elevation": sc.elevation, "hourly": {"time": time, "soil_moisture_0_to_7cm": vals}}


def transport(sc: Scenario, today: date) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        q = parse_qs(urlparse(str(request.url)).query)
        n = len(q["latitude"][0].split(","))
        host = request.url.host
        if host.startswith("api."):
            kind = "forecast"
            body = _forecast_body(sc, today, int(q["past_days"][0]), int(q["forecast_days"][0]))
        else:
            start, end = (
                date.fromisoformat(q["start_date"][0]),
                date.fromisoformat(q["end_date"][0]),
            )
            if "daily" in q:
                kind = "archive"
                body = _archive_body(sc, start, end)
            else:
                kind = "climatology"
                body = _climatology_body(sc, start, end)
        sc.calls.append(kind)
        if kind in sc.fail:
            return httpx.Response(503, text="Service Unavailable")
        return httpx.Response(200, json=[body] * n if n > 1 else body)

    return httpx.MockTransport(handler)
