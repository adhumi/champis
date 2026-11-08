# Illustrations des espèces

Une planche SVG par espèce, `shared/illustrations/<id>.svg`, listée dans `index.json`. Elles
servent aux listes (sélecteur d'espèce du site et de l'app, à la place du menu déroulant) et
partout où une vignette vaut mieux qu'un nom latin. La photo de la fiche (`about.photo`) reste la
photo.

## Style, commun aux dix

Planche naturaliste simplifiée : contours à l'encre (`#3a2e22`, 1,6 px), aplats dégradés, lumière
en haut à gauche, fond transparent. Même cadre (`viewBox 0 0 240 240`), même composition : le
sujet principal à droite, un second sujet plus petit à gauche (jeune bouchon, sujet penché ou
renversé qui montre l'hyménium), ombres portées, mousse et débris du sol selon l'hôte (feuilles
sous feuillus, aiguilles sous conifères). Lisible à 44 px sur fond clair comme sombre.

Ce qui distingue chaque espèce vient de la littérature : couleur et forme du chapeau, réticule
du pied des bolets (blanc et fin chez *B. edulis*, brun et complet chez *B. reticulatus*), plis
décurrents des girolles, creux de la trompette, aiguillons du pied de mouton, zones, fossettes et
lait orange du lactaire.

## Comment elles sont faites

Dessinées par `scripts/draw_illustrations.py` (bibliothèque standard, sortie déterministe), jamais
retouchées à la main :

- `make illustrations` redessine tout ;
- `make shared` (la CI) vérifie que les fichiers sont ceux du générateur et qu'il y en a un par
  espèce, au même cadre, avec un `<title>` ;
- une nouvelle espèce : une entrée dans `SPECIES` du script (gabarit `bolete_plate`,
  `funnel_plate`, `hydnum_plate`, `lactarius_plate`, ou un nouveau si la silhouette n'existe pas),
  puis `make illustrations`.

Pourquoi générer plutôt que chercher : aucune collection libre (planches de Boudier, Rolland,
Wikimedia Commons) ne couvre les dix espèces dans un même style, les girolles pâle et
blanchissante n'ayant jamais été figurées dans les atlas anciens ; mélanger des sources casse la
cohérence d'une liste.

## Licence

CC0 1.0 : dessins propres au projet, réutilisables sans condition. Le crédit n'est pas requis.
