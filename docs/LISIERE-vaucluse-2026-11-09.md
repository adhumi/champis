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

Depuis le backoffice de champis-api (fiche de l'espèce, décision d'Adrien du 12 nov. 2026 : le
contrôle GBIF tourne sur le worker champis-jobs) :

1. **« Recalculer le terrain »** avec le département 84 seul (outil `batch`, `depts = 84`,
   `species = lactarius_deliciosus`) : BD Forêt, SoilGrids, MNT du Vaucluse, rasters `grid/84/`
   (`edge.tif` compris), T de référence de l'espèce. Un quart d'heure environ.
2. **« Contrôler »** (outil `check`) avec `département = 84`, la variante lisière `0,0,100,400` et le
   poids `0.1` : le worker télécharge les occurrences GBIF du département, évalue le T de
   référence, calcule un T variant **en mémoire** avec le bloc candidat (dans `data/T-variants/`,
   jamais dans les tuiles), l'évalue sur les **mêmes occurrences** et dépose les deux rapports dans
   le bucket sous `reports/`. Le journal de la tâche porte les deux AUC et le verdict ; la fiche
   liste les rapports.

Le même test depuis un poste :

```bash
uv run champis-pipeline download --dept 84
uv run champis-pipeline grid --dept 84
uv run champis-pipeline terrain --dept 84 --species lactarius_deliciosus
uv run champis-pipeline check --dept 84 --species lactarius_deliciosus --edge 0,0,100,400 --edge-weight 0.1
```

Le fichier espèce n'est jamais écrit par le test.

## Bloc candidat

Trapèze sur la distance à la lisière en mètres : facteur 1 dans les 100 premiers mètres de forêt,
nul au-delà de 400 m (Bonet 2012 : production des lactaires concentrée en bord de peuplement et de
piste ; le premier anneau de pixels est à 25 m). Le poids `edge` = 0,10 est prélevé **au prorata
sur tous les poids existants** (c'est ce que fait la variante), la somme reste 1 :

```json
"edge_m": { "min": 0, "opt_low": 0, "opt_high": 100, "max": 400 },
"weights": { "cover": 0.225, "ph": 0.27, "altitude": 0.18, "aspect": 0.135, "slope": 0.09, "edge": 0.10 }
```

Les bornes et le poids sont un point de départ : si le gain vient surtout des 50 premiers mètres,
resserrer `opt_high` ; ne jamais ajuster sur un point isolé (skill `validation-gbif`).

## Critère d'adoption

- Au moins **30 occurrences en forêt** dans le rapport, sinon « non évalué ».
- **Gain d'AUC ≥ 0,01** avec le bloc, et T moyen aux occurrences qui ne baisse pas.
- Sinon le bloc reste hors du fichier et le résultat est noté ici avec les deux AUC.

Le rapport de la variante applique ce critère lui-même (`entry` du `.json`, verdict dans le
`.html`) ; il mesure, il ne décide pas.

## Si le bloc est adopté

Skill `species-file` : le bloc et le poids entrent dans `species/lactarius_deliciosus.json` avec la
référence `bonet2012` et le résultat du test (AUC avec et sans, Vaucluse, date) ; `validate.py`
exige bloc et poids ensemble. L'empreinte de l'espèce change : ses tuiles T France sont à rerendre
et republier, ainsi que le G des lactaires (deux parties) ; les vecteurs ne bougent pas (T n'y est
pas). Mêmes tests ensuite pour les autres lactaires et les grisets, un département à la fois.

## Résultat

**12 nov. 2026, Vaucluse, lactaire délicieux : non évalué.** GBIF ne connaît que 10 occurrences
géolocalisées de l'espèce dans l'emprise du département (829 dans toute la France, 53 dans tout le
Sud-Est) ; 3 passent le filtre de précision, 1 seule tombe en forêt BD Forêt. Les deux AUC
(0,814 sans, 0,827 avec, T moyen aux occurrences 0,638 → 0,654) ne veulent rien dire sur un point.
Rapports : `reports/lactarius_deliciosus-84[-edge-0-0-100-400-w0.1].html` du bucket.

GBIF est très clairsemé en Provence pour toutes les espèces de Champis (quelques dizaines
d'occurrences par espèce sur tout le Sud-Est), dense dans le Doubs et le Jura. Le test d'entrée de
la lisière se refait donc sur le **Doubs (25)**, où les données existent, avec les lactaires qui y
poussent : lactaire saumon (380 occurrences géolocalisées, sapinières), lactaire de l'épicéa (259,
pessières), et le petit-gris (134) pour les grisets ; le lactaire délicieux (17 dans le Doubs)
attend une source plus dense ou un contrôle groupant plusieurs départements. Même bloc candidat,
même critère ; le résultat de chaque espèce est à noter ici.

**12 nov. 2026, Doubs, lactaire saumon : non évalué.** 380 occurrences géolocalisées, mais 354 ont
une incertitude déclarée de 1 à 5 km (le jeu national qui porte l'essentiel des données françaises
est géoréférencé à la commune), 19 sont arrondies : 7 retenues, 6 en forêt. AUC 0,764 → 0,815,
T moyen 0,529 → 0,526 : six points, rien à conclure. Même constat pour le lactaire de l'épicéa
(3 occurrences précises sur 259) et le petit-gris (0 sur 134) dans le Doubs.

**Ce que GBIF permet.** À l'échelle d'un facteur de lisière (bande de 100 m sur des pixels de 25 m),
seules les occurrences à moins de 100 m comptent : iNaturalist et quelques jeux naturalistes en
fournissent, le gros des données françaises non. Par espèce, la France entière en offre 150 à 210
(lactaire délicieux 208, lactaire saumon 189, petit-gris 171, lactaire de l'épicéa 145, lactaire
sanguin 67), dispersées sur plusieurs départements, Pyrénées, Cévennes et Alpes surtout. Un
département seul n'atteint jamais le seuil de 30 ; **un contrôle groupant plusieurs départements**
(positives de chaque département sur son propre raster T, fond tiré dans les mêmes départements)
l'atteint pour les quatre premières espèces. C'est l'évolution de l'outil `check` à faire avant de
reprendre le test ; en attendant, le facteur reste hors des fichiers.
