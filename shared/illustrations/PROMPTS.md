# Prompts pour générer les planches (Midjourney, Gemini)

Décision du 8 nov. 2026 (Adrien) : les planches sont des aquarelles générées par Midjourney ou
Gemini à partir des prompts ci-dessous, dans le style de l'image de référence (aquarelle de
girolles : lavis doux, sans contour à l'encre, deux sujets, herbe et fougère, mousse pâle, fond
blanc). Les images se déposent ici en `<id>.jpg` (carré, 2000 px, fond blanc, fichier de l'outil
tel quel), une par fichier espèce.

## Recette de cohérence

1. Commencer par la girolle (`cantharellus_cibarius`), l'espèce la plus proche de la référence,
   et garder la meilleure sortie comme **image de style** pour toutes les autres.
2. Même préfixe de style, même bloc de composition, même format carré pour les dix ; seul le
   bloc « sujet » change.
3. Midjourney : `--sref <URL de l'image de style> --sw 100`, même `--seed`, `--style raw`,
   `--ar 1:1`, `--s 100`, et `--no text, watermark, frame, border, cast shadow, background`.
   Générer les dix dans la même session, par lots, et choisir à chaque fois la variante dont
   la lumière et le vert du sol sont les plus proches de la référence.
4. Gemini (génération d'images) : joindre l'image de style à chaque demande et commencer le
   prompt par « In exactly the same style, palette and composition as the attached
   illustration, … » ; demander une image carrée ; enchaîner les dix dans la même conversation.
5. Vérifier chaque sortie à 44 px sur fond clair et sombre (une liste, pas une fiche) : le
   sujet doit remplir 80 % du cadre, sans texte ni cadre.

## Blocs communs (anglais, les modèles y répondent mieux)

**Style** :

> Botanical watercolor and colored pencil illustration in the manner of a naturalist field
> guide plate, soft hand-painted texture, delicate graded washes, no black ink outlines,
> gentle light from the upper left, pure white background, no shadow cast on the background,
> no text, no frame.

**Composition** :

> Two mushrooms growing from a small patch of pale mossy green: one large mature specimen
> upright at centre-right, one smaller younger specimen in front at the lower left, a few
> bright green grass blades and small fern fronds around the base. Square format, subject
> centred and filling about 80% of the frame, three-quarter view slightly from above.

Prompt complet = Style + Composition + Sujet (+ paramètres Midjourney).

## Sujets, une espèce par bloc

### boletus_edulis — Cèpe de Bordeaux

> Porcini mushrooms (Boletus edulis): broad hemispherical to convex cap, chestnut to hazelnut
> brown, smooth and slightly glossy, with a thin pale whitish rim; thick bulbous club-shaped
> stem, pale cream to light ochre, with a fine white net-like reticulation on its upper part;
> sponge-like pore surface under the cap, white to pale yellow-green. The small one is a
> rounded young button whose cap is barely wider than its fat stem. A couple of fallen oak
> leaves on the moss.

### boletus_aereus — Cèpe bronzé

> Bronze boletes (Boletus aereus): very dark bronze-brown cap, almost black, velvety and
> matte, slightly uneven; stout stem ochre-brown with a fine brown net-like reticulation over
> most of its length; pore surface under the cap white turning pale yellow. The small one is a
> young button with a dark rounded cap. A couple of fallen oak leaves on the moss.

### boletus_pinophilus — Cèpe des pins

> Pine boletes (Boletus pinophilus): deep wine-red to reddish-brown cap, slightly bumpy and
> matte; very thick barrel-shaped stem, reddish-ochre with a brownish-red net-like
> reticulation; pore surface under the cap white turning yellow-olive. The small one is a
> stocky young button. A few dry pine needles scattered on the moss.

### boletus_reticulatus — Cèpe d'été

> Summer boletes (Boletus reticulatus): light ochre-tan to pale brown cap, dry and matte,
> finely cracked like parched earth; stem pale ochre, entirely covered with a prominent brown
> net-like reticulation from top to bottom; pore surface under the cap white turning pale
> yellow. The small one is a young button with a slightly cracked cap. A couple of fallen oak
> leaves on the moss.

### cantharellus_cibarius — Girolle

> Golden chanterelles (Cantharellus cibarius): egg-yolk yellow throughout, funnel-shaped cap
> with a wavy, irregularly lobed margin, thick blunt forked ridges running down the stem
> instead of gills, stem the same yellow tapering toward the base. Warm golden to light orange
> tones.

### cantharellus_pallens — Girolle pâle

> Pale chanterelles (Cantharellus pallens): stout and fleshy, cap pale cream to almost white
> with a fine frosty white bloom on top, wavy margin; underside ridges and stem pale yellow,
> with rusty-orange bruises where the flesh has been touched; broader and squatter than a
> common chanterelle.

### cantharellus_alborufescens — Girolle blanchissante

> Whitening chanterelles (Cantharellus alborufescens): small and slender, cap cream to ivory
> white with a wavy margin, underside ridges and stem whitish to very pale yellow, with
> distinct pinkish-red to rust-red reddening on the stem and on bruised spots; a few small
> leathery evergreen oak leaves on the moss.

### craterellus_cornucopioides — Trompette de la mort

> Black trumpet mushrooms (Craterellus cornucopioides): deep hollow trumpet shape open to the
> base, inside dark grey-black to brownish-black, outer surface ash-grey with faint wrinkles,
> broad wavy flaring margin; dark tones rendered as soft grey-brown watercolor, never flat
> pure black. A couple of fallen beech leaves on the moss.

### hydnum_repandum — Pied de mouton

> Hedgehog mushrooms (Hydnum repandum): irregular lumpy cap, cream to pale apricot, with an
> inrolled margin; underneath, dense short pale cream spines hanging like tiny teeth instead
> of gills, clearly visible under the cap edge; short thick white stem, slightly off-centre.
> The small one is tilted so its spines show.

### lactarius_deliciosus — Lactaire délicieux

> Saffron milk caps (Lactarius deliciosus): orange cap with concentric darker orange rings,
> depressed in the centre, inrolled margin; orange gills; short hollow orange stem with darker
> orange pits, a few dull green stains on cap and stem. The small one in front is lying on its
> side showing its bright orange gills and a drop of carrot-orange milk. A few dry pine needles
> scattered on the moss.

## Exemple assemblé (Midjourney)

```
Botanical watercolor and colored pencil illustration in the manner of a naturalist field guide plate, soft hand-painted texture, delicate graded washes, no black ink outlines, gentle light from the upper left, pure white background, no shadow cast on the background, no text, no frame. Two mushrooms growing from a small patch of pale mossy green: one large mature specimen upright at centre-right, one smaller younger specimen in front at the lower left, a few bright green grass blades and small fern fronds around the base. Square format, subject centred and filling about 80% of the frame, three-quarter view slightly from above. Hedgehog mushrooms (Hydnum repandum): irregular lumpy cap, cream to pale apricot, with an inrolled margin; underneath, dense short pale cream spines hanging like tiny teeth instead of gills, clearly visible under the cap edge; short thick white stem, slightly off-centre. The small one is tilted so its spines show. --ar 1:1 --style raw --s 100 --sref <URL> --sw 100 --seed 4242 --no text, watermark, frame, border, cast shadow, background
```
