# Copie de la spec

Ce dossier contient une copie de la spec de Champis, le document où chaque décision de conception
est écrite avant d'être codée. La source reste le doc « Spec — Champis (carte de cueillette) »,
tenu par l'auteur du projet hors de ce dépôt ; la copie est là pour qu'un contributeur puisse la
lire.

| Fichier | Onglet du doc | Révision copiée |
| --- | --- | --- |
| [`spec.md`](spec.md) | Spec — Champis (carte de cueillette) | 295 |
| [`references-phase-0.md`](references-phase-0.md) | Références phase 0 | 8 |

Export du 14 nov. 2026.

## Une copie expurgée

Ce n'est pas le document entier. En sont retirés les coûts, les comparaisons avec des tiers
nommés, les détails d'infrastructure et de sécurité, et quelques informations personnelles. Les
retraits ne sont pas signalés dans le texte, et le reste n'est pas réécrit : c'est l'export du doc,
moins ces passages. Une phrase peut donc renvoyer à un passage ou à un document qui n'est pas
publié ici.

## Ce qu'il faut savoir en la lisant

- C'est un journal de décisions autant qu'une description : les sections gardent leur historique
  (« État au… », « Tranché le… »), et une ligne ancienne peut être remplacée par une plus récente
  plus bas. En cas de contradiction, la décision la plus récente l'emporte.
- La copie peut avoir du retard sur le doc. La date et les révisions ci-dessus disent de quand elle
  est.
- Deux schémas embarqués (le circuit d'une tâche et la maquette de l'onglet Espèces du backoffice)
  ne s'exportent pas : il n'en reste que la légende, `[embedded content: …]`.

## Mise à jour

On ne modifie pas ces fichiers à la main. Après un changement du doc, la copie est refaite par un
nouvel export de chaque onglet, expurgée de la même façon, et proposée par PR ; ce fichier reçoit
alors la nouvelle date et les nouvelles révisions.

## Proposer un changement

Un changement de fond se propose par une issue dans ce dépôt, en citant la section concernée et ce
qui devrait changer, avec sa source s'il s'agit d'une règle du modèle. Une PR qui modifie
`spec.md` ou `references-phase-0.md` directement ne sera pas fusionnée : la décision se prend dans
le doc, puis la copie suit.
