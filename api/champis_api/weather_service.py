"""Assemble les séries d'une cellule et calcule M, M_eff et Φ par espèce, jour et classe d'altitude.

Réponse `/weather` (skill open-meteo) : pour chaque jour de J−3 à J+7, par classe d'altitude de la
cellule, `M`, `M_eff`, `phi` et le détail des facteurs — la fiche « pourquoi c'est vert » en dépend.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from champis_pipeline import SCORING_VERSION
from champis_pipeline.species import all_species_hash, load_species

from .grid import Cell
from .scoring import DailySeries, phenology_window, required_series_days, weather_index
from .weather_client import CellRaw, soil_percentile

DAYS_BEFORE = 3
DAYS_AFTER = 7


class SeriesGapError(Exception):
    """Trou ou troncature dans les séries : jamais une approximation silencieuse (SCHEMA.md)."""


def build_series(raw: CellRaw) -> DailySeries:
    """Archive (pluie seule, J−200 → J−93) puis prévision (tout, J−92 → J+7), sans trou.

    Avant la fenêtre prévision, seule la pluie est lue (facteur `memory`) ; les autres variables
    sont mises à 0 et ne sont jamais consultées : les fenêtres des autres facteurs (≤ 32 j) ne
    remontent pas au-delà de J−3−12−32 = J−47.
    """
    f, a = raw.forecast, raw.archive_rain
    f_dates = [date.fromisoformat(d) for d in f["dates"]]
    a_dates = [date.fromisoformat(d) for d in a["dates"]]
    first_f = f_dates[0]
    keep = [i for i, d in enumerate(a_dates) if d < first_f]
    if keep and a_dates[keep[-1]] + timedelta(days=1) != first_f:
        raise SeriesGapError(
            f"trou entre l'archive ({a_dates[keep[-1]]}) et la prévision ({first_f})"
        )
    n_a = len(keep)
    zeros = [0.0] * n_a
    kept_dates = [a_dates[i] for i in keep]
    rain = _nums("archive rain_sum", [a["rain"][i] for i in keep], kept_dates) + _nums(
        "rain_sum", f["rain"], f_dates
    )
    soil_pct = [
        soil_percentile(v, raw.soil_clim, d) for v, d in zip(f["soil"], f_dates, strict=True)
    ]
    missing = [d.isoformat() for v, d in zip(soil_pct, f_dates, strict=True) if v is None]
    if missing:
        raise SeriesGapError(f"humidité du sol manquante dans la prévision : {_summary(missing)}")
    return DailySeries(
        dates=kept_dates + f_dates,
        t_mean=zeros + _nums("temperature_2m_mean", f["t_mean"], f_dates),
        t_min=zeros + _nums("temperature_2m_min", f["t_min"], f_dates),
        t_max=zeros + _nums("temperature_2m_max", f["t_max"], f_dates),
        rain=rain,
        snow=zeros + _nums("snowfall_sum", f["snow"], f_dates),
        et0=zeros + _nums("et0_fao_evapotranspiration", f["et0"], f_dates),
        soil_moisture_pct=zeros + [float(v) for v in soil_pct],  # type: ignore[arg-type]
        cell_elevation_m=float(f["elevation"]),
    )


def _nums(name: str, values: list[Any], dates: list[date]) -> list[float]:
    """Convertit une série ; une valeur manquante est une erreur qui nomme la variable et les dates."""
    missing = [d.isoformat() for v, d in zip(values, dates, strict=True) if v is None]
    if missing:
        raise SeriesGapError(f"`{name}` manquant sur {_summary(missing)}")
    return [float(v) for v in values]


def _summary(dates: list[str]) -> str:
    if len(dates) <= 3:
        return ", ".join(dates)
    return f"{len(dates)} jours ({dates[0]} → {dates[-1]})"


def days_around(today: date) -> list[date]:
    return [today + timedelta(days=k) for k in range(-DAYS_BEFORE, DAYS_AFTER + 1)]


def cell_weather(
    cell: Cell, raw: CellRaw, species_ids: list[str], today: date, detail: bool = True
) -> dict[str, Any]:
    s = build_series(raw)
    days = days_around(today)
    out_species: dict[str, Any] = {}
    for sid in species_ids:
        sp = load_species(sid)
        need = required_series_days(sp)
        if s.i(days[0]) < need:
            raise SeriesGapError(
                f"{sid} : {need} j requis avant {days[0]}, {s.i(days[0])} disponibles"
            )
        day_rows = []
        for d in days:
            by_alt = {}
            for alt in cell.alt_classes:
                w = weather_index(sp, s, d, alt)
                row = {
                    "M": w["M"],
                    "M_eff": w["M_eff"],
                    "phi": phenology_window(sp, d, alt),
                }
                if detail:
                    row["factors"] = {k: v for k, v in w.items() if k not in ("M", "M_eff")}
                by_alt[str(int(alt))] = row
            day_rows.append({"date": d.isoformat(), "by_alt": by_alt})
        out_species[sid] = day_rows
    return {
        "cell": cell.as_dict(),
        "cell_elevation_m": s.cell_elevation_m,
        "today": today.isoformat(),
        "stale": raw.stale,
        "scoring_version": SCORING_VERSION,
        "species_hash": all_species_hash(),
        "species": out_species,
    }
