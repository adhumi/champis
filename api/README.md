# champis-api

Service FastAPI sans état : scoring météo `M × Φ` par cellule, fichiers espèces, palette. Aucun calcul géographique (tout est dans les tuiles). Spec › « Backend sur Railway ».

```bash
uv run champis-pipeline weather-grid --depts 25        # produit data/weather_grid.json
uv run uvicorn champis_api.app:app --reload            # http://127.0.0.1:8000/docs
```

| Variable | Défaut | Rôle |
| --- | --- | --- |
| `CHAMPIS_WEATHER_GRID` | `data/weather_grid.json` | Cellules météo (pipeline, étape `weather-grid`) |
| `CHAMPIS_CACHE_DB` | `data/weather_cache.db` | Cache SQLite des réponses Open-Meteo |
| `CHAMPIS_CORS_ORIGINS` | `*` | Origines autorisées, séparées par des virgules |

## Endpoints

- `GET /health` — `{"status": "ok", "cells": n}`.
- `GET /species` — `scoring_version`, `species_hash`, `palette` (`shared/palette.json`) et chaque `species/<id>.json` tel quel : les clients n'embarquent aucune valeur.
- `GET /weather?cell=<id>` ou `?lat=&lon=` (cellule la plus proche), `&species=<id>` répétable (défaut : toutes). Pour chaque jour de **J−3 à J+7** et chaque **classe d'altitude** de la cellule (centres 150, 450, 750… m) : `M`, `M_eff`, `phi` et `factors` (`temp`, `rain`, `trigger`, `soil_moisture`, `frost`, `water_balance`, `heat`, `memory`). Plus `stale` (cache périmé servi faute d'Open-Meteo), `cell_elevation_m`, `scoring_version`, `species_hash`.
- `GET /weather/bbox?min_lon&min_lat&max_lon&max_lat[&species][&day]` — même chose pour toutes les cellules de l'emprise (chaque `cell` avec `id`, `lat`, `lon`, `alt_classes`, `elevation_m`), sans `factors`, pour peindre la carte d'un coup.

Le client choisit la classe d'altitude de son pixel ; le score affiché est `T × M_eff × phi`.

## Open-Meteo (skill `open-meteo`)

`weather_client.py` est le seul module qui appelle Open-Meteo. Par cellule, trois jeux de données normalisés et mis en cache dans SQLite :

| Jeu | API | Fenêtre | Cache |
| --- | --- | --- | --- |
| `forecast` | prévision, `past_days=92&forecast_days=8` | J−92 → J+7 : températures, `rain_sum`, neige, ET0, humidité du sol 0–9 cm (moyenne journalière pondérée 1/2/6 des couches 0–1, 1–3, 3–9 cm). **Le modèle ne remonte que ~60 j : avant, l'API renvoie `null`** | 6 h |
| `archive` | archive ERA5-Land | J−200 → J−1, toutes les variables (humidité 0–7 cm horaire moyennée par jour) | 1 jour |
| `soil_clim` | archive ERA5-Land | 10 ans d'humidité 0–7 cm horaire → 11 quantiles par mois | permanent |

**Fusion** (`weather_service.build_series`, décision du 17 oct. 2026) : par variable et par jour, la prévision si elle a la valeur, sinon l'archive. De J−60 à J+7 tout vient donc du modèle de prévision (pas de discontinuité au jour J) ; avant J−60 — mémoire estivale, bout de fenêtre pluie des girolles — c'est ERA5-Land. Une valeur absente des deux → 502 qui nomme la variable et les dates.

L'humidité du jour est exprimée en percentile de la climatologie du mois (interpolation linéaire entre quantiles). Appels groupés jusqu'à 100 points (10 pour la climatologie). Open-Meteo injoignable → dernière réponse connue avec `"stale": true` ; aucune réponse connue → 503. Valeur absente des deux sources → 502, jamais une approximation silencieuse.

## Tests

`uv run pytest api/tests` — sans réseau : `tests/fixtures/open_meteo.py` fabrique des réponses Open-Meteo dans la forme exacte de l'API à partir d'un `Scenario` (pluie, neige, gel, panne…). Scénarios couverts : grosse pluie puis beau temps, petite pluie récente après grosse pluie ancienne, épisode neigeux, gel en altitude seulement, panne (cache périmé puis 503), cache par seau de 6 h, trou de série.
