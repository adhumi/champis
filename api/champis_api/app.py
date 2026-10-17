"""Service champis-api : `/species`, `/weather`, `/weather/bbox`, `/health`.

Sans état hors le cache météo SQLite ; aucun calcul géographique (tout est dans les tuiles).
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .cache import WeatherCache
from .grid import WeatherGrid
from .routers import species, weather
from .settings import Settings
from .weather_client import OpenMeteoClient


@dataclass
class State:
    grid: WeatherGrid
    client: OpenMeteoClient
    cache: WeatherCache


def create_app(settings: Settings | None = None, state: State | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if state is not None:
            app.state.champis = state
            yield
            return
        settings.cache_db.parent.mkdir(parents=True, exist_ok=True)
        cache = WeatherCache(settings.cache_db)
        async with httpx.AsyncClient(headers={"User-Agent": "champis-api"}) as http:
            app.state.champis = State(
                grid=WeatherGrid.load(settings.weather_grid),
                client=OpenMeteoClient(http, cache),
                cache=cache,
            )
            yield
        cache.close()

    app = FastAPI(title="Champis API", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware, allow_origins=list(settings.cors_origins), allow_methods=["GET"]
    )
    app.include_router(species.router)
    app.include_router(weather.router)

    @app.get("/health")
    async def health() -> dict[str, str | int]:
        return {"status": "ok", "cells": len(app.state.champis.grid)}

    return app


app = create_app()
