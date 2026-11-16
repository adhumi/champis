# Contribuer au référentiel

Champis est un projet personnel, tenu par une seule personne sur son temps libre. Les propositions
sont bienvenues ; elles sont relues quand l'auteur le peut, parfois après plusieurs semaines.

**Avertissement.** Rien dans ce dépôt ne dit qu'un champignon est comestible, et rien n'aide à
l'identifier. Les fiches ne donnent ni l'un ni l'autre, et une contribution ne doit pas l'ajouter :
une récolte se fait contrôler par un pharmacien ou une association mycologique.

## Ce qu'on peut proposer ici

- **Une espèce** : un nouveau fichier `species/<id>.json`.
- **Une correction de plage ou de poids** d'une espèce existante, avec la référence publiée qui la
  justifie.
- **Un texte du Guide** (`shared/texts/`) : une erreur, une formulation, une source manquante.
- **Une photo de fiche**, libre et créditée (`shared/photos/`).
- Une erreur dans la table BD Forêt (`mapping/`), dans `species/SCHEMA.md` ou dans les scripts de
  contrôle.

Le site, l'API et l'app ont leurs dépôts (`adhumi/champis-web`, `adhumi/champis-api`,
`adhumi/champis-ios`). Une faille de sécurité ne passe pas par une issue : voir `SECURITY.md`.

## Les règles du modèle

- **Une source par règle.** Chaque valeur d'un fichier espèce renvoie à une entrée de
  `references` : auteur, année, revue ou ouvrage, ce qu'elle établit. Littérature scientifique,
  guides de terrain, GBIF ; jamais une valeur recopiée d'un site commercial. Une valeur sans source
  solide se dit « confiance faible » dans `notes`.
- **Le gabarit des fichiers espèces** est décrit dans `species/SCHEMA.md` ; la marche à suivre,
  pas à pas, dans `.claude/skills/species-file/SKILL.md` (lisible sans outil particulier). En
  bref : partir d'un fichier existant du même groupe, garder le trapèze
  `min ≤ opt_low ≤ opt_high ≤ max`, donner un poids à chaque hôte, des poids qui somment à 1.
- **On ne contourne pas le validateur.** Si le schéma ne permet pas d'exprimer une règle, c'est le
  schéma qu'il faut faire évoluer : ouvrir une issue.
- **Photos** : une photo de Wikimedia Commons sous CC0, domaine public, CC BY ou CC BY-SA, copiée
  sans retouche dans `shared/photos/<id>.jpg`, avec le bloc `about.photo` du fichier espèce et la
  ligne de `shared/photos/README.md` dans la même PR.
- **Aquarelles** (`shared/illustrations/`) : elles sont produites par l'auteur dans un style
  commun ; elles ne se proposent pas par PR.

## Vérifier

```bash
make check
```

C'est exactement la CI : `species/validate.py` puis `scripts/check_shared.py`. Python 3.12,
bibliothèque standard, sans réseau, rien à installer.

## Les vecteurs de parité

Les fichiers de `shared/vectors/` ne se modifient jamais à la main. Ils sont régénérés par
`adhumi/champis-api` (`uv run champis-vectors`), et ils changent dès qu'un fichier espèce change :
ils doivent donc être mis à jour dans la même PR que l'espèce.

Si vous n'avez pas champis-api sous la main, ouvrez la PR sans les vecteurs et dites-le dans sa
description : l'auteur les régénérera sur votre branche avant la fusion. `make check` passe sans
eux ; c'est la CI de champis-api qui vérifie qu'ils sont à jour.

## Une branche, une PR

- Une branche par sujet, une PR, la CI verte, puis la fusion par l'auteur. Rien n'est poussé sur
  `main` directement, même une ligne de documentation.
- Dans la description : ce qui change, pourquoi, et la source.
- Une modification fusionnée ici n'apparaît sur le site et dans l'app qu'une fois reprise par les
  autres dépôts ; pour une espèce, il faut aussi que ses tuiles soient recalculées. Cela peut
  prendre du temps.

## Les décisions structurantes

Une formule ou un facteur du modèle, le schéma des fichiers, un format partagé entre les dépôts,
un nouveau groupe d'espèces, tout ce qui touche la vie privée : cela se discute d'abord dans une
issue. La spec du projet, tenue par l'auteur, fait foi (une copie expurgée est versionnée ici, dans
`docs/spec/`), et une PR qui la contredit n'est pas fusionnée, même si elle est meilleure : la
spec change d'abord.

## Licence des contributions

En proposant une contribution, vous acceptez qu'elle soit publiée sous la licence du dépôt :

- données et textes (fichiers d'espèces, table BD Forêt, textes du Guide, documents) :
  CC BY 4.0 (`LICENSE-DATA.md`) ;
- code (`species/validate.py`, `scripts/`) : MIT (`LICENSE`) ;
- photos : la licence libre de leur auteur, créditée (`shared/photos/README.md`). Ne proposez
  qu'une photo dont la licence permet cette copie.
