# Illustrations des espèces

Une planche par espèce, `shared/illustrations/<id>.jpg` (carré, 2 000 px, fond blanc, JPEG de
qualité 80 en 4:2:0, sans EXIF : 400 Ko environ, contre 3 Mo en PNG ; une image générée à une autre
taille est ramenée à ce gabarit, décision d'Adrien du 9 nov. 2026), pour les listes et le sélecteur
d'espèce du site et de l'app, à la place du menu déroulant. La photo de la fiche (`about.photo`) reste la photo.

Les planches sont des aquarelles générées par Midjourney ou Gemini à partir de `PROMPTS.md`, dans
le style d'une image de référence choisie par Adrien (8 nov. 2026) : lavis doux sans contour à
l'encre, deux sujets, herbe et fougère, mousse pâle, fond blanc. Le même préfixe de style et la
même composition pour les dix, seul le bloc « sujet » change ; la recette de cohérence est dans
`PROMPTS.md`. Une nouvelle espèce reçoit d'abord son bloc sujet là, puis son image ici.

Pourquoi générer plutôt que chercher : aucune collection libre (planches de Boudier, Rolland,
Wikimedia Commons) ne couvre les dix espèces dans un même style, les girolles pâle et
blanchissante n'ayant jamais été figurées dans les atlas anciens ; mélanger des sources casse la
cohérence d'une liste.

Les dix premières planches sont déposées (8 nov. 2026), puis les dix-sept des espèces ajoutées le
9 nov. (générées en 2 048 px et ~2 Mo, ramenées au gabarit commun). La planche n'est pas un prérequis de la CI
(décision d'Adrien du 9 nov. 2026) : `scripts/check_shared.py` signale seulement son absence. Elle
l'est pour qu'une espèce soit **complète** (bloc `about`, photo, planche) et s'affiche : l'API ne sert
au site et à l'app que les espèces complètes **dont les tuiles T France sont publiées** (`GET /species`,
indice par département, coins, carte ; `champis_api.catalog`, décision du 9 nov. 2026).
Les vingt-sept espèces ont leur planche (9 nov. 2026) ; une nouvelle espèce reçoit d'abord son bloc
sujet dans `PROMPTS.md`, puis sa planche ici, et n'apparaît qu'avec elle.

Licence des images générées : les vingt-sept planches sont générées avec Gemini (Google) par Adrien ;
elles relèvent des conditions d'utilisation de Google pour l'IA générative, qui laissent à
l'utilisateur les droits sur les sorties qu'il génère. À revoir si l'outil change.
