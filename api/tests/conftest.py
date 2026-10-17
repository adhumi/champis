from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import pytest
import pytest_asyncio
from champis_api.app import State, create_app
from champis_api.cache import WeatherCache
from champis_api.grid import WeatherGrid
from champis_api.scoring import DailySeries
from champis_api.weather_client import OpenMeteoClient
from fixtures.open_meteo import Scenario, transport


def make_series(
    start: date,
    n: int,
    *,
    t_mean: float = 13.0,
    t_min: float = 8.0,
    t_max: float = 18.0,
    rain: float = 2.5,
    snow: float = 0.0,
    et0: float = 1.5,
    soil: float = 0.6,
    elevation: float = 700.0,
) -> DailySeries:
    dates = [start + timedelta(days=i) for i in range(n)]
    return DailySeries(
        dates=dates,
        t_mean=[t_mean] * n,
        t_min=[t_min] * n,
        t_max=[t_max] * n,
        rain=[rain] * n,
        snow=[snow] * n,
        et0=[et0] * n,
        soil_moisture_pct=[soil] * n,
        cell_elevation_m=elevation,
    )


@pytest.fixture
def calm_autumn() -> DailySeries:
    """Automne idéal pour un cèpe : 13 °C, 2,5 mm/j, sol humide, depuis 200 jours."""
    return make_series(date(2026, 3, 1), 260)


# ------------------------------------------------------------------ API : grille, client, app


TODAY = date(2026, 10, 17)
NOW = datetime(2026, 10, 17, 14, 30, tzinfo=ZoneInfo("Europe/Paris"))

GRID = {
    "version": 1,
    "cell_m": 5000,
    "cells": [
        {
            "id": "c_0930_6680",
            "lat": 47.12,
            "lon": 6.31,
            "alt_classes": [450, 1350],
            "elevation_m": 650,
        },
        {"id": "c_0935_6680", "lat": 47.12, "lon": 6.38, "alt_classes": [150], "elevation_m": 180},
    ],
}


@pytest.fixture
def grid(tmp_path: Path) -> WeatherGrid:
    p = tmp_path / "weather_grid.json"
    p.write_text(json.dumps(GRID), encoding="utf-8")
    return WeatherGrid.load(p)


@pytest.fixture
def scenario() -> Scenario:
    return Scenario(elevation=600.0)


def make_client(
    scenario: Scenario, cache: WeatherCache | None = None, now: datetime = NOW
) -> OpenMeteoClient:
    http = httpx.AsyncClient(transport=transport(scenario, TODAY))
    return OpenMeteoClient(http, cache or WeatherCache(), now=lambda: now)


@pytest.fixture
def client(scenario: Scenario) -> OpenMeteoClient:
    return make_client(scenario)


@pytest.fixture
def app(grid: WeatherGrid, client: OpenMeteoClient):
    return create_app(state=State(grid=grid, client=client, cache=client.cache))


@pytest_asyncio.fixture
async def api(app):
    async with app.router.lifespan_context(app):
        transport_ = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport_, base_url="http://test") as c:
            yield c
