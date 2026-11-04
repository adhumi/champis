// Railway, Infrastructure as Code : les trois services de Champis, le volume, le bucket et la base,
// en un seul fichier pour tout le projet (doc Railway « Infrastructure as Code », novembre 2026).
// Remplace railway.toml, railway.warm.toml et railway.notify.toml (« Config as Code », déprécié,
// plus lu après le 1er décembre 2026 ; les services nouveaux ne pouvaient déjà plus s'y abonner).
//
// Railway ne lit pas ce fichier au déploiement : c'est le CLI qui l'applique, après relecture.
//   npm install                  # le SDK `railway` (package.json à la racine), une fois
//   railway login && railway link
//   make railway-plan            # = railway config plan : montre les changements, n'écrit rien
//   make railway-apply           # = railway config apply : les applique après confirmation
// Un fichier unique décrit TOUT l'environnement : une ressource ou une variable absente d'ici est
// supprimée par `apply` (changement marqué destructif, à confirmer). Les noms ci-dessous doivent donc
// coïncider avec ceux affichés dans Railway ; au premier `plan`, corriger les constantes jusqu'à ce
// que le plan ne montre plus que les changements voulus (`railway config pull --force` sur une
// branche de travail importe l'existant pour comparer). Pas à pas : api/README.md › Déploiement Railway.
//
// Aucune valeur secrète ici : les secrets restent dans Railway et sont désignés par référence
// (`ctx.shared.X` → ${{shared.X}}, `ref(bucket, "ACCESS_KEY_ID")` → ${{bucket.ACCESS_KEY_ID}}).

import {
  bucket,
  defineRailway,
  github,
  postgres,
  project,
  ref,
  service,
  volume,
} from "railway/iac";

// Noms tels qu'ils apparaissent dans Railway (à aligner au premier plan).
const PROJECT = "champis";
const REPO = "adhumi/champis";
const BRANCH = "main";
const POSTGRES = "Postgres"; // nom par défaut du service Postgres Railway
const BUCKET = "champis"; // bucket des PMTiles, de l'amorçage et de l'instantané du cache
const VOLUME = "champis-data"; // volume de l'API, monté sur /data
const API_DOMAINS = ["champis.adhumi.fr"]; // domaines personnalisés de l'API ; [] si aucun

// Même image pour les trois services : le Dockerfile à la racine (uv, python:3.12-slim).
const build = { builder: "DOCKERFILE" as const, dockerfilePath: "Dockerfile" };

export default defineRailway((ctx) => {
  const db = postgres(POSTGRES);
  const tiles = bucket(BUCKET);
  const data = volume(VOLUME);

  // Variables du bucket telles que les injecte « Connect Service to Bucket », préréglage
  // « AWS SDK (Generic) » : les mêmes noms que .env.example, lus par botocore.
  const bucketEnv = {
    AWS_ENDPOINT_URL: ref(tiles, "ENDPOINT"),
    AWS_S3_BUCKET_NAME: ref(tiles, "BUCKET"),
    AWS_DEFAULT_REGION: ref(tiles, "REGION"),
    AWS_ACCESS_KEY_ID: ref(tiles, "ACCESS_KEY_ID"),
    AWS_SECRET_ACCESS_KEY: ref(tiles, "SECRET_ACCESS_KEY"),
  };
  // Clé Open-Meteo (plan Standard) : variable partagée du projet, les trois services en ont besoin.
  const openMeteo = { CHAMPIS_OPEN_METEO_API_KEY: ctx.shared.CHAMPIS_OPEN_METEO_API_KEY };

  // L'API : FastAPI, plusieurs workers uvicorn (CMD du Dockerfile ; pas de startCommand ici),
  // cache météo SQLite sur le volume, site statique, relais de tuiles. Aucune tâche de fond :
  // CHAMPIS_WARM_HOURS et CHAMPIS_NOTIFY_HOURS restent vides (ENV du Dockerfile) et ne doivent
  // pas être posées ici ; une valeur mise à la main dans Railway serait retirée par `apply`.
  const api = service("champis-api", {
    source: github(REPO, { branch: BRANCH }),
    build,
    healthcheck: "/health",
    healthcheckTimeout: 120,
    deploy: { restartPolicyType: "ON_FAILURE", restartPolicyMaxRetries: 5 },
    domains: API_DOMAINS.map((domain) => ({ domain, port: 8000 })),
    volumeMounts: { "/data": data },
    env: {
      ...bucketEnv,
      ...openMeteo,
      DATABASE_URL: db.env.DATABASE_URL,
      CHAMPIS_WORKERS: "2",
    },
  });

  // Pré-chauffe Open-Meteo, indice par département, météo précalculée : 2 h et 14 h UTC (3 h et
  // 15 h Paris en hiver, une heure plus tard en été ; le cron Railway est en UTC, on le garde fixe).
  // Pas de volume : --pull repart de l'instantané du cache publié dans le bucket, --publish dépose
  // le nouveau que l'API importe (CHAMPIS_CACHE_POLL_MINUTES). Doit se terminer (≈ 40 min pour la
  // France) ; si la passe précédente tourne encore, Railway saute l'exécution. Ni domaine, ni
  // health check, ni redémarrage (NEVER : une passe en échec ne doit pas repartir en boucle).
  const warm = service("champis-warm", {
    source: github(REPO, { branch: BRANCH }),
    build,
    start: "uv run champis-api -q warm --pull --publish",
    deploy: { cronSchedule: "0 2,14 * * *", restartPolicyType: "NEVER" },
    env: { ...bucketEnv, ...openMeteo },
  });

  // Notification « mes coins » à 6 h UTC (7 h Paris en hiver, 8 h en été), après la passe de 2 h :
  // --pull reprend le cache publié (aucun appel Open-Meteo sauf cellule froide). Postgres pour les
  // coins et les appareils, APNs pour l'envoi : clé .p8 (PEM), identifiant de clé et d'équipe en
  // variables partagées du projet ; le sujet est l'identifiant de bundle de l'app.
  const notify = service("champis-notify", {
    source: github(REPO, { branch: BRANCH }),
    build,
    start: "uv run champis-api -q notify --pull",
    deploy: { cronSchedule: "0 6 * * *", restartPolicyType: "NEVER" },
    env: {
      ...bucketEnv,
      ...openMeteo,
      DATABASE_URL: db.env.DATABASE_URL,
      CHAMPIS_APNS_KEY: ctx.shared.CHAMPIS_APNS_KEY,
      CHAMPIS_APNS_KEY_ID: ctx.shared.CHAMPIS_APNS_KEY_ID,
      CHAMPIS_APNS_TEAM_ID: ctx.shared.CHAMPIS_APNS_TEAM_ID,
      CHAMPIS_APNS_TOPIC: "fr.adhumi.champis",
    },
  });

  return project(PROJECT, { resources: [api, warm, notify, db, tiles, data] });
});
