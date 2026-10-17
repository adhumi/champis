# web

Carte web jetable de la phase 1 : une page statique (MapLibre GL + PMTiles, chargés par CDN, aucun build) qui affiche le potentiel terrain T produit par le pipeline. Deviendra champis.adhumi.fr en phase 3.

## Lancer

Les tuiles sont des PNG de données (gris = T × 254, alpha 0 = hors forêt) : la page lit `shared/palette.json` pour les seuils et les couleurs, et `species/<id>.json` pour les noms et les groupes. Il faut donc servir **la racine du dépôt** :

```bash
python3 -m http.server 8000          # depuis la racine du dépôt
open http://localhost:8000/web/
```

Puis glisser un ou plusieurs `data/tiles/T-*.pmtiles` dans la zone prévue (ou cliquer dessus). L'espèce est déduite du nom du fichier (`T-<espèce>-…`).

Avec un serveur qui gère les requêtes `Range` (`npx serve .`, nginx, un bucket…), on peut aussi passer les tuiles en URL :

```
http://localhost:3000/web/?tiles=../data/tiles/T-boletus_edulis-…pmtiles,../data/tiles/T-boletus_aereus-…pmtiles
```

(`python -m http.server` ne gère pas `Range`, d'où le glisser-déposer.)

## Ce que fait la page

- Couche par espèce, ou **max du groupe** (cèpes, girolles) quand plusieurs espèces d'un groupe sont chargées — règle 9 du modèle.
- Colorisation côté client selon `shared/palette.json` (seuils et hex lus tels quels, rien en dur).
- Fonds : Plan IGN, orthophoto IGN (WMTS Géoplateforme, sans clé) ou OpenStreetMap.
- Clic sur la carte : valeur de T et classe au point cliqué (lue dans la tuile z15).
- Position dans l'URL (`#zoom/lat/lon`) pour partager une vue.

## Pas encore là

Le scoring `M × Φ` côté client (`web/src/scoring.js`, skill `scoring-parity`) et l'appel à l'API viennent en phase 2 : cette page ne montre que T.
