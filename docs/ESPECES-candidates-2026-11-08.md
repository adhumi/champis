# Espèces comestibles : ce qui entre, ce qui attend, ce qui reste dehors

État au 8 nov. 2026. Demande d'Adrien : « étudie en profondeur et ajoute tout ce qui est ajoutable, consigne le reste ; pense aussi au griset du Ventoux ».

Dix-sept espèces entrent dans le référentiel, ce qui porte Champis à vingt-sept espèces en onze groupes. Trois autres ont un fichier complet mais attendent une décision d'Adrien (`docs/brouillons/`). Vingt-cinq restent dehors, pour une raison dite ci-dessous avec ce qui les rendrait ajoutables. Les dix-sept espèces n'apparaissent sur le site et dans l'app qu'avec leur planche d'illustration, à générer d'après `shared/illustrations/PROMPTS.md` : une espèce est complète quand son fichier porte le bloc `about`, une photo et sa planche, et l'API ne sert que les espèces complètes dont les tuiles T France sont publiées dans le bucket (décisions d'Adrien du 9 nov. 2026). La planche n'est pas un prérequis de la CI. Les dix-sept planches sont déposées le 9 nov. ; restent les tuiles à rendre et publier.

## Comment on a trié

Une espèce entre si les cinq conditions tiennent.

1. **Habitat forestier lisible.** L'hôte est une essence que la BD Forêt V2 sépare : chênes, hêtre, châtaignier, chaque pin, sapin-épicéa, mélèze, douglas. Hors forêt, T vaut 0.
2. **Saison dans l'année civile.** Le schéma refuse une saison à cheval sur le 1er janvier. Une espèce qui pousse jusqu'en janvier s'arrête au 31 décembre, et sa fiche le dit.
3. **Données de contrôle suffisantes.** Il faut au moins 150 occurrences GBIF géolocalisées en France, pour que le contrôle `champis-pipeline check` ait du sens.
4. **Pas de jumeau mortel à l'état cueilli.** Une confusion mortelle documentée n'exclut pas l'espèce. Elle est écrite en tête des confusions de la fiche, comme l'amanite phalloïde pour le petit-gris. Ce qui exclut, c'est une forme cueillie presque identique à une espèce mortelle : l'œuf d'oronge et l'œuf de phalloïde, l'agaric des bois et les amanites blanches.
5. **Pas de question de conservation ou de santé ouverte.** Quand l'espèce décline en Europe ou que sa comestibilité est contestée, la décision revient à Adrien.

La première version de ce tri disait « aucun sosie mortel ». Elle ne tenait pas. Les victimes suédoises du cortinaire très joli l'avaient pris pour des girolles ou des chanterelles en tube (Holmdahl & Blohmé 1995, 22 cas, 9 insuffisances rénales terminales). La girolle publiée a donc reçu cette confusion en tête de sa fiche, dans la même PR.

## Ajoutées (17)

| Espèce | Groupe | Ce qu'elle apporte | Réserve principale |
| --- | --- | --- | --- |
| Lactaire sanguin, *Lactarius sanguifluus* | Lactaires | Pins sur calcaire du Sud-Est ; couvre aussi *L. semisanguifluus* et *L. vinosus* | Saison coupée au 31 déc. sur le littoral |
| Lactaire saumon, *Lactarius salmonicolor* | Lactaires | Sapinières de montagne | Sapin et épicéa confondus dans BD Forêt |
| Lactaire de l'épicéa, *Lactarius deterrimus* | Lactaires | Pessières, y compris plantations de plaine | Même carte ou presque que le saumon |
| Lactaire à lait abondant, *Lactifluus volemus* | Lactaires | Le seul lactaire d'été, juillet à septembre | Nom européen à trois espèces ; en recul en Europe |
| Girolle améthyste, *Cantharellus amethysteus* | Girolles | Hêtraies-sapinières de montagne, été | Occurrences GBIF de fiabilité moyenne |
| Craterelle cendrée, *Craterellus cinereus* | Trompettes de la mort | Cueillie avec la trompette | Nom accepté discuté (GBIF : *Cantharellus cinereus*) |
| Chanterelle en tube, *Craterellus tubaeformis* | Chanterelles (nouveau) | Octobre à décembre, conifères acides | Sosie mortel : cortinaire très joli |
| Chanterelle jaune, *Craterellus lutescens* | Chanterelles (nouveau) | Conifères humides, calcaires ou tourbeux | Micro-habitat mouillé invisible ; pinèdes sèches surestimées |
| Pied de mouton roux, *Hydnum rufescens* | Pieds de mouton | Complète *H. repandum* | Complexe de plusieurs espèces (Niskanen 2018) |
| Petit-gris, *Tricholoma terreum* | Grisets (nouveau) | Le griset du Ventoux et des pinèdes calcaires | Sosie mortel (phalloïde) ; comestibilité contestée |
| Tricholome prétentieux, *Tricholoma portentosum* | Grisets (nouveau) | Dernier champignon de l'année, pinèdes acides | Sosies mortels : phalloïde, tricholome équestre |
| Pied bleu, *Lepista nuda* | Pieds bleus (nouveau) | Octobre à décembre, toute litière | Jardins, haies et prés hors carte |
| Bolet bai, *Imleria badia* | Bolets bais (nouveau) | Très commun, conifères et feuillus acides | Fort accumulateur de césium 137 |
| Nonnette voilée, *Suillus luteus* | Nonnettes (nouveau) | Jeunes pinèdes | Troubles digestifs et allergies rapportés |
| Bolet granulé, *Suillus granulatus* | Nonnettes (nouveau) | Pins, poussée de printemps en plus | Idem |
| Russule charbonnière, *Russula cyanoxantha* | Russules (nouveau) | Feuillus, juin à octobre | Sosie mortel : phalloïde |
| Russule verdoyante, palomet, *Russula virescens* | Russules (nouveau) | Chênaies claires, été | Sosie mortel : phalloïde ; peu de données dans le Sud-Ouest |

### Le griset du Ventoux

Au Ventoux, le griset est le petit-gris, *Tricholoma terreum*, ou son complexe (*T. scalpturatum*, *T. myomyces*). Dans le massif, GBIF compte six relevés de *T. terreum* et deux de *T. scalpturatum*, faits par l'ONF à Bédoin, Brantes et Saint-Léger-du-Ventoux entre le 19 et le 29 octobre, en 2014 et 2015. Une encyclopédie locale donne au contraire le griset du Ventoux pour *T. portentosum*. Le groupe « Grisets » réunit les deux espèces et couvre le griset dans les deux lectures.

Le massif ressort sans paramètre propre. Les pins noirs des reboisements de restauration des terrains en montagne sont à 1 dans le fichier, le calcaire est dans l'optimum de pH et l'altitude dans l'optimum. Avec le décalage d'altitude, le pic à 1 100 m va du 22 septembre au 13 novembre, ce que confirment les relevés de fin octobre. Aucun arrêté propre au Ventoux n'a été trouvé ; le droit commun s'applique.

La comestibilité du petit-gris est contestée. Yin et al. (Chem. Eur. J., 2014) ont isolé d'une récolte française des saponaceolides qui provoquent une rhabdomyolyse chez la souris. Davoli et al. (2016) et Clericuzio et al. (Molecules, 2024) ne les retrouvent pas et jugent l'espèce consommable. Elle figure sur la liste des champignons commercialisables de l'ANSES et de la DGCCRF de 2017, sous le nom « tricholome gris ». Elle accumule aussi le césium 137 (CRIIRAD). La fiche ne dit jamais « comestible » ; la décision de la publier revient à Adrien.

## Prêtes, en attente d'une décision (3)

Les fichiers complets sont dans `docs/brouillons/`, avec leur bloc d'illustration. Les déplacer dans `species/` suffit à les ajouter.

| Espèce | Pourquoi elle attend | Ce qu'il faudrait trancher |
| --- | --- | --- |
| Hygrophore de mars, *Hygrophorus marzuolus* | Seule espèce de février à mai possible. Le modèle ne voit pas la fonte des neiges, son vrai déclencheur. L'espèce est en déclin : protégée en Allemagne, vulnérable au niveau mondial selon une évaluation UICN non vérifiée. | Publier une espèce vulnérable ; ajouter l'épaisseur de neige d'Open-Meteo au modèle d'abord |
| Sparassis crépu, *Sparassis crispa* | Parasite des racines de pins : l'arbre infecté est invisible. La carte dirait « toute pinède », donc « quand » mais pas « où ». | L'accepter comme espèce de « mes coins », un arbre connu suivi par la météo |
| Pholiote ridée, *Cortinarius caperatus* | Genre des cortinaires, déconseillé aux débutants. En déclin aux Pays-Bas, en Allemagne et au Royaume-Uni. Accumule césium, mercure et cadmium. | Publier un cortinaire ; statut en France à vérifier |

## Écartées (25)

| Espèce | Raison | Ce qui la rendrait ajoutable |
| --- | --- | --- |
| Oronge, *Amanita caesarea* | Œuf presque identique à celui de la phalloïde ; confusions annuelles avec l'amanite tue-mouches délavée. Non protégée en France, quasi menacée en Alsace et en Lorraine. Hôtes lisibles. | Une décision d'Adrien sur les jumeaux mortels |
| Agaric des bois, *Agaricus sylvicola* | Ressemble à une jeune phalloïde blanche | Idem |
| Coulemelle, *Macrolepiota procera* | Prairies, lisières et clairières, en bonne partie hors forêt ; petites lépiotes mortelles | Un facteur de lisière (codé le 9 nov. 2026, test d'entrée sur le Vaucluse : `docs/LISIERE-vaucluse-2026-11-09.md`) et l'ouverture aux prés ; décision sur les lépiotes |
| Morilles, *Morchella* spp. | Frênes et ormes noyés dans « autre feuillu », ripisylves de moins de 2 ha sans essence, brûlis, vergers et jardins hors forêt | Un modèle à part, BD Forêt V3 pour le frêne |
| Mousseron de la Saint-Georges, *Calocybe gambosa* | Prés, haies, vergers | Ouvrir la carte aux prés (structurant) |
| Rosé des prés, *Agaricus campestris* | Prairies et pâtures | Idem |
| Faux mousseron, *Marasmius oreades* | Pelouses, prairies ; sosie très toxique | Idem |
| Coprin chevelu, *Coprinus comatus* | Pelouses, bords de chemins, sols azotés | Idem |
| Pleurote du panicaut, *Pleurotus eryngii* | Racines de panicaut en terrain dégagé | Idem |
| Pleurote en huître, *Pleurotus ostreatus* | Lignicole sur bois mort ou affaibli ; automne-hiver à cheval sur le 1er janvier | Saisons à cheval sur l'année ; une donnée de bois mort |
| Collybie à pied velouté, *Flammulina velutipes* | Bois mort, octobre à février | Idem |
| Langue de bœuf, *Fistulina hepatica* | Parasite du bas des troncs de chênes et châtaigniers : l'arbre porteur est invisible | Comme le sparassis, un usage « mes coins » |
| Bolet rude, *Leccinum scabrum* | Bouleau, noyé dans « autre feuillu » ; intoxications même cuit (Amérique du Nord) | BD Forêt V3 si le bouleau y est séparé |
| Bolet orangé, *Leccinum aurantiacum* et voisins | Tremble et bouleau surtout, parfois chêne | Idem |
| Tête de moine, *Infundibulicybe geotropa* | Lisières, clairières et prés qui bordent les bois | Un facteur de lisière |
| Lyophylle en touffes, *Lyophyllum decastes* | Lisières, bords de chemins | Idem |
| Clitocybe nébuleux, *Clitocybe nebularis* | Déclaré non comestible (VAPKO 2017, 2023) ; déconseillé en France | Rien : à ne pas ajouter |
| Tricholome équestre, *Tricholoma equestre* | Vente interdite (décret n° 2005-1184 du 19 sept. 2005) ; rhabdomyolyses mortelles (Bedry et al., NEJM 2001) | Rien : à ne pas ajouter |
| Gyromitre, *Gyromitra esculenta* | Toxique mortelle ; vente interdite (décret n° 91-1039 du 7 oct. 1991) | Rien : à ne pas ajouter |
| Hygrophore escargot, *Hygrophorus latitabundus* | 87 occurrences GBIF en France, 22 de plus sous *H. limacinus* | Plus de données, ou un contrôle par les retours terrain |
| Bolet de Bellini, *Suillus bellinii* | 79 occurrences GBIF | Idem |
| Bolet à pied rouge, *Neoboletus luridiformis* | 71 occurrences sous ce nom, taxonomie éclatée dans GBIF ; toxique cru | Regrouper les noms dans GBIF |
| Truffes, *Tuber* spp. | Hypogées, cavées au chien ; récolte liée à la propriété (code forestier, art. L.163-11) ; truffe noire à cheval sur le 1er janvier | Hors du propos de Champis |
| Hygrophore russule, *Hygrophorus russula* | 266 occurrences, intérêt culinaire faible | Une demande d'Adrien |
| *Tricholoma scalpturatum*, *T. myomyces* | Complexe du petit-gris, identifications mêlées | Couverts de fait par le groupe Grisets |

## Limites communes aux dix-sept fichiers

- **Sources.** Le réseau de la session n'ouvrait que Wikipédia, Wikimedia Commons et GBIF. Les articles scientifiques ne sont connus que par leur résumé, et chaque référence le dit. Le bloc météo de la plupart des espèces est transposé de l'espèce existante la plus proche, en confiance faible. À relire quand les sources primaires seront accessibles : ANSES, Légifrance, INPN (liste rouge nationale 2024 des bolets, lactaires et tricholomes).
- **pH.** Les plages sont la littérature élargie ; les quantiles SoilGrids aux occurrences restent à calculer par `champis-pipeline check`.
- **Sapin et épicéa.** BD Forêt V2 ne les sépare pas : le lactaire saumon et le lactaire de l'épicéa donnent presque la même carte.
- **Tuiles.** Dix-sept rendus T France, et un G en deux parties pour les lactaires, une première en production. Elles peuvent être produites et publiées avant les planches : les clients ne lisent que les espèces du catalogue.

## Décisions demandées à Adrien

- [x] Publier des fiches qui nomment un sosie mortel : tranché le 9 nov. 2026, oui, le sosie en tête de fiche (grisets, russules, chanterelles en tube et jaune, girolle).
- [x] Publier le petit-gris malgré la controverse sur sa comestibilité : tranché le 9 nov. 2026, oui, sans le mot « comestible ».
- [x] Noms des groupes : tranché le 9 nov. 2026, « Grisets » (le nom provençal, celui du Ventoux) plutôt que « Petits-gris » ; « Chanterelles » pour les craterelles en tube et jaune.
- [x] Les trois brouillons en attente : tranché le 9 nov. 2026, aucun pour l'instant.
- [x] Les saisons à cheval sur le 1er janvier : tranché le 9 nov. 2026, schéma étendu le jour même ; pied bleu et petit-gris jusqu'au 31 janvier, lactaire sanguin et bolet bai jusqu'au 15 janvier.
- [ ] La règle « hors forêt → T = 0 » face aux espèces de lisière et de pré.
