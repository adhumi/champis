# Champis — référentiel

Où et quand cueillir des champignons en France, à l'échelle de la parcelle forestière : [champis.app](https://champis.app). Gratuit, sans compte, construit sur de l'open data et sur la littérature mycologique.

Ce dépôt est le **référentiel** de Champis : ce que le pipeline, l'API, le site et l'app partagent, et rien d'autre. Score d'un pixel de 25 m pour une espèce et un jour : `S = T × M_eff × Φ` (potentiel terrain, indice météo, fenêtre phénologique) ; le modèle complet est dans `species/SCHEMA.md`.

## Contenu

```
species/      un fichier JSON par espèce, SCHEMA.md (le modèle), validate.py
mapping/      bdforet_to_hosts.json : les 32 codes TFV de la BD Forêt → hôtes
shared/       palette.json (classes et couleurs), vectors/ (contrat de parité Python/Swift),
              texts/ (articles du Guide, lus par le site et l'app)
docs/         audit produit et plan (6 nov. 2026)
.claude/      skills partagés : champis-model, scoring-parity, spec-sync, species-file
```

## Les autres dépôts

Découpage des dépôts du 6 nov. 2026 (spec › Produit › Étape C, lot C7) :

| Dépôt | Contenu | Lit le référentiel |
| --- | --- | --- |
| `adhumi/champis-api` | pipeline terrain, API météo et crons, sur `api.champis.app` | sous-module `champis/` |
| `adhumi/champis-web` | le site `champis.app` (service statique) | sous-module `champis/` |
| `adhumi/champis-ios` | l'app iOS, iPadOS et macOS | copies : `scripts/sync-vectors.sh`, `sync-texts.sh`, `sync-skills.sh` |

Une modification ici n'atteint la production qu'après la PR qui avance le sous-module (`make referential` dans champis-api ou champis-web), ou après la synchronisation dans champis-ios.

## Modifier une espèce

Skill `species-file`. En bref :

1. Modifier `species/<id>.json` en partant d'un fichier existant ; une source par règle.
2. `make check` (= la CI) : `species/validate.py` doit afficher `ok`.
3. Les vecteurs de parité dépendent des espèces : les régénérer depuis champis-api (`uv run champis-vectors`, qui écrit dans son sous-module `champis/`), et les committer ici dans la même PR. La CI de champis-api vérifie qu'ils sont à jour (`champis-vectors --check`).
4. Reporter la règle dans la spec (skill `spec-sync`).

## Vérifier

```bash
make check     # fichiers espèces, table BD Forêt, JSON, index des textes, vecteurs
```

Python 3.12, bibliothèque standard seulement, sans réseau.

## Licences

Code (`species/validate.py`, `scripts/`) : MIT (`LICENSE`). Fichiers d'espèces, table BD Forêt, palette, vecteurs et textes du Guide : CC BY 4.0 (`LICENSE-DATA.md`), réutilisables librement en citant Champis.
