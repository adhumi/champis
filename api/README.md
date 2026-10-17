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

1. Versionner la grille météo : `uv run champis-pipeline weather-grid --depts 25` puis `git add data/weather_grid.json` (seule exception à `data/` ignoré ; quelques dizaines de ko).
2. Railway → New Project → Deploy from GitHub repo `adhumi/champis`, branche `main`. Le build utilise le `Dockerfile`.
3. Ajouter un **volume** monté sur `/data` (le cache SQLite `weather_cache.db` y vit ; sans volume, chaque déploiement repart à froid).
4. Variables déjà fixées dans l'image : `CHAMPIS_WEATHER_GRID`, `CHAMPIS_CACHE_DB=/data/weather_cache.db`, `CHAMPIS_WARM_HOURS=3,15` (pré-chauffe intégrée à 3 h et 15 h Paris, pas de second service). **À ajouter : `CHAMPIS_OPEN_METEO_API_KEY`** (plan payant Open-Meteo, en variable secrète Railway : l'IP de sortie Railway est partagée et bridée sur l'API gratuite). Optionnel : `CHAMPIS_WARM_ON_START=1` pour chauffer au premier déploiement (puis à retirer : chaque redéploiement relancerait un passage complet), `CHAMPIS_CORS_ORIGINS` pour restreindre.
5. Health check : `/health`. La carte est servie par le même service sur `/web/` (l'URL de l'API y est pré-remplie avec l'origine de la page).

Les PMTiles ne sont pas encore servis par le service (`/tiles` et le bucket viennent plus tard) : sur la carte déployée, on les glisse depuis son disque comme en local.

| Variable | Défaut | Rôle |
| --- | --- | --- |
| `CHAMPIS_WEATHER_GRID` | `data/weather_grid.json` | Cellules météo (pipeline, étape `weather-grid`) |
| `CHAMPIS_CACHE_DB` | `data/weather_cache.db` | Cache SQLite des réponses Open-Meteo |
| `CHAMPIS_OPEN_METEO_API_KEY` | *(vide)* | Clé du plan payant Open-Meteo : bascule sur `customer-api` / `customer-archive-api` avec quota dédié ; vide = API gratuite |
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

`weather_client.py` est le seul module qui appelle Open-Meteo. Par cellule, trois jeux de données normalisés et mis en cache dans SQLite :

| Jeu | API | Fenêtre | Cache |
| --- | --- | --- | --- |
| `forecast` | prévision, `past_days=60&forecast_days=8` | J−60 → J+7 : températures, `rain_sum`, neige, ET0, humidité du sol 0–9 cm (moyenne journalière pondérée 1/2/6 des couches horaires 0–1, 1–3, 3–9 cm). Le modèle ne remonte pas plus loin | 12 h |
| `archive` | archive ERA5-Land, journalier | J−200 → J−1, toutes les variables dont `soil_moisture_0_to_7cm_mean` | 1 jour |
| `soil_clim` | archive ERA5-Land, journalier | 10 ans de `soil_moisture_0_to_7cm_mean` → 11 quantiles par mois | permanent |

**Fusion** (`weather_service.build_series`, décision du 17 oct. 2026) : par variable et par jour, la prévision si elle a la valeur, sinon l'archive. De J−60 à J+7 tout vient donc du modèle de prévision (pas de discontinuité au jour J) ; avant J−60 — mémoire estivale, bout de fenêtre pluie des girolles — c'est ERA5-Land. Une valeur absente des deux → 502 qui nomme la variable et les dates.

L'humidité du jour est exprimée en percentile de la climatologie du mois (interpolation linéaire entre quantiles).

**Quotas.** Open-Meteo pondère chaque requête par le nombre de points et la longueur de la période (gratuit ≈ 600 appels pondérés/min, 5 000/h, 10 000/j) : une requête horaire sur 10 ans valait des milliers d'appels, d'où le 429 du premier test réel. Désormais : rien d'horaire hors prévision, lots de 100 / 50 / 10 points, 250 ms minimum entre deux requêtes, `/weather/bbox` plafonné à 40 cellules (422 « zoomez » au-delà ; les cellules en cache ne coûtent rien). Open-Meteo injoignable ou 429 → dernière réponse connue avec `"stale": true` ; aucune réponse connue → 503 (avec `Retry-After` sur un 429). Valeur absente des deux sources → 502, jamais une approximation silencieuse.

## Tests

`uv run pytest api/tests` — sans réseau : `tests/fixtures/open_meteo.py` fabrique des réponses Open-Meteo dans la forme exacte de l'API à partir d'un `Scenario` (pluie, neige, gel, panne…). Scénarios couverts : grosse pluie puis beau temps, petite pluie récente après grosse pluie ancienne, épisode neigeux, gel en altitude seulement, panne (cache périmé puis 503), cache par seau de 12 h, trou de série, pré-chauffe.
