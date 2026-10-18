# champis-api

Service FastAPI sans état : scoring météo `M × Φ` par cellule, fichiers espèces, palette. Aucun calcul géographique (tout est dans les tuiles). Spec › « Backend sur Railway ».

```bash
uv run champis-pipeline weather-grid --depts 25        # produit data/weather_grid.json
uv run uvicorn champis_api.app:app --reload            # http://127.0.0.1:8000/docs
```

**Pré-chauffe** (pas de temps réel : décision du 17 oct. 2026) — `uv run champis-api warm` parcourt toute la grille à une requête toutes les 2 s et remplit le cache ; sort en code 1 si des cellules restent indisponibles. À lancer par cron une fois par seau de 12 h, par exemple :

```
0 3,15 * * *  cd /chemin/champis && uv run champis-api warm >> data/warm.log 2>&1
```

## Déploiement Railway

Un seul service, `Dockerfile` et `railway.toml` à la racine du dépôt (spec › Backend sur Railway).

1. Versionner la grille météo et l'amorçage : `uv run champis-pipeline weather-grid --depts 25`, `uv run champis-api seed`, puis `git add data/weather_grid.json data/weather_seed.json` (seules exceptions à `data/` ignoré ; quelques Mo). Le Dockerfile copie les deux.
2. Railway → New Project → Deploy from GitHub repo `adhumi/champis`, branche `main`. Le build utilise le `Dockerfile`.
3. Ajouter un **volume** monté sur `/data` (le cache SQLite `weather_cache.db` y vit ; sans volume, chaque déploiement repart à froid).
4. Variables déjà fixées dans l'image : `CHAMPIS_WEATHER_GRID`, `CHAMPIS_CACHE_DB=/data/weather_cache.db`, `CHAMPIS_WARM_HOURS=3,15` (pré-chauffe intégrée à 3 h et 15 h Paris, pas de second service). **À ajouter : `CHAMPIS_OPEN_METEO_API_KEY`** (plan payant Open-Meteo, en variable secrète Railway : l'IP de sortie Railway est partagée et bridée sur l'API gratuite). Optionnel : `CHAMPIS_WARM_ON_START=1` pour chauffer au premier déploiement (puis à retirer : chaque redéploiement relancerait un passage complet), `CHAMPIS_CORS_ORIGINS` pour restreindre.
5. Health check : `/health`. La carte est servie par le même service sur `/web/` (l'URL de l'API y est pré-remplie avec l'origine de la page).

Les PMTiles ne sont pas encore servis par le service (`/tiles` et le bucket viennent plus tard) : sur la carte déployée, on les glisse depuis son disque comme en local.

| Variable | Défaut | Rôle |
| --- | --- | --- |
| `CHAMPIS_WEATHER_GRID` | `data/weather_grid.json` | Cellules météo (pipeline, étape `weather-grid`) |
| `CHAMPIS_WEATHER_SEED` | `data/weather_seed.json` | Amorçage (`champis-api seed`), importé au démarrage |
| `CHAMPIS_CACHE_DB` | `data/weather_cache.db` | Cache SQLite des réponses Open-Meteo |
| `CHAMPIS_OPEN_METEO_API_KEY` | *(vide)* | Clé du plan payant Open-Meteo (Standard) : prévision sur `customer-api` avec quota dédié ; vide = API gratuite |
| `CHAMPIS_CORS_ORIGINS` | `*` | Origines autorisées, séparées par des virgules |
| `CHAMPIS_WARM_HOURS` | *(vide)* | Heures Paris de la pré-chauffe intégrée, ex. `3,15` ; vide = cron externe (`champis-api warm`) |
| `CHAMPIS_WARM_ON_START` | `0` | `1` : pré-chauffe au démarrage |
| `CHAMPIS_SERVE_WEB` | `1` | Servir `web/`, `shared/`, `species/` en statique |

## Endpoints

- `GET /health` — `{"status": "ok", "cells": n}`.
- `GET /species` — `scoring_version`, `species_hash`, `palette` (`shared/palette.json`) et chaque `species/<id>.json` tel quel : les clients n'embarquent aucune valeur.
- `GET /weather?cell=<id>` ou `?lat=&lon=` (cellule la plus proche), `&species=<id>` répétable (défaut : toutes). Pour chaque jour de **J−3 à J+7** et chaque **classe d'altitude** de la cellule (centres 150, 450, 750… m) : `M`, `M_eff`, `phi` et `factors` (`temp`, `rain`, `trigger`, `soil_moisture`, `frost`, `water_balance`, `heat`, `memory`). Plus `stale` (cache périmé servi faute d'Open-Meteo), `cell_elevation_m`, `scoring_version`, `species_hash`.
- `GET /weather/bbox?min_lon&min_lat&max_lon&max_lat[&species][&day]` — même chose pour toutes les cellules de l'emprise (chaque `cell` avec `id`, `lat`, `lon`, `alt_classes`, `elevation_m`), sans `factors`, pour peindre la carte d'un coup. Les cellules sans météo (Open-Meteo injoignable, rien en cache) sont listées dans `unavailable` avec `retry_after` au lieu de faire échouer la réponse.

Le client choisit la classe d'altitude de son pixel ; le score affiché est `T × M_eff × phi`.

## Open-Meteo (skill `open-meteo`)

`weather_client.py` est le seul module qui appelle Open-Meteo. Décision du 17 oct. 2026, **« amorcer, puis accumuler »** :

| Donnée | Source | Quand |
| --- | --- | --- |
| Prévision J−60 → J+7 (températures, `rain_sum`, neige, ET0, humidité du sol 0–9 cm) | API prévision, **plan payant Standard** (`customer-api`, clé `CHAMPIS_OPEN_METEO_API_KEY`) | En service, un appel par cellule et par seau de 12 h |
| Historique J−200 → J−61 | Les ~60 jours passés de chaque prévision, **accumulés** dans SQLite (`history`) | Automatique, à chaque prévision fraîche |
| Historique initial + climatologie du sol (10 ans → 11 quantiles/mois) | **Amorçage** `champis-api seed` sur l'archive ERA5-Land **gratuite**, hors Railway | Une fois par grille → `data/weather_seed.json`, versionné, importé au démarrage |

L'API historique n'est pas dans le plan Standard et l'IP de sortie Railway est bridée sur l'API gratuite : en service, Railway ne parle donc **qu'à la prévision**. Les dates d'amorçage sont remplacées par la prévision dès qu'elle les couvre (même modèle avant et après J). Une valeur absente de la prévision et de l'historique → 502 nommant la variable et les dates, jamais une approximation.

```bash
uv run champis-api seed                     # depuis ton poste : ~265 cellules × 2 requêtes, 5 s d'intervalle ≈ 45 min
git add data/weather_seed.json && git commit -m "amorçage météo Doubs" && git push
```

Reprise possible (les cellules déjà dans le fichier ne sont pas refaites). Après un `weather-grid` qui ajoute des cellules, relancer `seed` : seules les nouvelles sont faites.

**Quotas** : lissage 250 ms entre requêtes (2 s en pré-chauffe, 5 s en amorçage), lots de 100 points, `/weather/bbox` plafonné à 40 cellules (422 « zoomez »), 429 court réessayé une fois sinon indisponibilité (cache périmé, cellule `unavailable`, 503 + `Retry-After`). Une cellule sans climatologie amorcée est `unavailable` avec la raison « amorçage requis ».

## Tests

`uv run pytest api/tests` — sans réseau : `tests/fixtures/open_meteo.py` fabrique des réponses Open-Meteo dans la forme exacte de l'API à partir d'un `Scenario` (pluie, neige, gel, panne…). Scénarios couverts : grosse pluie puis beau temps, petite pluie récente après grosse pluie ancienne, épisode neigeux, gel en altitude seulement, panne (cache périmé puis 503), cache par seau de 12 h, trou de série, pré-chauffe.
