# Champis — référentiel

Cartes de cueillette de champignons (France, 25 m). Pensé d'abord pour Adrien et ses proches, puis ouvert à tous, infrastructure financée par dons (spec, 30 oct. 2026). La spec vit dans le doc « Spec — Champis » ; les skills `.claude/skills/*` disent comment travailler ici — lis `champis-model` avant de toucher une espèce, la palette ou les vecteurs.

Découpage des dépôts (spec › Produit › Étape C, lot C7, 6 nov. 2026) : ce dépôt est le référentiel, partagé par `adhumi/champis-api` (pipeline, API, crons, sur `api.champis.app`) et `adhumi/champis-web` (site `champis.app`), qui l'ont en sous-module `champis/`, et par `adhumi/champis-ios`, qui en copie les vecteurs, les textes et trois skills par ses scripts `sync-*.sh`. Il ne contient pas de code applicatif.

## Structure

```
species/      fichiers espèces JSON + SCHEMA.md + validate.py   (skill species-file)
mapping/      bdforet_to_hosts.json : 32 codes TFV → hôtes
shared/       palette.json, vectors/ (contrat de parité Python/Swift) (skill scoring-parity), texts/ (articles du Guide, app et site)
scripts/      check_shared.py : JSON, index des textes, vecteurs
docs/         audit produit et plan
```

## Outillage

- `make check` = la CI : `species/validate.py` puis `scripts/check_shared.py`. Python 3.12, bibliothèque standard, sans réseau.
- Les chemins `species/`, `mapping/`, `shared/` et `.claude/skills/{champis-model,scoring-parity,spec-sync,species-file}` sont lus tels quels par les trois autres dépôts (sous-module, liens de skills, scripts de synchronisation de l'app) : ne pas les déplacer.
- Vecteurs (`shared/vectors/`) : générés uniquement par champis-api (`uv run champis-vectors` écrit dans son sous-module `champis/`), jamais à la main. Un changement d'espèce change leur empreinte : vecteurs régénérés dans la même PR, sinon la CI de champis-api échoue à la prochaine avancée du sous-module.

## Règles

- Jamais de commit poussé sur `main` sans PR : branche, PR, CI verte, fusion (règle du 30 oct. 2026).
- Jamais de valeur d'espèce dans le code des autres dépôts : tout vient de `species/*.json`.
- Jointure BD Forêt sur `CODE_TFV` uniquement.
- Une modification ici n'atteint la production qu'après la PR qui avance le sous-module dans champis-api et champis-web (`make referential`), et la synchronisation dans champis-ios.
- Toute décision structurante passe par la spec avant le code (skill `spec-sync`) ; en cas de doute, demander à Adrien.
