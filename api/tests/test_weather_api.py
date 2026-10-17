"""Service HTTP et client Open-Meteo, sur fixtures synthétiques (skill open-meteo : scénarios)."""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from champis_api.cache import WeatherCache
from champis_api.scoring import phenology_window
from champis_api.weather_client import soil_percentile
from champis_api.weather_service import SeriesGapError, build_series, cell_weather
from champis_pipeline.scoring import trapezoid
from champis_pipeline.species import load_species
from conftest import NOW, TODAY, make_client
from fixtures.open_meteo import Scenario

EDULIS = load_species("boletus_edulis")
CELL = "c_0930_6680"
J = TODAY.isoformat()


def _alt(resp: dict, sid: str, day: date, alt: int) -> dict:
    rows = {r["date"]: r for r in resp["species"][sid]}
    return rows[day.isoformat()]["by_alt"][str(alt)]


# ------------------------------------------------------------------ forme des réponses


@pytest.mark.asyncio
async def test_health_and_species(api):
    r = await api.get("/health")
    assert r.json() == {"status": "ok", "cells": 2}
    r = await api.get("/species")
    body = r.json()
    assert body["scoring_version"] == "1.0.0"
    assert body["palette"]["thresholds"][0]["label"] == "excellent"
    assert body["species"]["boletus_edulis"]["group"]["id"] == "cepes"
    assert len(body["species"]) == 7


@pytest.mark.asyncio
async def test_weather_shape(api):
    r = await api.get("/weather", params={"cell": CELL, "species": "boletus_edulis"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["cell"]["id"] == CELL
    assert body["stale"] is False
    assert body["cell_elevation_m"] == 600.0
    rows = body["species"]["boletus_edulis"]
    assert rows[0]["date"] == (TODAY - timedelta(days=3)).isoformat()
    assert len(rows) == 11
    today = _alt(body, "boletus_edulis", TODAY, 450)
    assert set(today) == {"M", "M_eff", "phi"} | {"factors"}
    assert set(today["factors"]) == {
        "temp",
        "rain",
        "trigger",
        "soil_moisture",
        "frost",
        "water_balance",
        "heat",
        "memory",
    }
    assert 0 <= today["M_eff"] <= 1
    assert today["phi"] == phenology_window(EDULIS, TODAY, 450.0)
    assert set(rows[0]["by_alt"]) == {"450", "1350"}


@pytest.mark.asyncio
async def test_weather_by_lat_lon_and_errors(api):
    r = await api.get("/weather", params={"lat": 47.12, "lon": 6.37})
    assert r.json()["cell"]["id"] == "c_0935_6680"
    assert set(r.json()["species"]) == set(load_species_ids())
    assert (await api.get("/weather", params={"cell": "nope"})).status_code == 404
    assert (await api.get("/weather")).status_code == 422
    r = await api.get("/weather", params={"cell": CELL, "species": "amanita_phalloides"})
    assert r.status_code == 404


def load_species_ids() -> list[str]:
    from champis_pipeline.species import list_species

    return list_species()


@pytest.mark.asyncio
async def test_bbox(api):
    r = await api.get(
        "/weather/bbox",
        params={
            "min_lon": 6.3,
            "min_lat": 47.0,
            "max_lon": 6.35,
            "max_lat": 47.2,
            "species": "cantharellus_cibarius",
            "day": J,
        },
    )
    body = r.json()
    assert [c["cell"] for c in body["cells"]] == [CELL]
    rows = body["cells"][0]["species"]["cantharellus_cibarius"]
    assert len(rows) == 1 and rows[0]["date"] == J
    assert "factors" not in rows[0]["by_alt"]["450"]


# ------------------------------------------------------------------ scénarios météo


def _cell(grid):
    return grid.get(CELL)


@pytest.mark.asyncio
async def test_big_rain_then_fair_weather(grid):
    """Grosse pluie J−12, puis beau temps sec : trigger optimal, bilan hydrique neutre."""
    sc = Scenario(elevation=600.0, rain=lambda d: 0.0).override(
        rain={TODAY - timedelta(days=12): 40.0}
    )
    raw = (await make_client(sc).fetch_cells([_cell(grid)]))[CELL]
    resp = cell_weather(_cell(grid), raw, ["boletus_edulis"], TODAY)
    f = _alt(resp, "boletus_edulis", TODAY, 450)["factors"]
    assert f["trigger"] == 1.0  # 12 j ∈ [10, 20]
    assert f["water_balance"] == 1.0  # 40 − 14 × 1,5 = +19 mm


@pytest.mark.asyncio
async def test_best_event_not_last(grid):
    """Petite pluie récente après grosse pluie ancienne : le meilleur événement gagne."""
    old, recent = TODAY - timedelta(days=15), TODAY - timedelta(days=2)
    sc = Scenario(elevation=600.0, rain=lambda d: 0.0).override(rain={old: 25.0, recent: 22.0})
    raw = (await make_client(sc).fetch_cells([_cell(grid)]))[CELL]
    f = _alt(
        cell_weather(_cell(grid), raw, ["boletus_edulis"], TODAY), "boletus_edulis", TODAY, 450
    )
    lag = EDULIS["weather"]["trigger"]["lag_days"]
    assert f["factors"]["trigger"] == max(trapezoid(15, lag), trapezoid(2, lag)) == 1.0


@pytest.mark.asyncio
async def test_snow_is_not_a_trigger(grid):
    day = TODAY - timedelta(days=12)
    sc = Scenario(elevation=600.0, rain=lambda d: 0.0).override(rain={day: 40.0}, snow={day: 5.0})
    raw = (await make_client(sc).fetch_cells([_cell(grid)]))[CELL]
    f = _alt(
        cell_weather(_cell(grid), raw, ["boletus_edulis"], TODAY), "boletus_edulis", TODAY, 450
    )
    assert f["factors"]["trigger"] == 0.0


@pytest.mark.asyncio
async def test_frost_only_at_altitude(grid):
    """Tmin 2 °C à 600 m : pas de gel à 450 m, gel à 1 350 m (2 − 0,006 × 750 = −2,5 °C)."""
    sc = Scenario(elevation=600.0, t_min=lambda d: 2.0)
    raw = (await make_client(sc).fetch_cells([_cell(grid)]))[CELL]
    resp = cell_weather(_cell(grid), raw, ["boletus_edulis"], TODAY)
    low, high = _alt(resp, "boletus_edulis", TODAY, 450), _alt(resp, "boletus_edulis", TODAY, 1350)
    assert low["factors"]["frost"] == 1.0
    assert high["factors"]["frost"] == EDULIS["weather"]["frost"]["factor"]
    assert high["M_eff"] < low["M_eff"]


# ------------------------------------------------------------------ cache et panne


@pytest.mark.asyncio
async def test_cache_hits_within_bucket(grid, scenario):
    client = make_client(scenario)
    cells = [grid.get(CELL), grid.get("c_0935_6680")]
    await client.fetch_cells(cells)
    assert sorted(scenario.calls) == [
        "archive",
        "climatology",
        "forecast",
    ]  # 2 points, 1 appel chacun
    await client.fetch_cells(cells)
    assert len(scenario.calls) == 3  # rien de nouveau dans le même seau de 6 h


@pytest.mark.asyncio
async def test_outage_serves_stale(grid, scenario):
    cache = WeatherCache()
    fresh = (await make_client(scenario, cache).fetch_cells([_cell(grid)]))[CELL]
    scenario.fail = {"forecast", "archive", "climatology"}
    later = make_client(scenario, cache, now=NOW + timedelta(hours=7))  # seau suivant
    stale = (await later.fetch_cells([_cell(grid)]))[CELL]
    assert stale.stale is True
    assert stale.forecast == fresh.forecast


@pytest.mark.asyncio
async def test_outage_without_cache_is_503(api, scenario):
    scenario.fail = {"forecast"}
    r = await api.get("/weather", params={"cell": CELL})
    assert r.status_code == 503
    assert "indisponible" in r.json()["detail"]


# ------------------------------------------------------------------ séries et percentiles


def test_soil_percentile():
    clim = {"months": {"10": [0.05 + 0.04 * i for i in range(11)]}}
    d = date(2026, 10, 17)
    assert soil_percentile(0.01, clim, d) == 0.0
    assert soil_percentile(0.99, clim, d) == 1.0
    assert soil_percentile(0.25, clim, d) == pytest.approx(0.5)
    assert soil_percentile(0.27, clim, d) == pytest.approx(0.55)
    assert soil_percentile(None, clim, d) is None


@pytest.mark.asyncio
async def test_series_gap_is_an_error(grid, scenario):
    raw = (await make_client(scenario).fetch_cells([_cell(grid)]))[CELL]
    raw.archive_rain["dates"] = raw.archive_rain["dates"][:-3]  # l'archive s'arrête trop tôt
    raw.archive_rain["rain"] = raw.archive_rain["rain"][:-3]
    with pytest.raises(SeriesGapError):
        build_series(raw)
