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
6. **Poids** : `terrain.weights` (cover, ph, altitude, aspect, slope) et `weather.weights` (temp, rain, trigger, soil_moisture) somment à 1.
7. **Valider** : `python3 species/validate.py` doit afficher `OK`. Ne pas contourner une erreur en modifiant le validateur.
8. **Mettre à jour la spec** : onglet « Références phase 0 » du doc (ou la phase courante) — une ligne par règle structurante, valeur, confiance, source ; et la liste des espèces dans la section « Modèle d'espèce ». Voir skill `spec-sync`.
9. **Regénérer `T`** pour l'espèce si `terrain` a changé (skill `geo-pipeline`) ; `M` et `Φ` sont lus à chaud par l'API, rien à régénérer.

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
