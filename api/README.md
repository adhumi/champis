# champis-api

Service FastAPI : scoring météo `M × Φ` par cellule, indice par département pour la vue France, fichiers espèces, palette ; observations terrain et « mes coins » de l'app dans Postgres, avec la notification récapitulative du matin. Aucun calcul géographique (tout est dans les tuiles). Spec › « Backend sur Railway ».

```bash
uv run champis-pipeline weather-grid --depts 25        # produit data/weather_grid.json
uv run uvicorn champis_api.app:app --reload            # http://127.0.0.1:8000/docs
```

Les commandes `champis-api` partagent l'affichage du pipeline (étapes, statut, journal dans `data/logs/`, `-v`/`-q`) ; `make warm`, `make seed`, `make publish-seed`, `make notify` les lancent.

**Pré-chauffe** (pas de temps réel : décision du 17 oct. 2026) — `uv run champis-api warm` parcourt toute la grille à une requête toutes les 2 s, remplit le cache, puis calcule l'indice par département et la météo précalculée de chaque cellule (`cell_weather`, ce que sert `/weather/bbox`) ; sort en code 1 si des cellules restent indisponibles. Une fois par seau de 12 h. Sur Railway, c'est un **service cron séparé** (ci-dessous) ; en local, `make warm`. Sur un serveur à soi :

```
0 3,15 * * *  cd /chemin/champis && uv run champis-api warm >> data/warm.log 2>&1
```

## Déploiement Railway

Trois services construits par le même `Dockerfile` (décision du 4 nov. 2026, spec › Points ouverts › Tuiles hors du processus Python : la pré-chauffe bloquait la boucle d'événements du seul processus uvicorn ≈ 36 min deux fois par jour ; site, relais de tuiles et `/weather/bbox` ne répondaient plus). Les trois, avec le volume, le bucket et la base Postgres, sont définis dans **`.railway/railway.ts`** (Railway « Infrastructure as Code », TypeScript, un seul fichier pour tout le projet). L'ancien « Config as Code » (`railway.toml` par service) est déprécié : les services nouveaux ne peuvent plus s'y abonner et les fichiers existants ne sont plus lus après le **1er décembre 2026**.

**Comment Railway applique le fichier.** Railway ne le lit pas au déploiement : c'est le CLI (`railway` ≥ 5.42, `brew install railway` ou `npm i -g @railway/cli`) qui compare le fichier à l'environnement lié et applique la différence, après relecture. Le SDK `railway` (npm, `package.json` à la racine) sert seulement à évaluer le fichier : `npm install` une fois.

```bash
npm install                      # SDK railway/iac
railway login && railway link    # projet et environnement (production)
make railway-plan                # = railway config plan : les changements, sans rien écrire
make railway-apply               # = railway config apply : les applique après confirmation
```

Le fichier décrit **tout** l'environnement : une ressource ou une variable qui en est absente est supprimée par `apply` (ligne marquée destructive, à confirmer). Les noms en tête du fichier (projet, bucket, volume, service Postgres, domaines) doivent donc être ceux affichés dans Railway : au premier `plan`, si une ligne propose de créer un bucket ou un volume et d'en détruire un autre, c'est un nom à corriger, pas un changement à appliquer. `railway config pull --force` sur une branche de travail importe l'existant pour comparer (les valeurs des variables restent dans Railway, rendues `preserve()`). `railway config plan --detailed-exit-code` sort en `2` s'il reste une dérive : à mettre en CI le jour où un jeton de projet Railway y est posé (`railwayapp/config`, un commentaire de plan par PR touchant `.railway/`, application à la fusion ; non installé ici, le plan et l'application restent manuels).

**Ce que le fichier déclare**, service par service (horaires cron **en UTC**) :

| Service | Source et build | Déploiement | Variables (références, jamais de valeur) |
| --- | --- | --- | --- |
| `champis-api` | `adhumi/champis` @ `main`, builder `DOCKERFILE` | `CMD` du Dockerfile ; health check `/health`, 120 s ; redémarrage `ON_FAILURE`, 5 essais ; volume `/data` ; domaine `champis.adhumi.fr` (port 8000) | `AWS_*` du bucket, `CHAMPIS_OPEN_METEO_API_KEY` (partagée), `DATABASE_URL` du Postgres, `CHAMPIS_WORKERS=2` |
| `champis-warm` | idem | `uv run champis-api -q warm --pull --publish`, cron `0 2,14 * * *`, redémarrage `NEVER`, pas de volume ni de health check | `AWS_*` du bucket, `CHAMPIS_OPEN_METEO_API_KEY` |
| `champis-notify` | idem | `uv run champis-api -q notify --pull`, cron `0 6 * * *`, redémarrage `NEVER` | `AWS_*`, `CHAMPIS_OPEN_METEO_API_KEY`, `DATABASE_URL`, `CHAMPIS_APNS_KEY`, `_KEY_ID`, `_TEAM_ID` (partagées), `CHAMPIS_APNS_TOPIC=fr.adhumi.champis` |

`CHAMPIS_WARM_HOURS` et `CHAMPIS_NOTIFY_HOURS` restent vides sur l'API (`ENV` du Dockerfile : aucune tâche de fond, les crons s'en chargent) et ne sont pas déclarées dans le fichier : une valeur posée à la main serait retirée par `apply`, ce qui est voulu.

**Mise en place, pas à pas** :

1. Versionner la grille météo : `uv run champis-pipeline weather-grid --depts all`, puis `git add data/weather_grid.json` (exception à `data/` ignoré). L'amorçage, lui, va dans le bucket : `uv run champis-api seed` (base SQLite `data/weather_seed.db`, reprise possible) puis `uv run champis-api publish-seed` ; l'API et le cron le téléchargent et l'importent quand sa date change. L'ancien `data/weather_seed.json` du Doubs reste un repli local tant qu'aucun amorçage n'est publié.
2. Dans Railway, le projet existe avec son bucket et son service Postgres (sinon : New Project, + New › Bucket, + New › Database › Postgres). Les **secrets** se posent une fois, dans Settings › Shared Variables du projet, jamais dans le dépôt : `CHAMPIS_OPEN_METEO_API_KEY` (plan payant Open-Meteo : l'IP de sortie Railway est partagée et bridée sur l'API gratuite), `CHAMPIS_APNS_KEY` (contenu PEM de la clé `.p8`), `CHAMPIS_APNS_KEY_ID`, `CHAMPIS_APNS_TEAM_ID`. Le fichier les désigne par `${{shared.NOM}}`, les identifiants du bucket par `${{<bucket>.ACCESS_KEY_ID}}` etc. (ce que fait « Connect Service to Bucket », préréglage AWS SDK (Generic)), l'URL Postgres par `${{Postgres.DATABASE_URL}}`.
3. `make railway-plan`, corriger les noms en tête de `.railway/railway.ts` jusqu'à ce que le plan ne montre que les changements voulus (création des deux crons, réglages de l'API), puis `make railway-apply`. Railway construit alors les deux services cron depuis `main` avec le `Dockerfile` et les planifie ; vérifier dans Settings › Deploy de chacun que le Cron Schedule et la Custom Start Command apparaissent, et dans Settings › Networking qu'aucun domaine public n'est généré (un cron n'écoute rien).
4. Vérifier : `make doctor` sur ton poste, avec les variables du bucket dans `.env`, affiche la ligne « pré-chauffe » avec la date du dernier cache publié ; `GET /health` de l'API renvoie la même date dans `cache_published` au plus tard `CHAMPIS_CACHE_POLL_MINUTES` après. `railway cron list` montre les exécutions, `railway cron run` en lance une hors horaire. La carte est servie par le même service sur `/web/` (l'URL de l'API y est pré-remplie avec l'origine de la page).

**Migration depuis les fichiers `railway*.toml`** (API déjà déployée avec `railway.toml`) : le CLI refuse de planifier un service encore géré par un fichier Config as Code. Dans l'ordre : (a) dans Settings › Deploy du service API, s'assurer que health check `/health` (120 s) et redémarrage on_failure (5 essais) sont posés dans le tableau de bord, pour que le déploiement qui suit la fusion ne les perde pas ; (b) fusionner la PR qui supprime les toml ; (c) dans Settings › Config as code du service API, vider le chemin du fichier s'il est renseigné ; (d) `make railway-plan` puis `make railway-apply`. Si des services `champis-warm` et `champis-notify` avaient déjà été créés à la main avec leurs variables, garder les mêmes noms : le plan ne montre alors que les différences. Si tu préfères que le CLI écrive le fichier lui-même, `railway config migrate` sait le faire depuis les toml d'un dépôt ; ici il est écrit à la main, les toml sont retirés.

**Sans le CLI** (repli, tableau de bord seulement) : les mêmes réglages se saisissent service par service, + New › GitHub Repo `adhumi/champis` deux fois ; Settings › Deploy : Cron Schedule `0 2,14 * * *` (resp. `0 6 * * *`), Custom Start Command `uv run champis-api -q warm --pull --publish` (resp. `… notify --pull`), Restart Policy Never ; aucun domaine public, aucun health check, aucun volume ; Variables : « Connect Service to Bucket » (AWS SDK (Generic)), `CHAMPIS_OPEN_METEO_API_KEY=${{shared.CHAMPIS_OPEN_METEO_API_KEY}}` ; pour `champis-notify` en plus « Connect » le Postgres et les quatre `CHAMPIS_APNS_*`. Sur l'API : health check `/health`, redémarrage on_failure (5), volume `/data`.

Comment ça circule, et pourquoi par le bucket : la référence Infrastructure as Code de Railway le confirme (novembre 2026, « A volume can be attached to one service »), **un volume ne se monte que sur un seul service** ; le cron ne peut donc pas écrire dans le cache de l'API. Il travaille sur sa propre copie : `warm --pull` repart de l'instantané publié (cache, historique accumulé, climatologie, puis un amorçage plus récent s'il y en a un), pré-chauffe, calcule l'indice et la météo précalculée, et `--publish` dépose un instantané compact (`VACUUM INTO`, ≈ 1 Go pour la France) dans le bucket : `weather/weather_cache.db` et sa fiche `weather/weather_cache.json` (`published`, `today`, `dept_index_at`, `cells`, `cell_weather`, `bytes`). Côté API, le **worker meneur** compare la fiche à sa clé `meta` `cache_published` au démarrage puis toutes les `CHAMPIS_CACHE_POLL_MINUTES`, télécharge l'instantané et le réimporte **en une transaction** (remplacement table par table ; en WAL, les autres workers lisent l'ancien état puis le nouveau, jamais un mélange), dans un fil, sans bloquer les requêtes. Le cron n'a donc besoin d'aucun volume : un conteneur neuf à chaque exécution reprend tout du bucket (≈ 1 Go à télécharger, puis à téléverser ; sortie et entrée entre services d'un même projet Railway). Si Railway permettait un jour de monter un volume sur deux services, le cron pourrait simplement écrire dans `/data/weather_cache.db` (SQLite en WAL, `champis-api warm` sans `--pull` ni `--publish`) et `CHAMPIS_CACHE_POLL_MINUTES=0` ; l'instantané par le bucket reste la voie documentée parce qu'elle marche dans les deux cas. `champis-api notify --pull` reprend de la même façon le cache publié à 2 h UTC avant d'annoncer les coins.

Migration d'une API qui pré-chauffait elle-même (avant PR #71) : avant la première exécution du cron, publier le cache courant de l'API pour que le cron reparte de l'historique accumulé plutôt que de l'amorçage seul (`champis-api publish-cache` depuis un shell dans le conteneur de l'API, par exemple `railway ssh` si ta version du CLI l'offre). Sans cela, le cron repart de l'amorçage publié et redemande à Open-Meteo jusqu'à 92 jours de passé par cellule : complet si l'amorçage a moins de 92 jours, sinon re-amorcer (`make seed`, `make publish-seed`). Puis redéployer l'API avec `CHAMPIS_WARM_HOURS` vide.

**Repli sans cron** : `CHAMPIS_WARM_HOURS=3,15` (et `CHAMPIS_NOTIFY_HOURS=7`) sur le service API remettent les tâches de fond dans l'API ; elles tournent dans le seul worker meneur, qui ne répond plus pendant la passe (les autres workers continuent). `make doctor` dit lequel des deux modes est actif.

**Plusieurs workers** (`CHAMPIS_WORKERS`, 2 par défaut ; `uvicorn --workers`) : chaque processus a son propre état en mémoire, à savoir le **limiteur de débit** (seau par IP et par processus : un client peut obtenir jusqu'à N fois la limite affichée, acceptable, le limiteur protège le CPU et Open-Meteo, pas l'équité), le **cache du manifeste** `/tiles` (une lecture S3 par worker toutes les 10 min) et le moteur SQLAlchemy de Postgres. Le cache météo SQLite est partagé sur le volume : journal **WAL** et `timeout` de 30 s sur chaque connexion. Au démarrage, l'import de l'amorçage passe sous un verrou de fichier (`/data/.champis-seed.lock`) : un worker importe, les autres attendent puis constatent qu'il n'y a rien à faire. Un second verrou (`/data/.champis-leader.lock`, `flock`, rendu à la mort du processus) élit le **meneur** qui seul importe le cache publié et, en repli, pré-chauffe et notifie ; les autres workers réessaient toutes les `CHAMPIS_LEADER_RETRY_S` (60 s) et prennent le relais si le meneur disparaît.

Les PMTiles ne sont pas encore servis par le service (`/tiles` et le bucket viennent plus tard) : sur la carte déployée, on les glisse depuis son disque comme en local.

| Variable | Défaut | Rôle |
| --- | --- | --- |
| `CHAMPIS_WEATHER_GRID` | `data/weather_grid.json` | Cellules météo (pipeline, étape `weather-grid`) |
| `CHAMPIS_WEATHER_SEED` | `data/weather_seed.json` | Amorçage local de repli (`.db` ou ancien `.json`), importé une fois si le bucket n'en publie pas |
| `CHAMPIS_WEATHER_SEED_DB` | `data/weather_seed.db` | Sortie de `champis-api seed`, source de `publish-seed` |
| `CHAMPIS_CACHE_DB` | `data/weather_cache.db` | Cache SQLite des réponses Open-Meteo |
| `CHAMPIS_OPEN_METEO_API_KEY` | *(vide)* | Clé du plan payant Open-Meteo (Standard) : prévision sur `customer-api` avec quota dédié ; vide = API gratuite |
| `AWS_ENDPOINT_URL`, `AWS_S3_BUCKET_NAME`, `AWS_DEFAULT_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | *(vides)* | Bucket Railway des PMTiles, tels que les injecte « Connect Service to Bucket » avec le préréglage **AWS SDK (Generic)** ; vides = `/tiles` répond `configured: false`. `CHAMPIS_S3_ENDPOINT` / `CHAMPIS_S3_BUCKET` / `CHAMPIS_S3_REGION` priment s'ils sont posés |
| `CHAMPIS_TILES_MODE` | `presign` | `presign` : URL présignées lues par le navigateur ; `proxy` : relais `/tiles/{name}` (si le bucket n'envoie pas les en-têtes CORS) |
| `CHAMPIS_TILES_URL_HOURS` | `24` | Durée des URL présignées |
| `CHAMPIS_TILE_CACHE_DIR` | `<dossier de CHAMPIS_CACHE_DB>/tiles` (`/data/tiles` sur Railway) | Cache disque du relais (mode `proxy`) : une entrée par plage `Range` exacte relayée, servie ensuite sans repasser par le bucket |
| `CHAMPIS_TILE_CACHE_MB` | `2048` | Taille totale du cache disque en Mo, éviction des plages les moins lues au-delà ; `0` = désactivé |
| `CHAMPIS_CORS_ORIGINS` | `*` | Origines autorisées, séparées par des virgules |
| `CHAMPIS_WARM_HOURS` | *(vide)* | Heures Paris de la pré-chauffe intégrée (repli), ex. `3,15` ; vide = service cron `champis-warm` |
| `CHAMPIS_WARM_ON_START` | `0` | `1` : pré-chauffe au démarrage (repli ; chaque redéploiement relancerait une passe) |
| `CHAMPIS_CACHE_POLL_MINUTES` | `10` | Minutes entre deux lectures de la fiche du cache publié par le cron ; `0` = import au démarrage seulement |
| `CHAMPIS_WORKERS` | `2` | Workers uvicorn (Dockerfile seulement) |
| `CHAMPIS_LEADER_RETRY_S` | `60` | Secondes entre deux tentatives d'un worker pour devenir meneur |
| `CHAMPIS_SERVE_WEB` | `1` | Servir `web/`, `shared/`, `species/` en statique |
| `DATABASE_URL` (ou `CHAMPIS_DATABASE_URL`) | `sqlite:///data/champis.db` | Observations et coins : Postgres Railway (variable injectée par le service Postgres, « Connect ») ; en local sans Postgres, SQLite. Vide = `/observations` et `/coins` en 503 |
| `CHAMPIS_APNS_KEY`, `CHAMPIS_APNS_KEY_ID`, `CHAMPIS_APNS_TEAM_ID` | *(vides)* | Clé APNs `.p8` (contenu PEM en variable secrète, ou chemin), son identifiant, l'identifiant d'équipe Apple. Sans eux, aucune notification n'est envoyée |
| `CHAMPIS_APNS_TOPIC` | `fr.adhumi.champis` | Sujet APNs = identifiant de bundle de l'app |
| `CHAMPIS_NOTIFY_HOURS` | `7` (vide dans l'image) | Heure(s) Paris de la notification « mes coins » envoyée par l'API (repli) ; vide = service cron `champis-notify` |
| `CHAMPIS_RATE_READ`, `CHAMPIS_RATE_WRITE` | `120`, `20` | Requêtes par minute et par IP, lectures et écritures (`POST`/`PUT`/`DELETE`) ; au-delà 429 + `Retry-After` |
| `CHAMPIS_MAX_BODY` | `262144` | Taille maximale d'un corps d'écriture (octets) ; au-delà 413 |

## PMTiles : bucket et `/tiles`

Les tuiles ne tiennent ni dans l'image ni dans le dépôt (France ≈ 2–4 Go par espèce) : elles vont dans un **Railway Storage Bucket** (S3-compatible, privé, sortie gratuite par URL présignées). Procédure :

1. Créer le bucket dans le projet Railway, « Connect Service to Bucket » → service API, préréglage **AWS SDK (Generic)** ; sur ton poste, les cinq mêmes variables dans `.env` à la racine (`cp .env.example .env`).
2. Après `champis-pipeline tiles --depts …` : `uv run champis-pipeline publish --depts … [--species …]` téléverse les PMTiles manquants et réécrit `tiles/manifest.json` ; `--prune` supprime du bucket les PMTiles des autres jeux de départements (la carte n'affiche qu'un jeu, le plus couvrant) (`{version, generated, depts_by_hash, tiles:[{kind, species, hash, scoring_version, depts_hash, name, key, bytes}]}`).
3. La carte appelle `GET /tiles` au chargement et ouvre chaque fichier par son URL ; le glisser-déposer reste disponible. Si le navigateur refuse les URL présignées (CORS absent sur le bucket : le statut de la carte affiche « Load failed » / « Failed to fetch » par fichier et `0/N chargés`), passer `CHAMPIS_TILES_MODE=proxy` : l'API relaie les requêtes `Range` via `/tiles/{name}` (sortie service facturée, à éviter si `presign` marche).
4. En mode `proxy`, le relais garde sur le volume chaque plage `Range: bytes=a-b` exacte et bornée (≤ 4 Mo) qu'il a relayée (`CHAMPIS_TILE_CACHE_DIR`, `CHAMPIS_TILE_CACHE_MB` ; spec › Points ouverts › Tuiles hors du processus Python, 4 nov. 2026) : en-tête, répertoires et tuiles chaudes ne sautent plus vers le bucket à chaque visiteur. La réponse est la même qu'en relais (206, `content-range`, `etag` mémorisé, `cache-control` immutable) avec `x-cache: hit` ou `miss` ; les PMTiles étant immuables, rien n'expire. Une requête sans `Range` (fichier entier), ouverte ou en suffixe reste un relais en streaming, jamais mise en cache. Écriture atomique (temporaire puis `rename`) et lecture sans verrou : plusieurs workers uvicorn partagent le même dossier. Au-delà de la borne, les plages dont le mtime est le plus ancien sont supprimées hors du chemin des requêtes (nettoyage après écriture, 5 s au plus) ; `champis-api doctor` affiche le nombre de plages et la taille.

## Endpoints

- `GET /health` — `{"status": "ok", "cells": n, "seeded": n, "dept_index_at": "…", "cache_published": "…"}` : `seeded` = cellules amorcées (climatologie du sol présente) ; doit valoir `cells` après l'import de l'amorçage ; `dept_index_at` = date du dernier calcul de l'indice par département (`null` avant la première pré-chauffe) ; `cache_published` = `published` du dernier instantané du cron importé (`null` si jamais : pré-chauffe intégrée ou cron pas encore passé).
- `GET /departements[?species=<id>…][&day=<date>]` — indice par département pour la vue France (spec › Scoring) : `I = Σ T × M_eff × Φ / Σ T` sur les pixels forestiers du département, par cellule météo et classe d'altitude, pour chaque espèce et chaque jour J−3 → J+7 (`day` pour un seul jour) ; `coverage` = part de Σ T dont la météo était disponible ; par groupe, le maximum des espèces et l'espèce `leading` (règle 9). Calculé à la fin de chaque pré-chauffe sur le cache (aucun appel Open-Meteo), 503 tant qu'il ne l'a jamais été. Les poids Σ T viennent de `weather_grid.json` version 2 (`champis-pipeline weather-grid`) ; avec une grille version 1 l'indice n'est pas calculé.
- `GET /tiles` — `{configured, mode, generated, depts_by_hash, tiles:[{…, url}]}` ; `GET /tiles/{name}` — relais Range (mode `proxy` seulement).
- `GET /species` — `scoring_version`, `species_hash`, `palette` (`shared/palette.json`) et chaque `species/<id>.json` tel quel : les clients n'embarquent aucune valeur.
- `/web/` (statique, avec `SERVE_WEB`) — le site : `index.html` (Aujourd'hui), `carte.html`, `comprendre.html`, `soutenir.html` ; `/` redirige vers `/web/`.
- `/shared/texts/` (statique, avec `SERVE_WEB`) — les articles de Comprendre (`index.json` + Markdown), les mêmes mots pour l'app (copiés à la compilation) et le site ; les fiches d'espèces sont le bloc `about` de `GET /species`.
- `GET /weather?cell=<id>` ou `?lat=&lon=` (cellule la plus proche), `&species=<id>` répétable (défaut : toutes). Pour chaque jour de **J−3 à J+7** et chaque **classe d'altitude** de la cellule (centres 150, 450, 750… m) : `M`, `M_eff`, `phi` et `factors` (`temp`, `rain`, `trigger`, `soil_moisture`, `frost`, `water_balance`, `heat`, `memory`). Lot 2 de la refonte UX (1er nov. 2026) : chaque ligne porte aussi `trigger_days` (âge en jours de la pluie déclenchante retenue, `null` sans événement) et `summary`, deux à huit phrases courtes en français déduites des facteurs avec des seuils génériques (`champis_api/explain.py`) ; les clients les affichent telles quelles et ajoutent seuls la phrase de terrain depuis le libellé de palette de T. Plus `stale` (cache périmé servi faute d'Open-Meteo), `cell_elevation_m`, `scoring_version`, `species_hash`.
- `GET /weather/bbox?min_lon&min_lat&max_lon&max_lat[&species][&day]` — même chose pour toutes les cellules de l'emprise (chaque `cell` avec `id`, `lat`, `lon`, `alt_classes`, `elevation_m`), sans `factors`, pour peindre la carte d'un coup. Servi depuis la **météo précalculée** à la dernière pré-chauffe (table `cell_weather`, remplie par la même passe que l'indice par département ; `computed_at` l'horodate) : aucun recalcul ni appel Open-Meteo, une emprise d'écran entière tient dans une réponse, jusqu'à 5 000 cellules (au-delà, 422 « zoomez » : ce n'est plus un écran). Une cellule que la pré-chauffe n'a pas est calculée à la demande, 40 par requête au plus, et rangée pour la suivante ; les autres sont listées dans `unavailable`, comme les cellules sans météo (Open-Meteo injoignable, rien en cache), avec `retry_after` quand Open-Meteo l'a indiqué, au lieu de faire échouer la réponse. Entre minuit et la pré-chauffe de 3 h, les lignes de la veille couvrent J−4 → J+6 : J+7 manque. Réponses JSON compressées (gzip) au-delà de 1 Kio.

Le client choisit la classe d'altitude de son pixel ; le score affiché est `T × M_eff × phi`.

### Retour terrain et mes coins (app seulement)

Identité : en-tête `X-Champis-User`, un UUID généré par l'app au premier lancement et gardé dans le trousseau iCloud. Pas de compte. Tout ce qui suit est privé à cet identifiant ; `DELETE /observations` efface tout (observations, coins, jeton) : droit RGPD.

- `POST /observations` — `{"observations": [{id, species, lat, lon, accuracy_m?, date, found, quantity?}]}` (≤ 200), 201 → `{"inserted", "duplicates"}`. Idempotent par `id` : renvoyer un lot après une coupure réseau ne crée rien. `quantity` 1–3 obligatoire si `found`, interdite sinon ; pas de photo, pas de texte libre.
- `GET /observations` — les miennes, les plus récentes d'abord.
- `DELETE /observations` — `{"deleted": n}`.
- `PUT /coins` — `{"apns_token"?, "sandbox"?, "coins": [{id, name, lat, lon, target, alt_class, t}]}` (≤ 50) : remplace la liste complète (le serveur ne fusionne pas) et le jeton de notification. `target` = espèce ou groupe affiché ; `alt_class` = centre de la classe d'altitude du pixel (couche A) ; `t` = `{espèce: T}` lu par l'app dans les tuiles au moment où le coin est créé — le backend n'a pas les tuiles.
- `GET /coins` — mes coins avec `score` du jour (max sur les espèces de `T_e × M_eff_e × Φ_e`, cellule la plus proche, classe d'altitude du coin), `leading`, et `best_day`/`best` si un jour de J+1 à J+7 fait mieux.

**Notification** (`champis_api.coins.notify_all` ; service cron `champis-api notify --pull`, ou tâche intégrée à `CHAMPIS_NOTIFY_HOURS` en repli, ou `champis-api notify` à la main) : après la pré-chauffe du matin, une seule notification par appareil, récapitulative, envoyée seulement si au moins un coin est « bon » ou « excellent » (seuil lu dans `shared/palette.json`). Un jeton refusé par APNs (`Unregistered`, `BadDeviceToken`) est retiré, on n'insiste pas. L'app ne fait aucun rafraîchissement en arrière-plan.

**Protection** (service public) : seau à jetons par IP et par worker (`X-Forwarded-For` derrière Railway), 120 lectures et 20 écritures par minute par défaut, corps d'écriture ≤ 256 Ko, lots bornés, validation stricte des champs (espèces connues, France métropolitaine, dates non futures).

## Open-Meteo (skill `open-meteo`)

`weather_client.py` est le seul module qui appelle Open-Meteo. Décision du 17 oct. 2026, **« amorcer, puis accumuler »** :

| Donnée | Source | Quand |
| --- | --- | --- |
| Prévision J−n → J+7 (températures, `rain_sum`, neige, ET0, humidité du sol 0–9 cm), n = jours manquants dans l'historique, 1 à 92 | API prévision, **plan payant** (`customer-api`, clé `CHAMPIS_OPEN_METEO_API_KEY`) | En service, un appel par cellule et par seau de 12 h |
| Historique J−200 → J−n | Les jours passés de chaque prévision, **accumulés** dans SQLite (`history`) | Automatique, à chaque prévision fraîche |
| Climatologie du sol (10 ans → 11 quantiles/mois) | **Pipeline** `champis-pipeline soil-clim` : ERA5-Land 0–7 cm via le Climate Data Store (gratuit, compte CDS), quantiles par pixel 0,1° | Une fois → `data/weather_seed.db` (`soil_clim`), publié dans le bucket (`publish-seed`), importé au démarrage |
| Historique initial J−200 → J−1 | **Amorçage** `champis-api seed` sur l'archive ERA5-Land gratuite, hors Railway, 10 appels pondérés par cellule (200 jours × 7 variables) : France ≈ 227 000 appels, soit ≈ 23 jours sur l'archive gratuite (10 000 par jour) ou quelques heures avec une clé Professional ; en attendant, `past_days=92` puis accumulation (cellule `unavailable` avec sa date de complétude tant que la fenêtre mémoire n'est pas couverte, ≈ 41 j) | Une fois par grille → même base, mêmes publication et import |

L'API historique n'est pas dans le plan Standard (Professional seulement, pris le temps de l'amorçage France) et l'IP de sortie Railway est bridée sur l'API gratuite : en service, Railway ne parle donc **qu'à la prévision**, en ne demandant que les jours de passé absents de l'historique (`past_days` 1 à 92 ; poids Open-Meteo = points × jours/14 × variables/10, journalisé à chaque pré-chauffe). Les dates d'amorçage sont remplacées par la prévision dès qu'elle les couvre (même modèle avant et après J). Une valeur absente de la prévision et de l'historique → 502 nommant la variable et les dates, jamais une approximation.

```bash
uv run champis-pipeline soil-clim           # climatologie ERA5-Land (CDS) → data/weather_seed.db, une fois
uv run champis-api publish-seed             # → bucket weather/weather_seed.db + weather/weather_seed.json ; l'API l'importe au prochain démarrage
uv run champis-api seed                     # historique J−200 depuis l'archive gratuite, lots de 50, 1 s d'intervalle ; France ≈ 23 jours sur l'archive gratuite (quota 10 000/j), quelques heures en Professional
uv run champis-api publish-seed             # republier : l'API réimporte (ATTACH, sans rien charger en mémoire ; l'historique amorcé ne remplace jamais la prévision)
```

`seed --climatology` demande aussi la climatologie à Open-Meteo pour les cellules qui n'en ont pas (26 appels pondérés par cellule : un petit secteur, ou avec la clé sur `customer-archive-api`, plan Professional). Un 429 (quota) ne fait pas échouer la commande : elle attend (`Retry-After`, sinon 1 → 15 min) et reprend le même lot ; laisse-la tourner. Reprise possible (les cellules déjà dans la base ne sont pas refaites). Après un `weather-grid` qui ajoute des cellules, relancer `soil-clim`, `seed` puis `publish-seed` : seules les nouvelles sont faites.

**Quotas** : lissage 250 ms entre requêtes (2 s en pré-chauffe, 1 s en amorçage), lots de 100 points, `/weather/bbox` servi depuis le précalcul et limité à 40 cellules calculées à la demande par requête (5 000 cellules par emprise, sinon 422 « zoomez »), 429 court réessayé une fois sinon indisponibilité (cache périmé, cellule `unavailable`, 503 + `Retry-After`). Une cellule sans climatologie amorcée est `unavailable` avec la raison « amorçage requis ».

## Tests

`uv run pytest api/tests` — sans réseau : `tests/fixtures/open_meteo.py` fabrique des réponses Open-Meteo dans la forme exacte de l'API à partir d'un `Scenario` (pluie, neige, gel, panne…). Scénarios couverts : grosse pluie puis beau temps, petite pluie récente après grosse pluie ancienne, épisode neigeux, gel en altitude seulement, panne (cache périmé puis 503), cache par seau de 12 h, trou de série, pré-chauffe.
