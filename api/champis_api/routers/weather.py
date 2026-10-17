"""`GET /weather` (une cellule, détail des facteurs) et `GET /weather/bbox` (peindre une emprise)."""

from __future__ import annotations

from datetime import date
from typing import Annotated, Any

from champis_pipeline.species import list_species
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from ..grid import Cell, WeatherGrid
from ..weather_client import OpenMeteoClient, WeatherUnavailableError
from ..weather_service import SeriesGapError, cell_weather

router = APIRouter(prefix="/weather", tags=["weather"])


def _grid(request: Request) -> WeatherGrid:
    return request.app.state.champis.grid


def _client(request: Request) -> OpenMeteoClient:
    return request.app.state.champis.client


def _species(species: Annotated[list[str] | None, Query()] = None) -> list[str]:
    known = list_species()
    if not species:
        return known
    unknown = [s for s in species if s not in known]
    if unknown:
        raise HTTPException(404, f"espèce(s) inconnue(s) : {unknown}")
    return species


Grid = Annotated[WeatherGrid, Depends(_grid)]
Client = Annotated[OpenMeteoClient, Depends(_client)]
Species = Annotated[list[str], Depends(_species)]


async def _compute(
    client: OpenMeteoClient, cells: list[Cell], species: list[str], detail: bool
) -> list[dict[str, Any]]:
    try:
        raws = await client.fetch_cells(cells)
        today = client.today()
        return [cell_weather(c, raws[c.id], species, today, detail=detail) for c in cells]
    except WeatherUnavailableError as e:
        raise HTTPException(503, f"météo indisponible : {e}") from e
    except SeriesGapError as e:
        raise HTTPException(502, f"séries Open-Meteo incomplètes : {e}") from e


@router.get("")
async def get_weather(
    grid: Grid,
    client: Client,
    species: Species,
    cell: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
) -> dict[str, Any]:
    if cell is not None:
        c = grid.get(cell)
        if c is None:
            raise HTTPException(404, f"cellule inconnue : {cell}")
    elif lat is not None and lon is not None:
        c = grid.nearest(lat, lon)
        if c is None:
            raise HTTPException(404, "grille météo vide")
    else:
        raise HTTPException(422, "préciser cell=<id> ou lat=&lon=")
    return (await _compute(client, [c], species, detail=True))[0]


@router.get("/bbox")
async def get_weather_bbox(
    grid: Grid,
    client: Client,
    species: Species,
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
    day: date | None = None,
) -> dict[str, Any]:
    """Par cellule de l'emprise : `M_eff` et `phi` par classe d'altitude, sans détail des facteurs.

    `day` filtre sur un seul jour (défaut : les 11 jours J−3 → J+7).
    """
    cells = grid.in_bbox(min_lon, min_lat, max_lon, max_lat)
    results = await _compute(client, cells, species, detail=False)
    out = []
    for r in results:
        sp = {}
        for sid, rows in r["species"].items():
            if day is not None:
                rows = [row for row in rows if row["date"] == day.isoformat()]
            sp[sid] = rows
        out.append({"cell": r["cell"]["id"], "stale": r["stale"], "species": sp})
    return {
        "today": client.today().isoformat(),
        "scoring_version": results[0]["scoring_version"] if results else None,
        "cells": out,
    }
