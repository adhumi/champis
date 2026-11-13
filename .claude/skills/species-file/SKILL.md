---
name: species-file
description: Ajouter ou modifier un fichier espèce species/<id>.json (nouvelle espèce, changement de poids ou de plage). Impose le gabarit, une référence par règle, la validation et la mise à jour de la spec.
---

# Ajouter ou modifier une espèce

Une espèce = un fichier `species/<id>.json`, `id` = nom de fichier en `snake_case` latin (`boletus_edulis`). Le schéma complet est dans `species/SCHEMA.md` ; lis-le avant d'écrire.

## Procédure

1. **Partir d'un fichier existant** du même groupe (`cp species/boletus_edulis.json species/<id>.json`), jamais d'une page blanche : la structure, la liste complète des 30 hôtes et les clés météo doivent être identiques d'une espèce à l'autre.
2. **Changer `id`, `names`, `group`, `notes`.** `group.id` ∈ {`cepes`, `girolles`} ou un nouveau groupe à déclarer dans la spec ; une espèce « bonus » d'un groupe existant ne change pas l'interface.
3. **Renseigner chaque bloc avec une source.** Chaque clé de `terrain.refs` et `weather.refs` pointe vers une clé de `references`, et chaque entrée de `references` est une citation courte : auteur, année, revue, ce qu'elle établit. Une valeur sans source est marquée dans `notes` comme « à valider » et sa référence est `terrain_fr` ou `populaire_*` avec mention « confiance faible ».
4. **Garder le gabarit trapézoïdal** `min ≤ opt_low ≤ opt_high ≤ max` partout ; ne jamais inventer un autre format de plage.
5. **Tous les hôtes du vocabulaire** (`mapping/bdforet_to_hosts.json` → `hosts`) doivent avoir un poids explicite, plus `default`. `robinier`, `peupleraie`, `herbacee` restent à 0 sauf raison documentée.
6. **Poids** : `terrain.weights` (cover, ph, altitude, aspect, slope) et `weather.weights` (temp, rain, trigger, soil_moisture, plus `soil_temp` si le bloc optionnel `weather.soil_temp` est présent ; `terrain.weights` gagne `edge` avec le bloc optionnel `terrain.edge_m`, distance à la lisière, et `water` avec `terrain.water_m`, distance à l'eau) somment à 1. Une espèce hors forêt (morilles) nomme ses hôtes BD TOPO dans `terrain.hosts_topo` (vocabulaire `topo_hosts` du mapping, sans `default`) ; une espèce forestière n'a pas ce bloc. Un facteur optionnel absent vaut 0 : ne l'ajoute à une espèce qu'avec une source, et sache que son empreinte change (tuiles T à rerendre).
7. **Écrire la fiche `about`** (lot 4) : `summary`, `habitat`, `season` en mots, au moins une confusion dangereuse avec `name`, `latin`, `risk`, `tell` et une référence, `photo` à `null` tant qu'une image Wikimedia Commons sous licence libre n'est pas choisie (alors `url`, `page`, `author`, `license`) ; ses sources vont dans `about.references`, pas en tête de fichier : le bloc est exclu de l'empreinte, relire une fiche ne régénère rien. Jamais d'aide à l'identification, jamais de « comestible » sans la consigne du pharmacien (qui est dans `shared/texts/especes.md`, pas dans la fiche). Adrien relit.
8. **Valider** : `make check` (ou `python3 species/validate.py`) doit afficher `ok`. Ne pas contourner une erreur en modifiant le validateur.
9. **Mettre à jour la spec** : onglet « Références phase 0 » du doc (ou la phase courante) — une ligne par règle structurante, valeur, confiance, source ; et la liste des espèces dans la section « Modèle d'espèce ». Voir skill `spec-sync`.
10. **Régénérer les vecteurs de parité** : l'empreinte des espèces change. Depuis champis-api, `uv run champis-vectors` écrit dans son sous-module `champis/shared/vectors/` ; ces fichiers se committent ici, dans la même PR (skill `scoring-parity`).
11. **Regénérer `T`** pour l'espèce si `terrain` a changé (champis-api, skill `geo-pipeline`) ; `M` et `Φ` sont lus à chaud par l'API, rien à régénérer une fois le sous-module avancé (`make referential` dans champis-api).

## Ordres de grandeur attendus (pour relire un fichier)

| Bloc | Cèpes | Girolles |
| --- | --- | --- |
| temp_mean (20–21 j) | opt 10–16 °C (edulis), +4–5 °C pour aereus/reticulatus | opt 11–18 °C |
| rain (28 j) | opt 60–150 mm, max ouvert (≥ 500) | idem |
| trigger lag | opt 10–20 j (edulis), 7–12 j (aereus) | opt 14–28 j |
| persistence | 10–12 j | 30–35 j |
| ph (SoilGrids, élargi) | 4,0–6,5 acidophiles, jusqu'à 6,8–7,5 pour aereus | 4,2–6,2 (cibarius), 5,5–7,5 (pallens), 6,8–8,2 (alborufescens) |

Une valeur loin de ces plages n'est pas forcément fausse, mais elle doit être justifiée dans `notes`.

## Ce qu'on ne fait pas

- Pas de paramètre spécifique dans le code pour contourner le schéma : si le schéma ne permet pas d'exprimer une règle, on étend le schéma (version, SCHEMA.md, validateur, scoring), pas le fichier.
- Pas de valeur recopiée de carte-champignon.fr ou d'un site commercial : littérature scientifique, guides de terrain, GBIF.
- Pas de suppression d'une référence encore citée.
