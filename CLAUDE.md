# Champis — référentiel

Cartes de cueillette de champignons (France, 25 m). Pensé d'abord pour Adrien et ses proches, puis ouvert à tous, infrastructure financée par dons (spec, 30 oct. 2026). La spec vit dans le doc « Spec — Champis » ; sa copie publique, expurgée, est dans `docs/spec/` (mise à jour par PR après un changement du doc, jamais à la main) ; les skills `.claude/skills/*` disent comment travailler ici — lis `champis-model` avant de toucher une espèce, la palette ou les vecteurs.

Découpage des dépôts (spec › Produit › Étape C, lot C7, 6 nov. 2026) : ce dépôt est le référentiel, partagé par `adhumi/champis-api` (pipeline, API, crons, sur `api.champis.app`) et `adhumi/champis-web` (site `champis.app`), qui l'ont en sous-module `champis/`, et par `adhumi/champis-ios`, qui en copie les vecteurs, les textes et trois skills par ses scripts `sync-*.sh`. Il ne contient pas de code applicatif.

## Structure

```
species/      fichiers espèces JSON + SCHEMA.md + validate.py   (skill species-file)
mapping/      bdforet_to_hosts.json : 32 codes TFV → hôtes
shared/       palette.json (seuils, échelle, encodages des tuiles T, G, A et E), vectors/ (contrat de parité Python/Swift) (skill scoring-parity), texts/ (articles du Guide, app et site), illustrations/ (prompts des planches, puis les images), photos/ (copies des photos créditées des fiches)
scripts/      check_shared.py : JSON, index des textes, vecteurs, planches, photos
docs/         spec/ (copie publique expurgée de la spec), espèces candidates (ajoutées, en attente, écartées) et brouillons/ en attente de décision
```

## Outillage

- `make check` = la CI : `species/validate.py` puis `scripts/check_shared.py`. Python 3.12, bibliothèque standard, sans réseau.
- Les chemins `species/`, `mapping/`, `shared/` et `.claude/skills/{champis-model,scoring-parity,spec-sync,species-file,roadmap}` sont lus tels quels par les trois autres dépôts (sous-module, liens de skills, scripts de synchronisation de l'app) : ne pas les déplacer.
- Illustrations (`shared/illustrations/`) : aquarelles générées (Midjourney ou Gemini) à partir de `PROMPTS.md`, une par espèce (`<id>.jpg`), dans le style d'une image de référence ; une nouvelle espèce reçoit d'abord son bloc sujet dans `PROMPTS.md`.
- Photos (`shared/photos/`) : la copie, sans retouche, de la photo Wikimedia Commons de `about.photo`, une par espèce (`<id>.jpg`) ; site et app l'affichent d'ici, avec le crédit, pour ne rien demander à Wikimedia. Changer `about.photo` et le fichier dans la même PR ; chaque photo garde la licence de son auteur (`shared/photos/README.md`).
- Vecteurs (`shared/vectors/`) : générés uniquement par champis-api (`uv run champis-vectors` écrit dans son sous-module `champis/`), jamais à la main. Un changement d'espèce change leur empreinte : vecteurs régénérés dans la même PR, sinon la CI de champis-api échoue à la prochaine avancée du sous-module.

## Règles

- Jamais de commit poussé sur `main` sans PR : branche, PR, CI verte, fusion (règle du 30 oct. 2026).
- Jamais de valeur d'espèce dans le code des autres dépôts : tout vient de `species/*.json`.
- Jointure BD Forêt sur `CODE_TFV` uniquement.
- Une modification ici n'atteint la production qu'après la PR qui avance le sous-module dans champis-api et champis-web (`make referential`), et la synchronisation dans champis-ios.
- Toute décision structurante passe par la spec avant le code (skill `spec-sync`) ; en cas de doute, demander à Adrien.
- Les issues GitHub sont la source de vérité de ce qui reste à faire (décision du 17 nov. 2026, skill `roadmap`) : lire les issues ouvertes avant de commencer une tâche ; tout ce qui est remis à plus tard, découvert en chemin ou laissé hors périmètre devient une issue, jamais un « reste à faire » dans un message, un README ou un commentaire ; une PR cite son issue (`Closes #N`). Jamais de faille non corrigée, de secret ni de coût dans une issue : elles seront publiques.
