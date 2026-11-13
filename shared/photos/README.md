# Photos des fiches d'espèces

Une photo par espèce, `shared/photos/<id>.jpg` : la copie, telle que servie par Wikimedia Commons
en 1 280 px de large et sans retouche, de la photo choisie dans le bloc `about.photo` du fichier
espèce. Le site et l'app l'affichent depuis le référentiel, avec son crédit (auteur, licence, lien
vers la page Commons), au lieu de la charger chez Wikimedia : ouvrir une fiche n'envoie plus
l'adresse du lecteur à un tiers (décision d'Adrien du 13 nov. 2026, audit avant ouverture du code).

`about.photo` reste la source : `url` (l'image d'origine), `page` (la page Commons), `author`,
`license`. Changer de photo, c'est changer ce bloc **et** remplacer le fichier ici, dans la même
PR. `scripts/check_shared.py` refuse un fichier qui ne porte pas l'id d'une espèce et signale une
espèce sans photo.

## Crédits et licences

Ces photos ne sont **pas** sous la licence du référentiel : chacune garde celle de son auteur.
Les réutiliser demande de citer l'auteur et la licence ; les licences CC BY-SA imposent en plus de
partager une version modifiée sous la même licence.

| Fichier | Espèce | Auteur, page Commons | Licence |
| --- | --- | --- | --- |
| `boletus_aereus.jpg` | Cèpe bronzé | [Roberto Petruzzo](https://commons.wikimedia.org/wiki/File:Boletus_aereus_IT.JPG) | Public domain |
| `boletus_edulis.jpg` | Cèpe de Bordeaux | [Holger Krisp](https://commons.wikimedia.org/wiki/File:(Gemeine_Steinpilz)_Boletus_edulis.jpg) | CC BY 3.0 |
| `boletus_pinophilus.jpg` | Cèpe des pins | [Mariia Goncharskaia](https://commons.wikimedia.org/wiki/File:Boletus_pinophilus_15.jpg) | CC BY-SA 4.0 |
| `boletus_reticulatus.jpg` | Cèpe d'été (cèpe réticulé) | [Toffel](https://commons.wikimedia.org/wiki/File:Boletus_reticulatus_(2).JPG) | CC BY-SA 3.0 |
| `cantharellus_alborufescens.jpg` | Girolle blanchissante (girolle des chênes verts) | [Guillaume Eyssartier](https://commons.wikimedia.org/wiki/File:Cantharellus_alborufescens_confirmed_collection.jpg) | CC BY 4.0 |
| `cantharellus_amethysteus.jpg` | Girolle améthyste | [Jerzy Opioła](https://commons.wikimedia.org/wiki/File:Cantharellus_amethysteus_BW53_(8).jpg) | CC BY-SA 4.0 |
| `cantharellus_cibarius.jpg` | Girolle | [Heisenberg-pl](https://commons.wikimedia.org/wiki/File:Cantharellus_cibarius_20090717-01.jpg) | CC BY-SA 3.0 |
| `cantharellus_pallens.jpg` | Girolle pâle (girolle pruineuse) | [Allar Antson](https://commons.wikimedia.org/wiki/File:Cantharellus_pallens_FTLuJjc.jpg) | CC BY-SA 4.0 |
| `craterellus_cinereus.jpg` | Craterelle cendrée | [Jean.claude](https://commons.wikimedia.org/wiki/File:Chanterelle_cendr%C3%A9e_(Bouzonville_13).JPG) | CC BY-SA 3.0 |
| `craterellus_cornucopioides.jpg` | Trompette de la mort | [Jean-Pol Grandmont](https://commons.wikimedia.org/wiki/File:0_Craterellus_cornucopioides_-_Trompette_de_la_mort_(1).JPG) | CC BY 3.0 |
| `craterellus_lutescens.jpg` | Chanterelle jaune | [Andreas Kunze](https://commons.wikimedia.org/wiki/File:2007-11-10_Craterellus_lutescens.jpg) | CC BY-SA 3.0 |
| `craterellus_tubaeformis.jpg` | Chanterelle en tube | [Strobilomyces](https://commons.wikimedia.org/wiki/File:Craterellus_tubaeformis_110921w.JPG) | CC BY-SA 3.0 |
| `hydnum_repandum.jpg` | Pied de mouton | [Jean-Pol Grandmont](https://commons.wikimedia.org/wiki/File:Hydnum_repandum_JPG1.jpg) | CC BY 3.0 |
| `hydnum_rufescens.jpg` | Pied de mouton roux | [Weft](https://commons.wikimedia.org/wiki/File:Hydnum_rufescens_-_For%C3%AAt_de_Brotonne.JPG) | CC BY-SA 4.0 |
| `imleria_badia.jpg` | Bolet bai | [Achim Lammerts](https://commons.wikimedia.org/wiki/File:2025-11-04_D500-1630_Achim-Lammerts_Imleria-badia.jpg) | CC BY-SA 4.0 |
| `lactarius_deliciosus.jpg` | Lactaire délicieux | [furtwangl](https://commons.wikimedia.org/wiki/File:2009-09-28_Lactarius_deliciosus.jpg) | CC BY 2.0 |
| `lactarius_deterrimus.jpg` | Lactaire de l'épicéa | [Holger Krisp](https://commons.wikimedia.org/wiki/File:Lactarius-deterrimus-Fichten-Reizker.jpg) | CC BY 3.0 |
| `lactarius_salmonicolor.jpg` | Lactaire saumon | [Holger Krisp](https://commons.wikimedia.org/wiki/File:Lachs-Reizker_%28Lactarius_salmonicolor%29.JPG) | CC BY 3.0 |
| `lactarius_sanguifluus.jpg` | Lactaire sanguin | [Holger Krisp](https://commons.wikimedia.org/wiki/File:Weinroter_Kiefern-Reizker_Lactarius_sanguifluus.jpg) | CC BY 3.0 |
| `lactifluus_volemus.jpg` | Lactaire à lait abondant | [Jerzy Opioła](https://commons.wikimedia.org/wiki/File:Lactarius_volemus_a1_%281%29.JPG) | CC BY-SA 4.0 |
| `lepista_nuda.jpg` | Pied bleu | [George Chernilevsky](https://commons.wikimedia.org/wiki/File:Lepista_nuda_2022_G1.jpg) | CC BY-SA 4.0 |
| `russula_cyanoxantha.jpg` | Russule charbonnière (charbonnier) | [Holger Krisp](https://commons.wikimedia.org/wiki/File:Frauen-T%C3%A4ubling_Russula_cyanoxantha.jpg) | CC BY 3.0 |
| `russula_virescens.jpg` | Russule verdoyante (palomet) | [Paffka](https://commons.wikimedia.org/wiki/File:Russula_virescens3.JPG) | CC BY-SA 3.0 |
| `suillus_granulatus.jpg` | Bolet granulé | [Holger Krisp](https://commons.wikimedia.org/wiki/File:Suillus-granulatus.jpg) | CC BY 3.0 |
| `suillus_luteus.jpg` | Nonnette voilée | [Jerzy Opioła](https://commons.wikimedia.org/wiki/File:Suillus_luteus_G4.JPG) | CC BY-SA 3.0 |
| `tricholoma_portentosum.jpg` | Tricholome prétentieux | [Adrien BENOIT à la GUILLAUME](https://commons.wikimedia.org/wiki/File:Tricholoma_portentosum_%28Haute-Loire%2C_France%29.jpg) | CC BY-SA 4.0 |
| `tricholoma_terreum.jpg` | Petit-gris (tricholome terreux) | [Holger Krisp](https://commons.wikimedia.org/wiki/File:Erd-Ritterling_Tricholoma_terreum.jpg) | CC BY 3.0 |
