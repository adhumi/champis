# Lisière : test d'entrée du facteur `edge_m` sur le Vaucluse (84)

Décision d'Adrien du 9 nov. 2026 : le facteur terrain optionnel `edge_m` (palier 2, spec › Scoring ›
Facteurs de sol et de paysage) est codé dans champis-api mais aucune espèce ne l'emploie. La règle
d'entrée d'un facteur optionnel s'applique : il n'entre dans un fichier espèce que s'il **relève
l'AUC GBIF** d'un département de référence. Première espèce : le **lactaire délicieux** (lisières,
pare-feu et bords de pistes des pinèdes, Bonet 2012) ; département de référence : le **Vaucluse (84)**,
pinèdes de pin d'Alep et de pin sylvestre du Ventoux et du Luberon, choisi par Adrien.

Le test demande les données IGN (BD Forêt V2 du 84, BD ALTI) et SoilGrids du département : il se
lance depuis le backoffice de champis-api ou un poste local, pas depuis une session sans réseau.

## Protocole

Depuis un clone de champis-api (sous-module à jour) :

```bash
# 1. données et rasters du département (edge.tif compris, étape grid)
uv run champis-pipeline download --dept 84
uv run champis-pipeline grid --dept 84
# 2. T de référence, sans le bloc, et son AUC
uv run champis-pipeline terrain --dept 84 --species lactarius_deliciosus
uv run champis-pipeline check --dept 84 --species lactarius_deliciosus
cp reports/lactarius_deliciosus-84.json reports/lactarius_deliciosus-84-sans-lisiere.json
# 3. le bloc candidat ci-dessous dans champis/species/lactarius_deliciosus.json (copie de travail,
#    pas de commit), puis T et AUC avec le bloc
uv run champis-pipeline terrain --dept 84 --species lactarius_deliciosus --force
uv run champis-pipeline check --dept 84 --species lactarius_deliciosus
```

`check` lit le raster T courant de l'espèce ; les occurrences GBIF sont en cache après le premier
appel (`data/raw/gbif/`), les deux mesures portent donc exactement sur les mêmes points.

## Bloc candidat

Trapèze sur la distance à la lisière en mètres : facteur 1 dans les 100 premiers mètres de forêt,
nul au-delà de 400 m (Bonet 2012 : production des lactaires concentrée en bord de peuplement et de
piste ; le premier anneau de pixels est à 25 m). Le poids vient de `cover` et `ph`, la somme reste 1.

```json
"edge_m": { "min": 0, "opt_low": 0, "opt_high": 100, "max": 400 },
"weights": { "cover": 0.20, "ph": 0.25, "altitude": 0.20, "aspect": 0.15, "slope": 0.10, "edge": 0.10 }
```

Les bornes et le poids sont un point de départ : si le gain vient surtout des 50 premiers mètres,
resserrer `opt_high` ; ne jamais ajuster sur un point isolé (skill `validation-gbif`).

## Critère d'adoption

- Au moins **30 occurrences en forêt** dans le rapport, sinon « non évalué ».
- **Gain d'AUC ≥ 0,01** avec le bloc, et T moyen aux occurrences qui ne baisse pas.
- Sinon le bloc reste hors du fichier et le résultat est noté ici avec les deux AUC.

## Si le bloc est adopté

Skill `species-file` : le bloc et le poids entrent dans `species/lactarius_deliciosus.json` avec la
référence `bonet2012` et le résultat du test (AUC avec et sans, Vaucluse, date) ; `validate.py`
exige bloc et poids ensemble. L'empreinte de l'espèce change : ses tuiles T France sont à rerendre
et republier, ainsi que le G des lactaires (deux parties) ; les vecteurs ne bougent pas (T n'y est
pas). Mêmes tests ensuite pour les autres lactaires et les grisets, un département à la fois.

## Résultat

À compléter après le test : AUC sans / avec, occurrences en forêt, décision.
