---
name: open-meteo
description: Comment Champis consomme Open-Meteo (variables, deux API, correction d'altitude, cache, quotas) et calcule l'indice météo M. À lire avant tout code qui appelle Open-Meteo ou touche api/champis_api/weather*.
---

# Open-Meteo dans Champis

Un seul module client : `api/champis_api/weather_client.py`. Personne d'autre n'appelle Open-Meteo. Licence CC-BY 4.0, usage non commercial sans clé ; ~10 000 appels/jour. Mention « Weather data by Open-Meteo.com » dans l'« à propos » des clients.

## Deux API, deux rôles

| API | URL | Sert à | Pourquoi |
| --- | --- | --- | --- |
| Prévision | `https://api.open-meteo.com/v1/forecast` avec `past_days=60&forecast_days=8` | J−60 → J+7 : temp, rain, trigger, humidité du sol, frost, water_balance, heat, persistance | Même modèle avant et après J : pas de discontinuité le jour J. Le modèle ne remonte que ~60 j (au-delà `null`, constaté le 17 oct. 2026) |
| Archive (ERA5-Land) | `https://archive-api.open-meteo.com/v1/archive`, **journalier uniquement** (`daily=…,soil_moisture_0_to_7cm_mean`) | Toutes les variables J−200 → J−1 (comble les `null` de la prévision : mémoire estivale, bout de fenêtre pluie des girolles) et climatologie de l'humidité du sol (10 ans, même mois) | Seule source profonde ; ~11 km, lissée |

Fusion par variable et par jour (`weather_service.build_series`) : **prévision si présente, sinon archive**. Les fenêtres courtes (≤ 47 j avant J−3) restent donc 100 % prévision ; seule la mémoire, et pour les girolles l'extrémité de la fenêtre pluie, mélangent les deux modèles — décision du 17 oct. 2026, assumée dans la spec.

## Variables (`daily=`)

`temperature_2m_mean,temperature_2m_min,temperature_2m_max,rain_sum,snowfall_sum,et0_fao_evapotranspiration`. Humidité du sol : en archive, `daily=soil_moisture_0_to_7cm_mean` (journalier, jamais horaire : trop lourd pour le quota) ; en prévision il n'y a que l'horaire par couche `soil_moisture_0_to_1cm` / `1_to_3cm` / `3_to_9cm` → moyenne journalière pondérée 1/2/6 (≈ 0–9 cm). `timezone=Europe/Paris`. Toujours lire `elevation` de la réponse : c'est l'altitude de la cellule, nécessaire à la correction.

**`rain_sum`, jamais `precipitation_sum`.** Un jour avec `snowfall_sum > 0` n'est pas un jour de pluie déclenchante.

## Grille et cache

- Les cellules sont les points de `data/weather_grid.json` (étape `weather-grid` du pipeline : carrés de 5 km alignés Lambert-93 où `T > 0` pour au moins une espèce ; `{version: 1, cell_m: 5000, cells: [{id, lat, lon, alt_classes, elevation_m}]}`, `id` = coin SO en km, `alt_classes` = centres des classes de 300 m sous la forêt). ~25 000 cellules France. Lu par `champis_api.grid`.
- Cache des réponses brutes Open-Meteo **6 h par cellule**, clé `cell_id:date_utc_bucket`, stockage SQLite (`weather_cache.db` sur le volume Railway). Le scoring se recalcule à partir du cache, jamais de nouvel appel pour changer d'espèce ou de jour.
- **Quotas** : Open-Meteo pondère chaque requête par le nombre de points **et** la longueur de la période (gratuit ≈ 600 appels pondérés/min, 5 000/h, 10 000/j). Règles : jamais d'horaire hors prévision ; lots de 100 (prévision) / 50 (archive) / 10 (climatologie) points ; 250 ms minimum entre deux requêtes ; `/weather/bbox` plafonné à 40 cellules (422 « zoomez ») ; un 429 est une indisponibilité (cache périmé, sinon 503 + `Retry-After`), jamais une boucle de réessais. Le passage France entière (25 000 cellules) ne tient pas dans le quota gratuit avec une tâche nocturne complète : point ouvert de la spec.
- Tâche nocturne (Railway cron, 03:00) : rafraîchit toutes les cellules et précalcule les indices par département. En journée, un appel `/weather` sur une cellule froide déclenche un fetch à la demande.
- Si Open-Meteo est injoignable : servir le cache périmé avec `"stale": true` dans la réponse, jamais une erreur 500 côté client.

## Correction d'altitude

Pour chaque classe d'altitude `a` de la cellule (centres 150, 450, 750… m) : `t_corr = t_cell − 0,006 × (a − elevation_cell)` appliqué à mean, min et max. L'API renvoie `M` **par classe d'altitude** ; le client choisit la classe du pixel. Sans cela, le gel n'est jamais détecté en montagne.

## Calcul de `M` (`api/champis_api/scoring.py`)

Règles dans `species/SCHEMA.md` et skill `champis-model`. Rappels d'implémentation :
- Fenêtres glissantes calculées pour chaque J de J−`persistence.days` à J+7 (la persistance a besoin des M passés).
- `trigger` : parcourir tous les événements (`≥ event_mm` sur `event_days` jours consécutifs, hors neige) des `lag_days.max` derniers jours ; facteur = max des trapèzes.
- `soil_moisture_pct` : percentile de la valeur du jour (prévision, 0–9 cm) dans la distribution ERA5-Land 0–7 cm de la cellule pour le même mois sur 10 ans : 11 quantiles par mois, calculés **à la demande par l'API** (une requête archive par cellule, groupée par 10) et cachés à vie dans SQLite (`soil_clim`), interpolation linéaire. Deux modèles différents : seul le percentile est utilisé, jamais la valeur absolue (décision du 17 oct. 2026).
- `water_balance` : `Σ(rain_sum − et0)` sur `window_days`.
- `memory` : cumul `rain_sum` sur `[J−118, J−28]` (archive).
- Réponse `/weather` : pour chaque jour, `M`, `Φ`, `M_eff` par classe d'altitude **et le détail des facteurs** (`temp`, `rain`, `trigger`, `soil_moisture`, `frost`, `water_balance`, `heat`, `memory`) : la fiche « pourquoi c'est vert » en dépend.

## Tests

- Fixtures JSON de réponses Open-Meteo enregistrées (`tests/fixtures/open_meteo/*.json`), jamais d'appel réseau dans `pytest`.
- Scénarios obligatoires : grosse pluie puis beau temps (trigger optimal, water_balance neutre), petite pluie récente après grosse pluie ancienne (le max gagne), épisode neigeux (pas de trigger), gel en altitude seulement (correction), Open-Meteo en panne (stale).
- Vecteurs de parité : skill `scoring-parity`.
