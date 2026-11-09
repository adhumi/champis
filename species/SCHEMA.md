# Schéma des fichiers espèces — version 1

Un fichier `species/<id>.json` par espèce. Le pipeline (potentiel terrain `T`) et l'API (indice météo `M`, fenêtre `Φ`) ne connaissent aucune espèce en dur : ils lisent ces fichiers. Toute plage numérique suit le gabarit trapézoïdal `min / opt_low / opt_high / max` : score 0 sous `min` et au-dessus de `max`, 1 entre `opt_low` et `opt_high`, linéaire entre les deux.

## En-tête

| Clé | Rôle |
| --- | --- |
| `id` | Identifiant = nom de fichier |
| `schema_version` | 1 |
| `group` | Groupe d'affichage (`cepes`, `girolles`). L'UI affiche un groupe ; son score est le **max** des espèces du groupe. Permet d'ajouter *B. aereus* ou *C. pallens* sans changer l'interface |
| `names` | Noms français et latin |
| `notes` | Texte libre |
| `references` | Dictionnaire `clé → citation courte` ; chaque bloc pointe vers ces clés via `refs` |

## `terrain` → potentiel `T` (pipeline, statique, raster 25 m)

| Clé | Donnée source | Calcul |
| --- | --- | --- |
| `hosts` | BD Forêt V2 via `mapping/bdforet_to_hosts.json` ; hors BD Forêt, CLC 2018 ; tout autre code (vignes, cultures, bâti, eau) → `herbacee` | Poids 0–1 par hôte du vocabulaire ; `default` pour une clé absente |
| `cover` | BD Forêt V2 (classe de couvert) | Poids 0–1 : `fermee`, `ouverte`, `sans_couvert`, `plantation`, `non_foret` |
| `ph` | SoilGrids pH H2O 0–5 cm (valeur /10) | Trapèze, **plancher 0,15** (jamais 0 : SoilGrids est lissé à 250 m et surestime le pH des humus forestiers) ; pH manquant → 0,5 |
| `altitude_m` | BD ALTI 25 m | Trapèze |
| `aspect` | Dérivé du MNT, 8 classes + `flat` (pente < 3°) | Poids 0–1 |
| `slope_deg` | Dérivé du MNT | Trapèze |
| `weights` | — | Poids de `cover`, `ph`, `altitude`, `aspect`, `slope` ; somme = 1 |

**`T = host × Σ poids × facteur`** : l'hôte est multiplicatif, pas additif — une cédraie ou une vigne ne peut pas ressortir « bonne » parce que le pH et l'exposition sont parfaits. Règle dure : `altitude` hors `[min, max]` → `T = 0`. Hors forêt (ni BD Forêt, ni CLC forestier) → `T = 0`.

À faire en phase 1 : recalibrer les trapèzes `ph` sur la distribution SoilGrids aux coordonnées des occurrences GBIF françaises (quantiles 1/10/90/99 %) ; les valeurs actuelles sont la littérature de terrain élargie de +0,6.

## `phenology` → fenêtre `Φ` (API)

| Clé | Calcul |
| --- | --- |
| `season.start/end` (`MM-DD`) | `Φ = 0` hors saison ; **`Φ = 0,25` dès `season.start`** (plancher : les pousses précoces existent) |
| `peak.start/end` | `Φ = 1` au pic |
| `ramp_days` | Rampe linéaire de 0,25 à 1 sur `ramp_days` avant le pic, et de 1 à 0,25 sur `ramp_days` après la fin du pic, bornée par la saison ; le plancher 0,25 tient jusqu'à `season.end` (pousses tardives) |
| `secondary_peak` (optionnel) | Fenêtre `start/end` avec `Φ = phi` (ex. poussée printanière de *B. pinophilus* à 0,6), fusionnée par max avec la fenêtre principale |
| `altitude_shift` | Décale le **début** de `start_days_per_100m` et la **fin** de `end_days_per_100m` par 100 m au-dessus de `reference_m`, chacun borné à `±max_days`. Positif = plus tard. Asymétrique : en montagne les girolles démarrent plus tard (+4 j/100 m) mais les automnales finissent plus tôt (−3 j/100 m) |

## `weather` → indice `M` (API, par cellule météo, Open-Meteo)

Séries : les 92 derniers jours et J+1 à J+7 viennent de l'**API prévision** (`past_days=92`, même modèle avant et après J, pas de discontinuité) ; seule la mémoire (90 j) peut venir de l'archive ERA5-Land. Variables : `temperature_2m_mean/min/max`, `rain_sum` (pas `precipitation_sum` : la neige n'est pas une pluie déclenchante), `snowfall_sum`, `et0_fao_evapotranspiration`, `soil_moisture_0_to_7cm_mean`, `soil_temperature_0_to_7cm_mean` (depuis le 9 nov. 2026), `elevation` de la cellule.

**Correction altitudinale** : les températures de la cellule sont corrigées pour le pixel par −0,6 °C/100 m × (altitude pixel − altitude cellule), par classes de 300 m. Sans cela le gel n'est jamais vu à 1 400 m et la chaleur l'est à tort.

`M = (Σ poids × facteur) × gel × bilan_hydrique × chaleur × mémoire`, puis persistance.

**Facteurs optionnels** (décision du 9 nov. 2026) : un facteur absent du fichier vaut poids 0, et le fichier qui ne l'emploie pas ne change pas, donc ni son empreinte ni ses tuiles. Un facteur n'entre dans le schéma que s'il relève l'AUC GBIF d'au moins une espèce sur un département de référence (`T`) ou s'appuie sur la littérature (`M`). Aujourd'hui : `soil_temp`.

| Clé | Donnée | Calcul |
| --- | --- | --- |
| `temp_mean` | `temperature_2m_mean`, moyenne sur `window_days`, corrigée | Trapèze sur `c` |
| `rain` | `rain_sum`, cumul sur `window_days` | Trapèze sur `mm` (`max` volontairement élevé : pas de seuil supérieur observé) |
| `trigger` | Événements = `≥ event_mm` de pluie cumulés sur `event_days` jours consécutifs, hors jours à `snowfall_sum > 0` | Pour **chaque** événement des `lag_days.max` derniers jours, trapèze sur le nombre de jours écoulés ; facteur = **max** sur les événements (une petite pluie récente n'efface pas la grosse pluie d'il y a 15 j) ; aucun événement → 0. La date d'un événement est le **dernier jour** de sa fenêtre de `event_days` jours |
| `soil_moisture_pct` | `soil_moisture_0_to_7cm_mean`, exprimé jour par jour en **percentile** de la climatologie de la cellule sur **l'année entière** (10 ans, toutes dates confondues, 11 quantiles, interpolation linéaire), puis moyenne des 7 derniers jours | Trapèze sur 0–1 ; les valeurs absolues ne sont pas comparables d'un sol à l'autre, le percentile mesure l'eau du sol relativement à la plage propre de la cellule. Décision du 7 nov. 2026 : plus de climatologie par mois civil, qui faisait une marche au changement de mois et classait tout l'hiver (sols toujours proches de la saturation) comme « sec » au moindre écart |
| `frost` | `temperature_2m_min` corrigée | **Rampe** (décision du 4 nov. 2026), pas une marche. Pour chaque nuit des `window_days` derniers jours, sévérité `s = 1 − trapèze(tmin, min = tmin_c, opt_low = tmin_c + ramp_c, opt_high = +∞, max = +∞)` : 1 à `tmin_c` et en dessous, 0 dès `tmin_c + ramp_c`, linéaire entre. Cumul `S = Σ s` sur la fenêtre ; **facteur = 1 − (1 − factor) × min(1, S / nights)**. `nights` nuits pleines donnent × `factor` (comme l'ancienne marche) ; une nuit à mi-rampe donne `1 − (1 − factor) × 0,5 / nights`. Continu en température et en nombre de nuits : deux cellules météo voisines ne basculent plus de « bon » à « très faible » pour un dixième de degré. `ramp_c` en °C, > 0 |
| `water_balance` | `Σ (rain_sum − et0)` sur `window_days` | `< moderate_mm` → × `moderate_factor` ; `< severe_mm` → × `severe_factor`. Remplace un simple compteur de jours secs, qui pénalisait à tort la période de poussée (10–20 j de beau temps après la pluie déclenchante) |
| `heat` | `temperature_2m_max` corrigée | Si `≥ days` jours `≥ tmax_c` dans `window_days` → × `factor` |
| `memory` | Cumul de `rain_sum` sur les `window_days` glissants **avant la fenêtre `rain`** (soit J−117 à J−28 inclus pour 90/28) | × `(floor + (1 − floor) × trapèze)` : module entre `floor` et 1, jamais annule |
| `persistence` | — | `M_eff(J) = max(M(J), max_k M(J−k) × (1 − k/days))` pour `1 ≤ k ≤ days` ; gel (facteur du jour, en rampe) et bilan hydrique s'appliquent **après** (les sporophores existants gèlent ou se dessèchent) |
| `soil_temp` (**optionnel**) | `soil_temperature_0_to_7cm_mean`, moyenne sur `window_days`, corrigée à l'altitude du pixel comme l'air (−0,6 °C/100 m, même classe de 300 m : sur 7 à 14 jours le sol suit l'air moyen, approximation assumée) | Trapèze sur `c` ; poids `weights.soil_temp`. Absent → poids 0, rien ne change pour l'espèce. Spec › Scoring › Facteurs de sol et de paysage (9 nov. 2026) : le sol lisse les écarts jour-nuit et retarde le signal comme le mycélium. L'historique n'a la variable que depuis sa mise en service : une espèce ne l'active qu'après `window_days + persistence.days` jours de collecte, sinon l'API refuse la série |
| `weights` | — | Poids de `temp`, `rain`, `trigger`, `soil_moisture` et, s'il est présent, `soil_temp` ; somme = 1 |

Pour J+1 à J+7, mêmes formules sur les séries prévues. La série doit couvrir au moins `memory.window_days + rain.window_days + persistence.days` jours avant J (≈ 150 j) : une fenêtre tronquée est une erreur, jamais une approximation silencieuse. Les arrondis de jours utilisent « 0,5 → vers le haut » (comme JS et Swift), pas l'arrondi au pair de Python.

Pistes non implémentées (à évaluer en phase 5 sur les retours terrain) : choc thermique (chute de T moyenne ≥ 4 °C dans la semaine suivant la pluie, bonus ×1,2), température du sol au lieu de l'air, trigger en multiplicateur pour les bolets.

## `about` → fiche en mots (app et site, refonte UX lot 4)

Ce que l'onglet Comprendre et le site disent de l'espèce. Aucune aide à l'identification : la consigne « faites contrôler votre récolte par un pharmacien ou une association mycologique » précède toutes les fiches (`shared/texts/especes.md`).

| Clé | Rôle |
| --- | --- |
| `summary` | Deux ou trois phrases : allure générale, ce qui la distingue |
| `habitat` | Où elle pousse, en mots (hôtes, sols, altitude, région) |
| `season` | Quand, en mots (mois, pic, décalage en montagne) |
| `confusions` | Liste ; chaque entrée : `name`, `latin`, `risk` (ce qu'on risque), `tell` (comment la distinguer), `refs` (≥ 1 clé de `references`) |
| `photo` | `null` tant qu'elle n'est pas choisie, sinon `url` (image), `page` (page Wikimedia Commons), `author`, `license` parmi les licences libres acceptées (CC0, domaine public, CC BY, CC BY-SA) ; le crédit s'affiche sous la photo |
| *(illustration)* | Pas de clé : chaque espèce a sa planche `shared/illustrations/<id>.jpg`, aquarelle générée d'après `shared/illustrations/PROMPTS.md` (même style pour toutes), pour les listes et le sélecteur d'espèce ; la photo reste celle de la fiche |
| `refs` | Sources de la fiche |
| `references` | Dictionnaire des sources propres à la fiche (clé → citation courte), comme `references` en tête de fichier |

Le bloc est **autoporteur et exclu de l'empreinte d'espèce** (`species_hash`, calculée sur le fichier sans `about`) : relire une fiche ne renomme aucune tuile et ne régénère rien.

Première version rédigée par Claude, relue par Adrien (décision du 1er nov. 2026).

## Score final

`S(pixel, espèce, J) = T(pixel) × M_eff(cellule, J, altitude du pixel) × Φ(J, altitude du pixel)`

Seuils d'affichage (voir la spec) : ≥ 0,75 excellent · 0,55 bon · 0,35 moyen · 0,15 faible · < 0,15 très faible.

Couleur d'un pixel (échelle linéaire, décision du 6 nov. 2026, `shared/palette.json` › `scale`) : un seul violet `scale.hex`, dont l'alpha porte le score : `alpha = floor(255 × (alpha_min + (alpha_max − alpha_min) × S) + 0,5)`, `S` borné à [0, 1], même arrondi dans tous les langages. Les seuils ne servent qu'aux mots (fiche, coins, notifications, graduations de la légende) ; le `hex` de chaque seuil est le violet au milieu de la classe composé sur blanc, pour les pastilles.

## Validation

`python3 species/validate.py` vérifie la structure, les sommes de poids, l'ordre des trapèzes, le vocabulaire des hôtes, la couverture des 32 codes TFV, la présence des références citées, les paramètres de gel (`ramp_c` > 0, `nights` ≥ 1) et le bloc `about` (une référence par confusion, photo libre créditée ou `null`).
