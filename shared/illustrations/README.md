# Illustrations des espèces

Une planche par espèce, `shared/illustrations/<id>.jpg` (carré, 2000 px, fond blanc, le fichier
produit par l'outil tel quel, sans recompression : 400 Ko environ, contre 3 Mo en PNG), pour les listes et le sélecteur d'espèce du site et de l'app, à la place du menu
déroulant. La photo de la fiche (`about.photo`) reste la photo.

Les planches sont des aquarelles générées par Midjourney ou Gemini à partir de `PROMPTS.md`, dans
le style d'une image de référence choisie par Adrien (8 nov. 2026) : lavis doux sans contour à
l'encre, deux sujets, herbe et fougère, mousse pâle, fond blanc. Le même préfixe de style et la
même composition pour les dix, seul le bloc « sujet » change ; la recette de cohérence est dans
`PROMPTS.md`. Une nouvelle espèce reçoit d'abord son bloc sujet là, puis son image ici.

Pourquoi générer plutôt que chercher : aucune collection libre (planches de Boudier, Rolland,
Wikimedia Commons) ne couvre les dix espèces dans un même style, les girolles pâle et
blanchissante n'ayant jamais été figurées dans les atlas anciens ; mélanger des sources casse la
cohérence d'une liste.

Les dix premières planches sont déposées (8 nov. 2026), puis quinze le 9 nov. (girolle améthyste,
craterelle cendrée, chanterelle jaune, bolet bai, pied de mouton roux, pied bleu, les quatre lactaires
ajoutés, les deux russules, les deux nonnettes, tricholome prétentieux ; générées en 2 048 px, environ
2 Mo, déposées telles quelles). La planche n'est pas un prérequis de la CI
(décision d'Adrien du 9 nov. 2026) : `scripts/check_shared.py` signale seulement son absence. Elle
l'est pour qu'une espèce soit **complète** (bloc `about`, photo, planche) et s'affiche : l'API ne sert
au site et à l'app que les espèces complètes (`GET /species`, indice par département, coins, carte).
Les dix-sept espèces ajoutées le 8 nov. 2026 (`docs/ESPECES-candidates-2026-11-08.md`) ont leur bloc
sujet dans `PROMPTS.md` ; deux attendent encore leur planche pour apparaître (chanterelle en tube, petit-gris).

Licence des images générées : à fixer (conditions de Midjourney ou de Gemini selon l'outil), à
noter ici.
