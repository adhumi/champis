# Champis — référentiel

Où et quand cueillir des champignons en France, à l'échelle de la parcelle forestière : [champis.app](https://champis.app). Gratuit, sans compte, construit sur de l'open data et sur la littérature mycologique.

Ce dépôt est le **référentiel** de Champis : ce que le pipeline, l'API, le site et l'app partagent, et rien d'autre. Il ne contient pas de code applicatif. Score d'un pixel de 25 m pour une espèce et un jour : `S = T × M_eff × Φ` (potentiel terrain, indice météo, fenêtre phénologique) ; le modèle complet est dans `species/SCHEMA.md`.

Rien ici ne dit qu'un champignon est comestible ni n'aide à l'identifier : une récolte se fait contrôler par un pharmacien ou une association mycologique.

## Contenu

```
species/      un fichier JSON par espèce, SCHEMA.md (le modèle), validate.py
mapping/      bdforet_to_hosts.json : les 32 codes TFV de la BD Forêt → hôtes
shared/       palette.json (classes et couleurs), vectors/ (contrat de parité Python/Swift),
              texts/ (articles du Guide, lus par le site et l'app), illustrations/ (une aquarelle par espèce),
              photos/ (la photo créditée de chaque fiche)
docs/         spec/ (copie expurgée de la spec), espèces candidates, test du facteur lisière,
              brouillons d'espèces en attente
scripts/      check_shared.py : contrôle de tout ce qui n'est pas un fichier espèce
.claude/      skills partagés : champis-model, scoring-parity, spec-sync, species-file, roadmap
```

Les skills de `.claude/skills/` sont des notes de travail en Markdown, écrites pour un assistant de code et lisibles par tous : `champis-model` résume le contrat du modèle, `species-file` la marche à suivre pour un fichier espèce.

## Vérifier

```bash
make check     # fichiers espèces, table BD Forêt, JSON, index des textes, vecteurs, planches, photos
```

Python 3.12, bibliothèque standard seulement, sans réseau : rien à installer. C'est exactement ce que lance la CI. `make` seul liste les cibles.

## Proposer une modification

Une espèce, une correction de plage ou de poids avec sa référence, un texte du Guide, une photo libre créditée : voir [`CONTRIBUTING.md`](CONTRIBUTING.md). En bref, pour une espèce :

1. Modifier `species/<id>.json` en partant d'un fichier existant ; une source par règle (`species/SCHEMA.md`).
2. `make check` : `species/validate.py` doit afficher `ok`.
3. Les vecteurs de parité (`shared/vectors/`) dépendent des espèces et ne se modifient jamais à la main : ils sont régénérés depuis champis-api (`uv run champis-vectors`) dans la même PR. Sans champis-api, ouvrir la PR sans eux : l'auteur les régénérera.
4. Une branche, une PR, la CI verte.

Une décision structurante (formule, schéma, format partagé) passe d'abord par une issue : la spec fait foi.

## Les autres dépôts

Le référentiel est lu par trois autres dépôts :

| Dépôt | Contenu | Lit le référentiel |
| --- | --- | --- |
| `adhumi/champis-api` | pipeline terrain, API météo et crons, sur `api.champis.app` | sous-module `champis/` |
| `adhumi/champis-web` | le site `champis.app` (service statique) | sous-module `champis/` |
| `adhumi/champis-ios` | l'app iOS, iPadOS et macOS | copies : `scripts/sync-vectors.sh`, `sync-texts.sh`, `sync-skills.sh` |

Une modification ici n'atteint la production qu'après la PR qui avance le sous-module (`make referential` dans champis-api ou champis-web), ou après la synchronisation dans champis-ios. Les chemins `species/`, `mapping/`, `shared/` et `.claude/skills/` sont lus tels quels par ces dépôts : ils ne se déplacent pas.

## La spec

Chaque décision de conception est écrite dans la spec avant d'être codée. C'est un document tenu par l'auteur ; une copie est versionnée dans ce dépôt, dans [`docs/spec/`](docs/spec/README.md). Elle est expurgée (coûts, comparaisons avec des tiers nommés, détails d'infrastructure et de sécurité, quelques informations personnelles) et se met à jour par PR à partir du document, jamais à la main. `species/SCHEMA.md` décrit le modèle, et un changement de fond se propose par une issue.

## Signaler une faille

Par courriel à hello@champis.app, pas par une issue publique : voir [`SECURITY.md`](SECURITY.md). La même adresse vaut pour le site, l'API et l'app.

## Licences

Code (`species/validate.py`, `scripts/`) : MIT (`LICENSE`). Fichiers d'espèces, table BD Forêt, palette, vecteurs, textes du Guide, aquarelles et documents de `docs/` : CC BY 4.0 (`LICENSE-DATA.md`), réutilisables librement en citant Champis. Les photos de `shared/photos/` gardent la licence de leur auteur (`shared/photos/README.md`).
