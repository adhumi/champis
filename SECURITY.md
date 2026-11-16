# Signaler une faille de sécurité

## Comment

Écrire à **hello@champis.app**. Ne pas ouvrir d'issue publique ni de PR qui décrit la faille :
tant qu'elle n'est pas corrigée, le détail doit rester entre vous et l'auteur.

Dans le message, autant que possible :

- le dépôt ou le service concerné (voir ci-dessous) ;
- ce que la faille permet, et à qui ;
- les étapes pour la reproduire, ou une preuve de concept ;
- la version, le commit ou l'adresse où vous l'avez constatée.

## Ce que couvre cette adresse

Ce dépôt ne contient que des données (fichiers d'espèces, palette, textes, vecteurs, images) et
deux scripts de contrôle : il y a peu à y attaquer. Les failles du site, de l'API ou de l'app se
signalent à la même adresse, en nommant le dépôt concerné :

| Où | Dépôt |
| --- | --- |
| API et pipeline, `api.champis.app` | `adhumi/champis-api` |
| Site, `champis.app` | `adhumi/champis-web` |
| App iOS, iPadOS et macOS | `adhumi/champis-ios` |
| Données et scripts du référentiel | `adhumi/champis` (ce dépôt) |

Une erreur dans une donnée (une plage, une source, une confusion mal décrite dans une fiche) n'est
pas une faille : elle se signale par une issue, voir `CONTRIBUTING.md`.

## Ce à quoi vous attendre

Champis est un projet personnel, tenu par une seule personne sur son temps libre.

- Accusé de réception sous quelques jours, pas sous quelques heures.
- Un correctif dès que possible selon la gravité, puis un mot pour vous dire qu'il est en ligne.
  Votre nom est cité si vous le souhaitez.
- Pas de prime : le projet est gratuit et financé par des dons.

## En cherchant

- Ne testez pas la production en charge : pas de déni de service, pas de balayage massif. Le
  service est petit et sert tout le monde.
- N'accédez pas aux données d'autres personnes (coins, observations) au-delà de ce qu'il faut pour
  montrer le problème, et ne les conservez pas.
- Laissez à l'auteur un délai raisonnable pour corriger avant d'en parler publiquement.
