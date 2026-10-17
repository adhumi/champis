from __future__ import annotations

from datetime import date, timedelta

import pytest
from champis_api.scoring import DailySeries


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
