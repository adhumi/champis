# Prompts pour générer les planches (Midjourney, Gemini)

Décision du 8 nov. 2026 (Adrien) : les planches sont des aquarelles générées par Midjourney ou
Gemini à partir des prompts ci-dessous, dans le style de l'image de référence (aquarelle de
girolles : lavis doux, sans contour à l'encre, deux sujets, herbe et fougère, mousse pâle, fond
blanc). Les images se déposent ici en `<id>.jpg` (carré, 2000 px, fond blanc, fichier de l'outil
tel quel), une par fichier espèce.

## Recette de cohérence

1. Commencer par la girolle (`cantharellus_cibarius`), l'espèce la plus proche de la référence,
   et garder la meilleure sortie comme **image de style** pour toutes les autres.
2. Même préfixe de style, même bloc de composition, même format carré pour toutes ; seul le
   bloc « sujet » change.
3. Midjourney : `--sref <URL de l'image de style> --sw 100`, même `--seed`, `--style raw`,
   `--ar 1:1`, `--s 100`, et `--no text, watermark, frame, border, cast shadow, background`.
   Générer les planches dans la même session, par lots, et choisir à chaque fois la variante dont
   la lumière et le vert du sol sont les plus proches de la référence.
4. Gemini (génération d'images) : joindre l'image de style à chaque demande et commencer le
   prompt par « In exactly the same style, palette and composition as the attached
   illustration, … » ; demander une image carrée ; enchaîner les planches dans la même conversation.
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

### cantharellus_amethysteus — Girolle améthyste

> Amethyst chanterelles (Cantharellus amethysteus): fleshy funnel-shaped cap, ochre-yellow
> densely dotted with tiny lilac to violet scales, most crowded toward the centre, with a wavy
> irregular margin; thick blunt forked pale yellow ridges running down the stem instead of
> gills; firm pale yellow stem tapering toward the base. The small one is a young button whose
> cap is almost entirely veiled in fine lilac scales. A couple of short silver fir needles and
> a fallen beech leaf on the moss.

### craterellus_cinereus — Craterelle cendrée

> Ashen chanterelles (Craterellus cinereus): small funnel-shaped cap, dark grey-black, thin,
> with a strongly lobed wavy margin and a small hole in the centre; underneath, well-formed
> forked bluish-grey ridges running down the stem instead of gills, clearly visible; slender
> hollow stem the same dark grey, paler toward the base; dark tones rendered as soft
> grey-brown and slate-blue watercolor, never flat pure black. The small one is tilted so its
> grey ridges show. A couple of fallen beech leaves on the moss.

### craterellus_lutescens — Chanterelle jaune

> Yellowfoot chanterelles (Craterellus lutescens): thin lobed funnel-shaped cap, yellowish-brown
> covered with fine darker brown fibrils, frilly irregular margin; underside almost smooth with
> only faint low veins, pale orange-yellow, no gills; hollow stem bright saffron-orange,
> flattened and grooved, tapering to the base. The small one is a young specimen with a
> rounded brown cap on a vivid orange stem. A few strands of pale green sphagnum moss and two
> short spruce needles on the moss.

### craterellus_tubaeformis — Chanterelle en tube

> Winter chanterelles (Craterellus tubaeformis): small slender funnel-shaped cap, dull brown to
> greyish-brown, thin and wavy, with a small hole in the centre opening into the hollow stem;
> underneath, widely spaced blunt forked grey-yellow ridges running down the stem instead of
> gills; long thin hollow stem, bright egg-yolk yellow, slightly flattened and grooved. The
> small one is a young specimen with a convex brown cap and inrolled margin on a thin yellow
> stem. A few short spruce needles and a sliver of soft rotten wood on the moss.

### hydnum_rufescens — Pied de mouton roux

> Terracotta hedgehog mushrooms (Hydnum rufescens): smaller and more regular than the common
> hedgehog, rounded cap rusty orange to apricot-tan, smooth and matte, sometimes with a small
> shallow dimple in the centre and a slightly paler wavy margin; underneath, short soft pale
> cream spines with an orange tinge hanging like tiny teeth instead of gills, stopping at the
> stem without running down it; slender central whitish stem, pale flesh-pink near the base.
> The small one is tilted so its spines show. A few dry spruce needles scattered on the moss.

### imleria_badia — Bolet bai

> Bay boletes (Imleria badia): smooth convex cap, rich chestnut to bay brown, slightly
> glossy and greasy-looking as if damp, with a thin paler rim; slender cylindrical stem, pale
> yellowish-buff with fine darker brown longitudinal streaks, no net pattern; sponge-like pore
> surface under the cap, cream-yellow to pale greenish-yellow, with one small blue-green
> bruise on its edge. The small one is a young button with a rounded dark brown cap and a
> short stocky stem. A few dry spruce needles and a small spruce cone scale on the moss.

### lepista_nuda — Pied bleu

> Wood blewits (Lepista nuda): fleshy smooth cap, lilac-violet with a soft brownish-tan flush
> spreading from the centre, the margin still inrolled; crowded bright lilac-violet gills; stout
> stem, lilac with fine silvery-white lengthwise fibres, slightly swollen at the base with a
> little fluffy pale violet mycelium. The small one in front is a young firm specimen, entirely
> violet with a strongly inrolled margin, slightly tilted so its violet gills show. A couple of
> fallen brown beech leaves on the moss.

### russula_cyanoxantha — Russule charbonnière (charbonnier)

> Charcoal burner brittlegills (Russula cyanoxantha): broad, firm, fleshy cap, convex then flattened with a shallow
> central dip, softly mottled with slate violet, lilac, blue-grey and olive green on the same cap, with a faint greasy
> sheen; crowded pure white gills, supple rather than brittle, a few forked near the stem; short, stout, pure white stem
> with no ring, finely veined lengthwise. The small one is a young specimen with a domed violet-grey cap tinged green at
> the rim, on a thick white stem. A couple of fallen beech leaves on the moss.

### russula_virescens — Russule verdoyante (palomet)

> Green-cracking brittlegills (Russula virescens): firm, fleshy cap, domed then flattened with a slight central dip,
> pale jade to verdigris green, dry and matte, its surface broken into small angular darker green patches over a creamy
> white background, the patches densest toward the margin; crowded white to cream gills; stout white stem with no ring,
> slightly mealy at the top and faintly rust-stained at the base. The small one is a young rounded button, paler green,
> with the cracking only just beginning at its edge. A couple of fallen oak leaves on the moss.

### suillus_granulatus — Bolet granulé

> Weeping boletes (Suillus granulatus): flattish convex cap, warm tan to orange-brown, smooth
> and sticky-looking with a soft sheen; pale lemon-yellow stem dotted with small
> brownish-yellow granules on its upper part, no ring; pore surface under the cap pale yellow
> with a few tiny milky-white droplets beading on the pores. The small one is a young button
> tilted to show its weeping yellow pores. A few dry pine needles and a short tuft of grass on
> the moss.

### suillus_luteus — Nonnette voilée

> Slippery jacks (Suillus luteus): convex cap, dark chocolate to chestnut brown, very shiny
> and slimy-looking with a wet glaze, edge slightly paler; short pale yellowish stem dotted
> with tiny brownish granules above a large flaring membranous ring, white tinged with dull
> violet-brown; pore surface under the cap bright lemon yellow. The small one is a young
> button whose underside is still covered by a whitish veil stretched from cap edge to stem.
> A few dry two-needle pine needles scattered on the moss.

### tricholoma_portentosum — Tricholome prétentieux

> Sooty-head mushrooms (Tricholoma portentosum): fleshy cap, steel-grey to dark grey with fine
> radiating black streaks, a broad central bump and faint lemon-yellow to olive tints near the
> margin, slightly shiny as if damp; crowded white gills with a soft pale yellow tinge; stout
> white stem with no ring, flushed pale yellow toward the top. The small one is a young button
> with a dark, almost blackish rounded cap and a short thick stem. A few dry pine needles and a
> pale grey tuft of lichen scattered on the moss.

### tricholoma_terreum — Petit-gris (tricholome terreux)

> Grey knight mushrooms (Tricholoma terreum): small slender cap, mouse-grey to grey-brown, finely
> felted and radially fibrillose like soft suede, conical to flattened with a low central bump and
> a thin, slightly paler, often split margin; crowded, fairly broad pale grey gills with a notched
> attachment; slim smooth white stem with no ring, fragile and slightly fibrous. The small one is a
> young specimen with a rounded, darker grey cap still curved over its stem. A few dry pine needles
> scattered on the moss.

### lactarius_deterrimus — Lactaire de l'épicéa

> False saffron milk caps (Lactarius deterrimus): orange cap, depressed in the centre, barely
> zoned, with large patches of verdigris green; orange gills with green stains; smooth
> unpitted orange stem with a paler band near the top. The small one in front is lying on its
> side showing its orange gills and a drop of orange milk turning wine-red. A few short
> spruce needles and a small spruce cone on the moss.

### lactarius_salmonicolor — Lactaire saumon

> Salmon milk caps (Lactarius salmonicolor): soft salmon-orange cap, depressed in the centre
> with an inrolled margin and faint concentric bands, no green tones at all; pale salmon
> gills; fairly long salmon-orange stem with a few darker orange pits. The small one is a
> young rounded specimen with a tightly inrolled margin. A few short flat fir needles and a
> tiny fir cone scale on the moss.

### lactarius_sanguifluus — Lactaire sanguin

> Bloody milk caps (Lactarius sanguifluus): pale orange to pinkish-buff cap, depressed in the
> centre with an inrolled margin, faintly zoned, with a few dull grey-green stains; crowded
> wine-pink gills; short stout pinkish-buff stem with a few wine-red pits. The small one in
> front is lying on its side showing its wine-pink gills and a drop of deep wine-red milk.
> A few dry pine needles and a small pale limestone pebble on the moss.

### lactifluus_volemus — Lactaire à lait abondant

> Weeping milk caps (Lactifluus volemus): broad dry velvety cap, tawny orange to rusty
> apricot-brown, slightly depressed in the centre; crowded pale cream to golden-yellow gills
> with a few brownish stains; firm stem the same tawny orange as the cap, paler at the top.
> The small one in front is lying on its side showing its cream gills beaded with several
> thick drops of white milk. A couple of fallen beech leaves on the moss.

## Exemple assemblé (Midjourney)

```
Botanical watercolor and colored pencil illustration in the manner of a naturalist field guide plate, soft hand-painted texture, delicate graded washes, no black ink outlines, gentle light from the upper left, pure white background, no shadow cast on the background, no text, no frame. Two mushrooms growing from a small patch of pale mossy green: one large mature specimen upright at centre-right, one smaller younger specimen in front at the lower left, a few bright green grass blades and small fern fronds around the base. Square format, subject centred and filling about 80% of the frame, three-quarter view slightly from above. Hedgehog mushrooms (Hydnum repandum): irregular lumpy cap, cream to pale apricot, with an inrolled margin; underneath, dense short pale cream spines hanging like tiny teeth instead of gills, clearly visible under the cap edge; short thick white stem, slightly off-centre. The small one is tilted so its spines show. --ar 1:1 --style raw --s 100 --sref <URL> --sw 100 --seed 4242 --no text, watermark, frame, border, cast shadow, background
```
