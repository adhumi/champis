# Champis — Audit UX, UI, produit et marketing

6 nov. 2026 · Adrien Humilière

Copie figée, au 6 nov. 2026, du doc Claude [« Champis — Audit UX, UI, produit et marketing »](https://claude.ai/artifact/V8dWjVKE6ZkmLrqEvdyXBS), suivie en annexe de la section « Produit » de la spec avec les décisions prises le même jour. Pour toute décision, c'est la spec qui fait foi : [Spec — Champis](https://claude.ai/artifact/54H9wdXiTTFcnoP6DAW81C), section Produit de l'onglet principal.

> **Mise à jour du 6 nov., après les réponses d'Adrien.** Échelle visée : des dizaines à quelques centaines d'utilisateurs, gratuit, 2 à 10 heures par semaine, mesure minimale, espèces ajoutées une à une, rien encore partagé avec les proches. Le lancement public, la presse et le référencement décrits plus bas ne s'appliquent donc plus tels quels. Adrien a ensuite tranché les quatorze points ouverts sur la PR monorepo #87 (App Store public, Android natif à prévoir, noindex jusqu'à la publication des apps, bandeau des jours retiré de la carte, code open source, soutien facultatif via RevenueCat…). Décisions, points encore ouverts et plan révisé : section Produit de la spec (copie en [annexe](#annexe--section-produit-de-la-spec-copie-du-6-nov-2026)). Les défauts relevés ici restent valables.

## En bref

Le moteur de Champis est rare (25 m sur toute la France, météo par classe d'altitude, sources ouvertes citées, coins privés), mais le produit ne le vend pas encore. On arrive sur une carte orange et rouge du Doubs, sans savoir où l'on est, ce que vaut ce week-end, ni pourquoi croire la couleur. Le site n'a pas de page d'accueil, l'app n'existe que sur iPhone, et Champis n'a rien à offrir de décembre à juillet.

La refonte du 1er novembre a bien réglé la structure (trois onglets, des mots avant les chiffres, deux tapes en forêt). Cet audit relève ce qu'elle a laissé passer, ce que la mise en œuvre a dévié, et ce qu'il faut pour une ouverture publique.

Cinq priorités, dans l'ordre :

1. **Corriger ce qui est faux** : l'accueil de l'app se ferme au premier « Suivant » et saute l'avertissement légal ; « Rien n'est collecté » et « identifiant anonyme » contredisent ce que l'app envoie ; le bandeau des jours dit « Moyen » quand la carte est orange ; les Lactaires sont dans le Guide mais pas sur la carte.
2. **Rendre la carte lisible pour tous** : palette illisible pour les daltoniens (Excellent et Très faible quasi identiques en protanopie), rouge dominant, jours sans numéro.
3. **Faire de la carte une réponse** : « près de moi, ce week-end, et pourquoi » ; géolocalisation et recherche de commune sur le site, phrases qui disent « trop tôt » ou « trop tard », raisons sur la fiche d'un coin.
4. **Préparer l'ouverture** : page d'accueil, pages légales (mentions, confidentialité complète), mesure d'audience respectueuse, dons en ligne, décision Android, couche des forêts publiques.
5. **Viser le début de saison 2027** pour le lancement public (fin août), avec au moins une espèce d'hiver ou de printemps pour ne pas disparaître six mois.

Les décisions qui dépendent d'Adrien sont regroupées en fin de document, section Questions.

## Périmètre et méthode

État audité : `main` des deux dépôts au 6 nov. 2026 (monorepo jusqu'à la PR #86, champis-ios jusqu'à la #28), la spec (révision 135) et l'analyse UX du 1er nov.

| Surface | Comment | Limite |
| --- | --- | --- |
| Site champis.app | Captures réelles en ordinateur (1440 × 900) et iPhone 15, carte, panneau, fiche, Guide, Soutenir | Fond de carte IGN bloqué par le réseau du bac à sable : absent des captures, la couche Champis est réelle |
| API en production | `/health`, `/tiles`, `/departements` du 6 nov. | Lecture seule |
| App iOS | Lecture du code SwiftUI écran par écran | Pas lancée (pas de Mac) : rien sur les performances ni le rendu réel |
| Textes | `shared/texts/`, blocs `about`, notifications, phrases de `explain.py` | — |
| Palette | Simulation protanopie et deutéranopie (matrices de Machado 2009), écarts ΔE76 | Calcul, pas test avec des personnes |
| Concurrence | Recherche web | Pages de carte-champignon.fr, de l'App Store et de Google Play inaccessibles depuis le bac à sable : à compléter |

Gravité : **bloquant** = le persona n'obtient pas sa réponse ou l'app dit quelque chose de faux ; **majeur** = il l'obtient avec effort ou doute ; **mineur** = friction. Les personas sont ceux du 1er nov. : Marc (veut comprendre), Hélène (trois coins, une question), Julien (découvreur venu par le site).

## Ce qui est solide

Ces acquis sont des avantages concurrentiels : les corrections ci-dessous ne doivent pas les entamer.

- **La finesse et la couverture** : 25 m sur 96 départements, 7 espèces publiées, météo de 22 672 cellules recalculée deux fois par jour, corrigée à l'altitude du pixel.
- **La traçabilité** : une référence par règle d'espèce, open data uniquement, aucun seuil dans le code. C'est un argument de confiance rare dans cette catégorie.
- **Le vocabulaire** : cinq mots de la palette, des dates plutôt que J+n, les chiffres derrière « Détails ». Le Guide est court, juste et bien écrit (« La couleur ne dit jamais « il y en a » : elle dit « les conditions sont réunies » »).
- **La vie privée par conception** : pas de compte, pas de photo, coins jamais partagés, suppression complète, notifications calculées côté serveur sans exécution en arrière-plan.
- **Le terrain d'abord dans l'app** : hors ligne par département proposé à la création d'un coin, « Rien trouvé » en une tape avec Annuler, barre latérale et inspecteur sur iPad et Mac.
- **La sécurité alimentaire** : fiches d'espèces sans aide à l'identification, confusions dangereuses sourcées, consigne du pharmacien, numéro d'urgence.
- **La qualité d'exécution** : parité Python et Swift par vecteurs, décodage PNG octet par octet, cache des tuiles, tests. Rien dans cet audit ne remet en cause l'architecture.

## Défauts UX : parcours et interactions

Dix-sept défauts, trois bloquants. Les deux plus graves sont des écarts entre ce que l'interface affirme et ce qui est vrai (accueil, bandeau des jours) ; le troisième prive le découvreur de sa première réponse, « et chez moi ? ».

| N° | Gravité | Défaut | Où, pour qui | Preuve | Correction proposée |
| --- | --- | --- | --- | --- | --- |
| U1 | Bloquant | L'accueil de l'app se ferme au premier bouton : « Suivant » termine l'accueil. Les cartes « Cueillir sans nuire » et « Rien n'est collecté » ne sont vues que par qui balaie | App, tous | `OnboardingView` : le bouton appelle `done()` quel que soit son libellé | « Suivant » avance d'une carte, « Commencer » ferme sur la dernière |
| U2 | Bloquant | Le site s'ouvre sur le Doubs pour tout le monde, sans bouton « autour de moi » ni recherche de commune | Site, Julien | Capture du 6 nov. (`#9/47.1/6.35`), aucun contrôle de position dans `app.js` | Bouton de géolocalisation, recherche de commune ou de forêt (API Adresse de l'État, gratuite), dernière vue mémorisée |
| U3 | Bloquant | Le bandeau des jours contredit la carte : il est colorié par l'indice du département, qui n'est pas à l'échelle du pixel. Le 6 nov. sur le Doubs : onze pastilles « Moyen » sur une carte surtout orange et rouge. Onze pastilles identiques n'apprennent rien | Site et app, Hélène, Julien | Capture du 6 nov., `GET /departements`, spec › Vue France (4 nov.) | Colorier chaque jour par la part de forêt visible au moins « bon », calculée depuis les tuiles déjà décodées ; ou par le score du point sélectionné ; sinon, pas de couleur |
| U4 | Majeur | Jours sans numéro : le site écrit « mar. … mar. » (3 et 10 nov.), l'app des initiales « m m » (mardi, mercredi). « Mieux vendredi », un vendredi, désigne la semaine suivante | Site, app | `Site.renderDays`, `CoinTrend.initial` | « sam. 8 » partout, séparation nette entre jours passés et à venir, « vendredi 13 » quand le jour se répète |
| U5 | Majeur | Les phrases de la fiche ne disent pas quoi faire : « hors du meilleur délai » ne dit pas trop tôt ou trop tard, « en marge de la saison » ne dit pas début ou fin, « pluie déclenchante » est un mot de modèle | Fiche, Hélène | `explain.py` | Phrases d'action : « pousse attendue dans 5 à 10 jours », « la pousse de la pluie du 20 oct. s'essouffle », « début de saison », « fin de saison » ; glossaire dans le Guide |
| U6 | Majeur | La fiche d'un coin n'explique rien : pas de phrases, pas d'itinéraire, pas mes observations à cet endroit | App, Hélène | `CoinDetailView` | Phrases de la fiche d'un point, bouton Itinéraire (Plans), mes trouvés et rien trouvés à moins de 200 m |
| U7 | Majeur | Noter en forêt oblige à viser la carte : l'appui long est invisible, et « Trouvé ici » prend le point pressé, pas ma position GPS | App, Marc | `MapScreen`, `QuickFoundSheet` (« votre position exacte : menu Retour terrain ») | Bouton flottant « Noter » quand la position est connue, prérempli à ma position, trouvé et rien trouvé dans la même feuille |
| U8 | Majeur | La notification parle en chiffres à l'anglaise (« bon (0.62, cèpe de Bordeaux) … Pic samedi : X 0.71 ») et ne part que si c'est bon aujourd'hui, alors qu'Hélène décide le vendredi pour le week-end | Notification, Hélène | `coins.compose` | « Bois de la Chaux : bon aujourd'hui pour les cèpes. Meilleur jour : samedi. » ; un rappel « ce week-end » le jeudi soir (question) |
| U9 | Majeur | Les Lactaires sont dans le Guide, absents du menu de la carte : aucune tuile publiée, indice nul dans les 96 départements | Site, app | `/tiles` et `/departements` du 6 nov. | Ne montrer un groupe qu'avec ses tuiles, ou « bientôt sur la carte » |
| U10 | Majeur | Hors saison, rien ne guide : carte rouge, aucune date de reprise, aucune autre espèce à regarder | Tous | Capture du 6 nov. (cèpes) | Calendrier des saisons par espèce dans la légende et le Guide, « hors saison, reprise vers mi-août en plaine » |
| U11 | Majeur | Le site ne montre la fraîcheur de la météo qu'en mode développement, alors que le Guide promet « la date de la météo s'affiche sur la carte » | Site | `fetchWeather` : `computed_at` réservé à `?dev=1` | Ligne permanente « Météo calculée ce matin à 3 h » sous le bandeau |
| U12 | Mineur | Messages d'erreur de développeur : « GET /tiles », « manifeste illisible », « classe prise sur la médiane de la cellule », erreurs système brutes | App | `MapModel`, `OfflineModel` | Messages en clair avec une action (Réessayer), le détail derrière un bouton |
| U13 | Mineur | Site mobile : barre d'onglets de deux entrées dans une grille de trois (case vide), Soutenir absent, boutons de zoom sous le panneau, attribution sous le bandeau | Site mobile | Capture iPhone 15, `site.css` | Trois entrées (Carte, Guide, Soutenir), commandes de zoom déplacées ou retirées sur téléphone |
| U14 | Mineur | Les réglages ne s'ouvrent pas depuis l'onglet Carte, où l'on passe le plus de temps | App | `SettingsView` appelée par Mes coins et Guide seulement | Entrée Réglages dans la barre de la carte |
| U15 | Mineur | L'app s'ouvre sur toute la France, pas sur ma région ni mes coins | App, Hélène | `MapModel.initialRegion` | Dernière vue, sinon les coins, sinon la position si autorisée |
| U16 | Mineur | « L'app Champis sur iPhone » sans lien : l'app n'est pas publique | Site | `Site.APP_LINE` | Masquer jusqu'à l'App Store, ou lien d'invitation TestFlight |
| U17 | Mineur | Impossible d'ajouter un coin là où la météo manque, ni de voir ou corriger une observation isolée | App | `PointSheet` : bouton masqué sans score | Coin possible sur tout point de forêt ; carnet personnel (voir Produit) |

## Défauts UI : palette, hiérarchie, accessibilité

Le défaut visuel le plus lourd est la palette : elle se lit mal pour environ un homme sur douze, cœur de la cible des 45–75 ans, et elle peint la forêt en rouge la moitié de l'année.

### La palette n'est pas faite pour une échelle

Le score est une grandeur ordonnée (de très faible à excellent) : l'état de l'art est une rampe séquentielle dont la clarté monte ou descend régulièrement. La palette actuelle est un rouge → vert de type « feu tricolore », dont la clarté (L\*) va 44, 66, 80, 61, 40 de très faible à excellent : les deux extrêmes ont presque la même clarté.

| Paire de classes | Écart normal (ΔE76) | Protanopie | Deutéranopie |
| --- | --- | --- | --- |
| Excellent / Très faible | 85 | 4 | 25 |
| Bon / Faible | 77 | 7 | 24 |
| Bon / Très faible | 95 | 31 | 13 |
| Moyen / Faible | 37 | 23 | 13 |

Sous un écart de 10, deux aplats voisins se confondent sur une carte. En protanopie, une zone excellente et une zone très faible ont la même couleur. La simulation est celle des formes complètes ; les formes partielles, plus fréquentes, rapprochent les mêmes paires, moins fortement.

Proposition, à trancher dans la spec car `shared/palette.json` est un contrat partagé (et les vecteurs de parité portent la palette) :

- rampe à clarté monotone, du clair au foncé, sans rouge (par exemple jaune pâle → vert → vert-bleu profond, famille viridis) ;
- « très faible » transparent ou presque : la carte ne montre plus que le signal, comme les cartes de chaleur de Strava ou Windy ;
- opacité qui suit le score, pour que le fond (chemins, lieux-dits) reste lisible là où il n'y a rien à voir.

### Autres défauts visuels

| N° | Gravité | Défaut | Preuve | Correction |
| --- | --- | --- | --- | --- |
| I1 | Majeur | Le vert d'accent du site échoue au contraste : 2,8:1 en texte sur le fond papier, 3,1:1 en blanc sur bouton (minimum WCAG AA : 4,5:1). Touche les liens, « Soutenir », « Calque et légende » | Calcul sur `#4CA64C`, `#f8f6f0`, `#fffdf8` | Accent foncé pour le texte (le vert « Excellent » passe), le vert « Bon » réservé aux aplats |
| I2 | Majeur | Sur le site, la couche à 75 % recouvre les chemins et les noms du Plan IGN : on ne sait pas où l'on est sur la carte colorée | `OPACITY = 0.75`, fond raster sous la couche | Opacité selon le score (voir palette), ou fond vectoriel (OpenFreeMap) avec les libellés au-dessus, comme l'app (`.aboveRoads`) |
| I3 | Majeur | Le panneau de droite sur ordinateur ressemble à un formulaire (deux listes déroulantes, une case à cocher) et reste vide aux deux tiers tant qu'on n'a pas cliqué | Capture 1440 × 900 | Groupes en pastilles avec icônes, puis « cette zone cette semaine » et la fiche du point dans l'espace libre |
| I4 | Mineur | Le bandeau des jours ne dit pas de quelle zone il parle (le département sous le centre n'est jamais nommé) | `paintDays`, `DayStrip` | « Doubs · cèpes » au-dessus des pastilles, ou la zone visible si U3 est retenu |
| I5 | Mineur | Icône feuille pour deux choses dans l'app : le menu Retour terrain et le potentiel toute saison | `MapScreen` | Une icône de crayon ou de panier pour noter |
| I6 | Mineur | Liste des couches du site à plat : deux groupes et sept espèces aux noms longs dans une seule liste, sans séparation | Capture, `refreshLayerList` | Groupes d'abord, espèces dans un sous-groupe replié, comme dans l'app |
| I7 | Mineur | Carte du site inaccessible au clavier : la fiche ne s'ouvre qu'au clic | `map.on("click")` | Touche Entrée sur le centre de la carte, avec un réticule |
| I8 | Mineur | Identité du site fonctionnelle mais neutre : police système, aucune image, liste d'espèces sans vignette. Elle ne se distingue pas d'un outil interne | Captures Guide et Espèces | Petit système de marque avant l'ouverture : titrage, vignettes des photos déjà choisies, une illustration de saison (question) |

## Défauts produit

Champis est prêt pour des proches qui connaissent Adrien ; il ne l'est pas pour un inconnu. Il manque une promesse, une preuve, une raison de revenir hors saison, une réponse pour les deux tiers des Français sur Android, et le socle légal d'un service public.

| N° | Gravité | Défaut | Pourquoi c'est un problème | Correction proposée |
| --- | --- | --- | --- | --- |
| P1 | Bloquant pour l'ouverture | Aucune promesse formulée : nulle part une phrase qui dit ce qu'est Champis et pour qui ; le site ouvre directement sur la carte | Un visiteur a quelques secondes pour comprendre ; l'App Store, la presse et le partage ont besoin de cette phrase | Une promesse en une ligne, par exemple « Où et quand poussent cèpes et girolles, forêt par forêt, jour par jour. Gratuit, sans compte. », en tête de l'accueil, de la fiche App Store et des partages |
| P2 | Majeur | Les trois groupes sont d'été et d'automne : rien de janvier à mai, ni les morilles, la cueillette de printemps la plus recherchée | Cinq à six mois sans usage : rétention, dons et référencement retombent à zéro chaque hiver | Avancer la décision « 3e espèce » de la phase 5 : arrière-saison (trompette de la mort, pied-de-mouton) pour prolonger jusqu'en décembre, morille pour le printemps (modèle plus difficile : frênes, ormes, brûlis, que BD Forêt voit mal) |
| P3 | Majeur | Aucune preuve que le modèle marche : l'AUC de la phase 1 a été reportée à la France, aucun résultat consigné depuis | Ni le public ni Adrien n'ont de signal de fiabilité ; c'est pourtant l'argument central face à un concurrent installé | Mesurer l'AUC GBIF France, publier « Comment on sait que ça marche » avec le chiffre et ses limites, suivre la part de « trouvé » quand le score est bon |
| P4 | Majeur | Les observations ne rendent rien à qui les donne : pas de carnet, pas de retour, suppression tout ou rien | Les négatives, « le vrai trésor » selon la spec, ne viendront pas sans incitation ; la calibration de la phase 5 sera vide | Carnet personnel privé (liste, carte, correction), bilan de fin de saison, compteur public « observations reçues cette saison » |
| P5 | Majeur | iPhone seulement, alors que la spec dit « ouvert à tous » | Android équipe environ deux tiers des smartphones en France (ordre de grandeur à sourcer), sans doute plus chez les cueilleurs ruraux : coins, notifications et hors ligne leur sont fermés | Trois options à trancher : application web installable (coins dans le navigateur, notifications Web Push), app Android, ou assumer iPhone seul |
| P6 | Majeur | Une carte publique à 25 m sur une forêt privée aux trois quarts environ, sans aide pour cueillir là où c'est permis | Conflits possibles avec propriétaires, ONF, communes et cueilleurs locaux (« l'app qui livre les coins ») ; l'avertissement seul ne suffit pas | Couche « forêts publiques » (données ouvertes de l'ONF et de l'IGN, à vérifier), rappel « forêt privée : accord du propriétaire » dans la fiche, discours de lancement préparé |
| P7 | Majeur | Pas de mentions légales ni de contact ; la page Confidentialité ne nomme ni responsable, ni base légale, ni durée de conservation, ni sous-traitants (Railway, Apple), ni adresses IP du limiteur, ni droits et recours | Obligatoire pour un site public et pour l'App Store ; « identifiant anonyme » est un pseudonyme au sens du RGPD, et la position liée à un identifiant se déclare dans les étiquettes de confidentialité | Mentions légales, Confidentialité complète et contact avant la levée du noindex ; « pseudonyme » partout |
| P8 | Majeur | Aucune mesure : ni audience, ni usage, ni justesse des notifications | Impossible de savoir si l'ouverture marche, si les notifications ont raison, si les dons couvrent | Compteurs agrégés côté serveur (appareils actifs, coins, notifications envoyées et ouvertes, observations), éventuellement un outil sans cookie pour le site |
| P9 | Mineur | Dons non branchés (`SUPPORT_URL` vide), demandés seulement depuis les réglages et une page | Le critère de la phase Ouverture est « un mois d'infrastructure couvert par les dons » | Lien de paiement, coûts publiés (« ce mois : X € de serveurs, Y € couverts »), demande en fin de saison et après une bonne sortie |
| P10 | Mineur | Textes inexacts ou malvenus : « publics dans le dépôt du projet » (les deux dépôts sont privés), « Rien n'est collecté », « tête-de-nègre » dans le nom du cèpe bronzé | Crédibilité ; le dernier terme est raciste, de plus en plus écarté des guides, inutilement exposé sur un site public | Publier `species/` ou corriger la phrase ; « Vos coins restent à vous » ; « Cèpe bronzé » seul (skill species-file) |
| P11 | Mineur | Aucun canal de retour : ni contact, ni « signaler une erreur » | Un modèle à calibrer et un service public ont besoin des remarques de terrain | Adresse de contact, « Signaler une erreur ici » dans la fiche, sans compte |
| P12 | Mineur | Le principe « Rien n'est recommandé » est ambigu face à une carte qui classe chaque parcelle | Il bloque des idées utiles (pages par département, alerte de début de saison) sans dire ce qu'il protège | Le reformuler : « aucun classement de secteurs, aucune suggestion de coin », et lister ce qui reste permis |

## La spec

La spec est un excellent journal technique, mais ce n'est plus une spec de produit : 78 000 signes, des sections qui décrivent l'état d'il y a trois semaines, et une liste « Points ouverts » de 32 entrées dont quatre au plus attendent encore une décision. Une session de code qui la lit de haut en bas peut implémenter une règle périmée.

### Ce qui est faux ou périmé

État au moment de l'audit ; les corrections faites le 6 nov. sont signalées dans la spec (« Corrigé le 6 nov. 2026 », notes « État au 6 nov. 2026 »).

| Section | Ce que dit la spec | Ce qui est vrai aujourd'hui | Gravité |
| --- | --- | --- | --- |
| Scoring | « Facteur lag : on cherche la dernière pluie déclenchante » | Le contrat du modèle dit l'inverse : meilleur événement de la fenêtre, pas le dernier (skill champis-model, règle 4) | Haute : contradiction dans le contrat du modèle |
| Scoring | Φ : « rampe de 30 jours » | `ramp_days` par espèce | Moyenne |
| Objectif, Décisions, App, Site | champis.adhumi.fr | champis.app depuis le 5 nov. | Moyenne |
| Objectif | « Espèces au lancement : cèpe de Bordeaux, girolle » | 8 espèces, 3 groupes (7 publiées sur la carte) | Moyenne |
| Scoring, App, Site | Vue France par département, « sur les 5 jours » ; page Aujourd'hui avec la France colorée | Vue France retirée le 4 nov., page Aujourd'hui retirée le 5 nov., bandeau de 11 jours | Moyenne |
| Backend | « Un seul service Railway » ; « FastAPI ou Node » ; « un jeton partagé dans l'app suffit » ; « archive 30 jours, cache 6 h » | Trois services, Postgres et un bucket ; FastAPI ; pas de jeton, limitation de débit ; accumulation SQLite, seau de 12 h, pré-chauffe | Moyenne |
| Sources de données | BRGM (géologie) et OpenStreetMap comme sources ; licences « de ma connaissance » | Ni BRGM ni OSM dans le pipeline ; licences jamais revérifiées | Moyenne (crédibilité de la page Données) |
| Pipeline | « Un dépôt champis-pipeline », GDAL | Dossier du monorepo, aucun outil GDAL requis | Basse |
| App iOS | Sélecteur segmenté, curseur J−3 → J+7, opacité réglable, adresse de l'API en réglage | Menu de calque, bandeau des jours, opacité fixe, menu développeur | Basse |
| Plan de réalisation | Phases 2, 3, 4 sans livrable réel ni résultat du critère ; phase 2 « 2 espèces » | France publiée avec 7 espèces ; aucune « sortie réelle » consignée | Haute : on ne sait pas où en est le projet |
| Coûts | Dispersés (Open-Meteo, Postgres, volume, bucket) | Aucun total mensuel, alors que la page Soutenir en a besoin | Moyenne |

### Ce qui manque

- **Promesse et positionnement** : une phrase, pour qui, contre quoi, et les non-objectifs.
- **Publics et parcours** : les trois personas vivent dans un autre doc ; la spec doit au moins les nommer, avec leurs parcours clés.
- **Principes d'interface** : les huit règles du 1er nov. (« des mots avant des chiffres »…) ne sont résumées qu'en une ligne de tableau.
- **Indicateurs de succès et mesure** : quoi compter, comment, sans trahir la promesse de vie privée.
- **Saisons et feuille de route des espèces** : quelle espèce, quand, avec quel critère d'entrée.
- **Plateformes** : la décision Android ou application web.
- **Accessibilité** : exigences sur la palette (daltonisme), les contrastes, VoiceOver, Dynamic Type ; aujourd'hui « à revoir plus tard ».
- **Contenus** : ton, glossaire (pluie déclenchante, potentiel, coin), catalogue des messages d'erreur et des états vides, texte des notifications.
- **Légal** : mentions, confidentialité complète, durée de conservation des observations, limitation de responsabilité (intoxications), étiquettes App Store.
- **Lancement** : calendrier, canaux, fiche App Store, référencement, presse.
- **Support et exploitation** : contact, alertes si la pré-chauffe ou les notifications échouent, que faire si Adrien est indisponible en pleine saison.
- **Coûts et financement** : un tableau mensuel tenu à jour.

### Restructuration proposée

Cinq onglets de travail plus les références ; chaque section dit l'état actuel, l'historique part dans le journal.

1. **Produit** (deux pages au plus) : promesse, publics, principes, périmètre et non-objectifs, indicateurs, feuille de route, lancement.
2. **Modèle et données** : scoring, schéma d'espèce, sources et licences vérifiées.
3. **Architecture** : pipeline, API, clients, hébergement, coûts.
4. **Décisions** : un seul tableau daté (sujet, décision, pourquoi, date, PR), où migrent les 28 points déjà tranchés.
5. **Points ouverts** : seulement ce qui attend Adrien (aujourd'hui : structure juridique des dons, AUC France, contrats « à confirmer » des 30 oct. et 2 nov.).
6. **Références** : inchangé.

Le skill `spec-sync` dirait alors où écrire selon la nature de la décision, et une PR qui change un comportement mettrait à jour la section d'état, pas seulement le journal.

## Product marketing (première passe)

Champis a de quoi se distinguer nettement (gratuit, sans compte, à la parcelle, sourcé), mais n'a encore ni message, ni moment de lancement, ni canal. Cette première passe pose des hypothèses ; depuis les réponses d'Adrien (échelle de quelques centaines d'utilisateurs, voir la mise à jour en tête), seuls le positionnement et la diffusion par lien restent d'actualité.

### Positionnement proposé

- **Catégorie : « la météo des champignons »**, pas « la carte des coins ». Le mot météo est familier, dit « quand » autant que « où », et désamorce le reproche de livrer les coins : Champis dit quand les conditions sont réunies, pas où sont les champignons.
- **Pour qui** : le cœur, ce sont les cueilleurs réguliers qui ont leurs coins (Hélène, Marc) ; la porte d'entrée, les curieux et randonneurs venus par la recherche ou un lien (Julien).
- **Contre quoi** : l'intuition (« il a plu, on ira dans dix jours »), les groupes de cueilleurs sur les réseaux, et carte-champignon.fr.
- **Preuves** : 25 m sur toute la France, sept espèces, météo recalculée deux fois par jour et corrigée à l'altitude, chaque règle sourcée ; la fiabilité mesurée (P3) manque encore.
- **Valeurs** : gratuit, sans compte, sans publicité, vos coins restent à vous, financé par dons, cueillette respectueuse.

Trois piliers de message : **quand y aller** (la prévision), **où chercher** (la parcelle), **sans nuire** (privé, légal, mycélium). Accroches à tester : « La météo des champignons, forêt par forêt. » · « Savoir quand y aller. » · « Vos coins, au bon moment. »

### Concurrence (à vérifier)

Les pages des produits n'ont pas pu être ouvertes depuis le bac à sable : ce tableau vient des résultats de recherche et de la spec.

| Produit | Ce qu'il propose (selon la source) | Modèle | Ce que Champis en retient |
| --- | --- | --- | --- |
| carte-champignon.fr | Indice par département, avec un « verrou » sur une partie des jours selon la spec | À confirmer ; jugé « trop cher pour un outil qui a l'air vibe codé » par Adrien | La référence que Champis veut remplacer |
| MycoMap (Italie) | Carte, carnet personnel, trouvailles enregistrées ; en PRO, prévisions locales et modèles écologiques par espèce ; zones consultées disponibles hors ligne | Gratuit + PRO | Le carnet personnel est attendu (P4) ; la prévision est l'argument payant |
| Sporecast | Prévision de pousse à 10 jours en Pro, vue carte annoncée | Gratuit + Pro | Horizon équivalent aux 7 jours de Champis |
| ShroomCast | Prévision à 14 jours, carte de probabilité sur 130 régions | À confirmer | Maille régionale : la parcelle reste un avantage |
| Tattis (Finlande) | Cartes de chaleur par espèce, météo de l'institut finlandais | À confirmer | Le modèle « météo nationale + carte par espèce » existe ailleurs |

Lecture : la norme du marché semble être le gratuit plus un abonnement qui ouvre la prévision. Un service entièrement gratuit, sans compte et à la parcelle se distingue fortement, à condition de le dire.

### Canaux

Écrit avant les réponses d'Adrien ; à l'échelle retenue, seuls le bouche-à-oreille et le partage par lien s'appliquent.

| Canal | Pourquoi | Ce qu'il faut |
| --- | --- | --- |
| Référencement | La recherche est saisonnière et locale (« cèpes Doubs », « pousse des girolles ») | Lever le noindex ; une page par département et par groupe (« Cèpes dans le Doubs : les conditions de la semaine ») générée depuis `/departements` ; fiches d'espèces indexables ; P12 clarifié |
| Presse quotidienne régionale | Chaque automne, des sujets « saison des champignons » ; un angle neuf : gratuit, sans pub, sourcé | Dossier de presse, image « la France des cèpes aujourd'hui », un porte-parole |
| Sociétés mycologiques | Relais crédibles, déjà cités par la consigne « faites contrôler » | Contact, présentation, éventuellement un retour sur les fiches d'espèces |
| Groupes de cueilleurs (réseaux sociaux) | Très actifs chez les 45–75 ans | Partage d'une vue avec image d'aperçu (la position est déjà dans l'URL) |
| App Store | Point d'entrée de l'app | Nom et sous-titre (« Champis — météo des champignons »), captures qui portent la promesse, étiquettes de confidentialité exemplaires |
| Bouche-à-oreille | C'est ainsi que l'outil est né | « Partager Champis » dans l'app, lien vers la page de l'app sur le site |

### Calendrier

La saison est le levier principal, et elle se termine. Recommandation d'origine : ne pas ouvrir publiquement maintenant ; utiliser l'hiver pour corriger et préparer ; élargir la bêta au printemps ou en juin–juillet ; ouvrir fin août 2027, au début de la saison des cèpes ; faire le bilan fin novembre 2027. Le plan révisé (annexe) garde ce calendrier sans lancement public.

### Risques d'image à préparer

- « L'app qui livre les coins » : réponse prête (météo, pas coins ; forêts publiques ; respect), couche des forêts publiques (P6).
- « L'app m'a dit qu'il y avait des cèpes » après une intoxication : la consigne du pharmacien est déjà là ; ajouter une limitation de responsabilité et ne jamais montrer de photo sans sa mise en garde.
- Prévision fausse un week-end de forte attente : publier les limites (« ce que l'app ne sait pas » existe) et la fiabilité mesurée.

### Indicateurs

En saison : visiteurs du site, part qui ouvre une fiche, installations, coins par appareil, part qui accepte les notifications, observations par appareil actif, dons du mois face aux coûts du mois. Depuis la décision « mesure minimale » du 6 nov., la liste retenue est celle de l'annexe.

## Plan d'itération

Plan d'origine : cinq étapes, chacune close par un critère vérifiable. Il est remplacé par le plan révisé de l'annexe, plus léger (pas de lancement public), qui garde les mêmes étapes A à C.

| Étape | Période | Contenu | Critère de passage |
| --- | --- | --- | --- |
| A · Corriger | nov. 2026 | Accueil, bandeau des jours, dates, notification, Lactaires, textes faux, fraîcheur météo, site mobile, spec nettoyée | Plus rien de faux à l'écran |
| B · Clarifier | nov.–déc. 2026 | Palette lisible par tous, phrases d'action, coin expliqué, position et recherche sur le site, bouton Noter, erreurs en clair | 4 testeurs sur 5 décident « samedi ou pas » en moins d'une minute |
| C · Préparer | janv.–mars 2027 | Promesse et accueil, pages légales, mesure, dons, AUC publiée, forêts publiques, carnet, décision Android, fiche App Store | Pages légales en ligne, fiabilité publiée, lien de don actif |
| D · Bêta élargie | avr.–juil. 2027 | Testeurs au-delà des proches, espèce de printemps ou d'été, pages par département, rappel du week-end, presse préparée | Les notifications « bon » confirmées par les observations des testeurs |
| E · Lancer | fin août 2027 | App Store, noindex levé, presse régionale, sociétés mycologiques, indicateurs suivis chaque semaine de la saison | Bilan fin nov. 2027 : un mois d'infrastructure couvert par les dons |

Les défauts se répartissent ainsi :

1. **A · Corriger** : U1, U3 (en attendant mieux, retirer la couleur du bandeau), U4, U8, U9, U11, U13, U14, U16, I1, P10, et les affirmations périmées de la spec. Petites PR, aucune décision structurante sauf U8 (texte de notification).
2. **B · Clarifier** : la palette (décision de spec, vecteurs à régénérer), I2, I3, I6, I7, U2, U5, U6, U7, U10, U12, U15, U17. Critère : test avec cinq personnes (deux Hélène, deux Julien, un Marc) sur trois tâches : décider pour samedi, expliquer une couleur, noter « rien trouvé » en forêt.
3. **C · Préparer** : P1, P3, P4, P5 (décision), P6, P7, P8, P9, P11, P12, la spec restructurée, la fiche App Store et ses étiquettes de confidentialité.
4. **D · Bêta élargie** : P2 (une espèce hors automne), pages par département, rappel du week-end, dossier de presse ; on mesure si les notifications ont raison.
5. **E · Lancer** : ouverture publique au début de la saison, puis suivi hebdomadaire des indicateurs ; le critère final reprend celui de la phase Ouverture de la spec.

Chaque étape commence par sa ligne dans la spec (skill `spec-sync`), comme pour les lots du 1er nov.

## Questions posées à Adrien

Dix-huit questions. Réponses du 6 nov. : Q1 (des dizaines à centaines d'utilisateurs, gratuit), Q2 (2 à 10 h par semaine), Q3 (rien encore partagé avec les proches), Q9 (toute espèce, ajout progressif), Q12 (mesure vraiment minimale), Q15 (carte-champignon.fr « trop cher pour un outil qui a l'air vibe codé »). Les autres ont été tranchées sur la PR monorepo #87 ou restent ouvertes : voir l'annexe, Décisions sur les suites de l'audit et Points encore ouverts.

| N° | Question | Pourquoi | Bloque |
| --- | --- | --- | --- |
| Q1 | Quelle ambition à douze mois : un outil pour quelques dizaines de proches, ou un service utilisé par des milliers d'inconnus ? | Le légal, Android, le support et les coûts en dépendent | C, D, E |
| Q2 | Ouverture publique fin août 2027, ou plus tôt ? Combien d'heures par semaine pour Champis cet hiver ? | Calibre les dates du plan | Calendrier |
| Q3 | Qu'ont dit les proches après leurs sorties ? Combien utilisent l'app, et quelles frictions ? Les critères « une sortie réelle » des phases 3 et 4 sont-ils remplis ? | Aucun retour d'usage n'est consigné | B |
| Q4 | Android : application web installable, app native, ou iPhone seul assumé ? | Deux tiers des smartphones environ (P5) | C |
| Q5 | Palette : quitter le rouge → vert pour une rampe lisible par les daltoniens, « très faible » transparent ? | Contrat partagé, vecteurs, habitudes des proches | B |
| Q6 | Bandeau des jours : part de forêt visible au moins « bon », score du point sélectionné, ou pas de couleur ? | U3 | A, B |
| Q7 | « Rien n'est recommandé » permet-il des pages par département et une alerte « début de saison dans votre secteur » ? | P12, référencement | D |
| Q8 | Ajoute-t-on une couche des forêts publiques ? | P6 : utile et protecteur | C |
| Q9 | Quelle espèce hors automne : trompette ou pied-de-mouton (arrière-saison), morille (printemps), ou aucune avant la calibration ? | P2 | D |
| Q10 | Un carnet personnel des observations (voir, corriger, supprimer une à une), contre la décision du 1er nov. « aucune liste » ? | P4 | C |
| Q11 | Notifications : un rappel « ce week-end » le jeudi soir, une alerte de début de saison, une heure réglable ? | U8 | D |
| Q12 | Mesure : des compteurs agrégés côté serveur, et un outil sans cookie pour le site ? | P8 | C |
| Q13 | Ouvre-t-on le code, ou au moins `species/` et le modèle ? | Crédibilité ; le Guide l'affirme déjà (P10) | C |
| Q14 | Identité : rester sobre et outil, ou viser plus chaleureux (titrage, photos, illustrations) ? Un regard de designer est-il possible ? | I8 | C |
| Q15 | Que sait-on de carte-champignon.fr (modèle, prix, audience) et pourquoi le remplacer ? D'autres concurrents ? | Concurrence non vérifiée | Marketing |
| Q16 | Des contacts : société mycologique, presse régionale, groupes de cueilleurs ? | Canaux de lancement | D |
| Q17 | Dons : association créée ou à créer ? Quel montant mensuel visé ? | P9, critère final | C |
| Q18 | Marque : « Champis » a-t-il été vérifié (INPI, stores) ? Une des accroches proposées convient-elle ? | Positionnement | C |

## Sources

Pages et documents ouverts pour cet audit (6 nov. 2026) :

- [Spec — Champis (carte de cueillette)](https://claude.ai/artifact/54H9wdXiTTFcnoP6DAW81C), révision 135
- [Champis — Analyse UX/UI et proposition de refonte](https://claude.ai/artifact/9hbiPbtBbk4fNth1uSTBgB), 1er nov. 2026
- Dépôts privés `adhumi/champis` et `adhumi/champis-ios`, branche `main`
- Site : [carte](https://champis.app/web/carte.html), [Guide](https://champis.app/web/comprendre.html), [Espèces](https://champis.app/web/comprendre.html?article=especes), [Soutenir](https://champis.app/web/soutenir.html)
- API : [/health](https://champis.app/health), [/tiles](https://champis.app/tiles), [/departements](https://champis.app/departements?group=cepes&day=2026-11-06)

Résultats de recherche, pages non ouvertes (les magasins d'applications et carte-champignon.fr sont bloqués depuis le bac à sable) : fiches de MycoMap sur Google Play, de Sporecast, ShroomCast, Tattis et Mushroom Spot sur l'App Store. Les lignes qui en viennent sont marquées « à vérifier ».

Méthode, de mémoire et non revérifiée : simulation du daltonisme par les matrices de Machado, Oliveira et Fernandes (2009) ; contrastes selon WCAG 2.2, critère 1.4.3. Les ordres de grandeur sans source (part d'Android en France, part de forêt privée, fréquence du daltonisme) sont à sourcer avant tout usage public.

---

## Annexe — section Produit de la spec (copie du 6 nov. 2026)

Copie de la section « Produit » de l'onglet principal de la [spec](https://claude.ai/artifact/54H9wdXiTTFcnoP6DAW81C), avec les décisions prises par Adrien le 6 nov. 2026 dans la conversation puis sur cette PR. La spec fait foi : les décisions et points ouverts y évoluent, pas ici.

Ce qui est **décidé** est marqué comme tel ; le reste est **proposé**.

### Ambition et contraintes

Décidé par Adrien le 6 nov. 2026 :

| Sujet | Décision |
| --- | --- |
| Échelle visée | Des dizaines à quelques centaines d'utilisateurs : objectif atteint à ce niveau. Au-delà, l'infrastructure et donc le modèle économique seraient à revoir |
| Modèle | Gratuit ; soutien facultatif (voir Décisions sur les suites de l'audit) |
| Temps disponible | 2 à 10 heures par semaine selon les besoins |
| Plateformes | App iOS sur l'App Store public ; app Android native à prévoir ; le site garde son noindex jusqu'à la publication des apps |
| Code | Tout devient open source avant la publication des apps |
| Mesure d'audience | Vraiment minimale, pour éviter fenêtres de consentement et obligations RGPD supplémentaires |
| Espèces | Toute espèce est envisageable, ajoutée progressivement |
| Partage | Le site et l'app n'ont pas encore été partagés avec les proches : les critères « une sortie réelle » des phases 3 et 4 restent à remplir |

Conséquences (proposé) :

- **Pas de lancement marketing** : ni presse ni référencement poussé ; l'App Store public et la levée du noindex arrivent avec la publication des apps, sans campagne. La diffusion se fait par bouche-à-oreille.
- **Les coûts restent fixes** : la météo est précalculée pour toute la France quel que soit le nombre d'utilisateurs ; seule la sortie réseau des tuiles croît avec l'usage.
- **La confiance tient au soin** : Adrien juge carte-champignon.fr « trop cher pour un outil qui a l'air vibe codé » ; Champis doit être gratuit et ne pas avoir l'air bricolé.
- **Les obligations légales de base demeurent** dès qu'un inconnu peut ouvrir le site ou l'app : mentions légales, contact, confidentialité complète.

### Promesse et positionnement

Proposé, à valider. Une phrase reprise en tête du site, dans l'accueil de l'app, sur l'App Store et dans chaque partage.

- **Promesse** : « Où et quand poussent cèpes et girolles, forêt par forêt, jour par jour. Gratuit, sans compte. »
- **Catégorie** : « la météo des champignons » plutôt que « la carte des coins » : Champis dit quand les conditions sont réunies, pas où sont les champignons.
- **Pour qui** : d'abord les cueilleurs qui ont leurs coins (Hélène, Marc), puis les curieux (Julien). Personas : doc « Champis — Analyse UX/UI et proposition de refonte », 1er nov. 2026.
- **Face à carte-champignon.fr** : gratuit, à la parcelle, chaque règle sourcée, code ouvert, et soigné.
- **Accroches à choisir** : « La météo des champignons, forêt par forêt. » · « Savoir quand y aller. » · « Vos coins, au bon moment. »

### Principes d'interface

Huit règles décidées avec la refonte du 1er nov. 2026 ; quand deux solutions se valent, la règle la plus haute l'emporte.

1. **Trois questions, trois entrées** : Quand (Mes coins), Où (Carte), Pourquoi (Guide).
2. **Des mots avant des chiffres** : libellé de la palette d'abord ; S, T, M, Φ seulement derrière « Détails ».
3. **Des dates, pas des J+n.**
4. **Un silence expliqué là où il se produit** (pixel transparent, cellule sans météo, hors ligne).
5. **Deux tapes en forêt** pour trouvé, rien trouvé, ajouter un coin.
6. **Natif et sobre** dans l'app ; le site reprend la structure, pas le verre.
7. **La confiance se montre** : pas de compte, pas de collecte superflue, dit une fois au bon endroit.
8. **Rien n'est recommandé** : pas de classement de secteurs ni de suggestion de coin.

Trois ajouts proposés après l'audit du 6 nov., à valider :

9. **Rien de faux à l'écran** : un texte qui contredit le code ou les données est un défaut bloquant.
10. **Soigné, pas bricolé** : aucun message de développeur, les mêmes formats de date et de nombre partout (virgule décimale, « sam. 8 nov. »), aucune promesse sans source.
11. **Lisible par tous** : palette distinguable par les daltoniens rouge-vert et détachée du fond de carte, contraste WCAG AA (4,5:1) pour tout texte, VoiceOver et Dynamic Type dans l'app, carte du site utilisable au clavier.

### Mesure minimale

Décidé : une mesure vraiment minimale (6 nov. 2026). Proposé : quelques compteurs agrégés par jour, calculés côté serveur à partir de ce que Champis reçoit ou stocke déjà. Rien n'est lu ni écrit sur l'appareil pour mesurer : pas de cookie, pas d'identifiant nouveau, pas d'outil tiers, donc pas de fenêtre de consentement (lecture de la règle CNIL à confirmer avant publication).

| Compteur, par jour | D'où il vient | À quoi il sert |
| --- | --- | --- |
| Ouvertures de la carte du site | Nombre de requêtes sur `carte.html`, sans adresse IP conservée | Savoir si le site sert, en saison et hors saison |
| Appareils avec au moins un coin, nombre de coins | Table des coins, déjà en base | Savoir si l'app sert au-delà d'Adrien |
| Observations reçues (trouvé, rien trouvé) | Table des observations, déjà en base | Savoir si le retour terrain vit (sinon il sera retiré) |
| Notifications envoyées, échecs | Journal du service de notifications, déjà écrit | Savoir si « mes coins » fonctionne |
| Cellules sans météo après la pré-chauffe | Déjà calculé | Exploitation |
| Soutiens reçus, coûts du mois | Relevé manuel, mensuel | Critère de la phase Ouverture |

Règles proposées : agrégats seulement, gardés 13 mois, visibles d'Adrien seul (par exemple dans `champis-api doctor`) ; aucune requête vers un tiers qui ne soit pas nécessaire au service, ce qui écarte à terme le CDN unpkg du site ; les fonds de carte IGN et OpenStreetMap restent, et la page Confidentialité le dit.

### Espèces : ajout progressif

Décidé : toute espèce est envisageable, ajoutée une à une (6 nov. 2026). Les trois groupes actuels sont d'été et d'automne : Champis n'a rien à montrer de janvier à mai.

Règle proposée : **une espèce entre dans le Guide et sur la carte le même jour**, quand son fichier est complet et validé (skill species-file), son contrôle GBIF passé, ses tuiles T et G publiées avec un indice par département non nul, et son bloc `about` relu par Adrien.

Ordre proposé : (1) lactaire délicieux, déjà décidé, tuiles à publier ; (2) une espèce d'arrière-saison, pied-de-mouton ou trompette de la mort ; (3) la morille au printemps, modèle à part à étudier (frênes, ormes, ripisylves, brûlis mal vus par BD Forêt). Les espèces de pré se heurtent à la règle « hors forêt → T = 0 ».

### Coûts mensuels

Total à relever sur les factures ; il manque pour la page Soutenir et pour le critère « un mois couvert par les dons ».

| Poste | Montant | Source |
| --- | --- | --- |
| Open-Meteo, plan Standard | ≈ 29 € | Spec, 17 oct. 2026 |
| Postgres Railway | ≈ 5 $ | Spec, 30 oct. 2026 |
| Bucket Railway (≈ 41 Go : jeu France 20,4 Go d'après le manifeste du 6 nov., jeux par département à peu près autant ; plus les G à venir) | ≈ 0,6 $ à 0,015 $ le Go | Spec, 18 oct. ; `/tiles` |
| Trois services Railway et volume | À relever | Facture Railway |
| Sortie réseau du relais de tuiles | À relever (0,05 $ le Go selon la spec) | Facture Railway |
| Domaine champis.app | À relever | Registraire |
| Comptes développeur Apple et Google Play | À relever | Apple, Google |

### Décisions sur les suites de l'audit

Décidé par Adrien le 6 nov. 2026, sur cette PR :

| Sujet | Décision |
| --- | --- |
| Distribution de l'app | App Store public |
| Android | App native à prévoir |
| Référencement du site | Noindex conservé jusqu'à la publication des apps |
| Palette | Rampe à clarté monotone sans rouge, « très faible » transparent, opacité qui suit le score ; couleurs choisies pour se détacher nettement du fond de carte |
| Bandeau des jours | Retiré de la carte. Les onze jours restent dans la fiche d'un point, avec la tendance et, quand les prévisions le permettent, le meilleur jour à venir |
| Phrases en clair | Sens du délai (« trop tôt : pousse attendue dans 5 à 10 jours », « la pousse s'essouffle »), « début » ou « fin de saison », « grosse pluie » au lieu de « pluie déclenchante » ; seuils génériques ; contrat `summary` à mettre à jour dans Backend |
| Notification | En mots, sans chiffres ni point décimal ; rappel « ce week-end » le jeudi soir à tester avec les proches |
| Retour terrain | Trouvé et rien trouvé maintenus tels quels, sans carnet personnel ; la fonction sera retirée si elle ne reçoit pas de retours |
| Textes | Corrections retenues (« Vos coins restent à vous », « identifiant pseudonyme », « Cèpe bronzé ») ; la phrase « publics dans le dépôt du projet » deviendra vraie, les dépôts passant en public avant la publication des apps |
| Code ouvert | Tout open source ; découpage possible en dépôts `champis` (référentiel : `species/`, `SCHEMA.md`), `champis-api`, `champis-web`, `champis-ios`, `champis-android` |
| Pages légales | Mentions légales, contact et confidentialité complète ; éditeur : Adrien en personne tant qu'il n'y a pas d'association, avec une adresse dédiée |
| Soutien | 100 % facultatif, ponctuel ou récurrent, par achat intégré sur iOS, éventuellement récompensé par une collection d'icônes d'app (espèces de champignons) ; RevenueCat sur iOS et sur le web (décision du 30 oct. confirmée) |
| Forêts publiques | Statut public ou privé de la forêt affiché dans la fiche d'un point ; pas sur la carte, en tout cas pas par défaut |
| Structure de la spec | Un onglet unique : la section Produit vit dans l'onglet principal |

### Points encore ouverts

- [ ] **Jour affiché par la carte sans bandeau.** (a) Toujours aujourd'hui ; la fiche d'un point montre les onze jours, la tendance et le meilleur jour sans changer la carte. (b) Choisir un jour dans la fiche recolore la carte, avec un rappel visible du jour affiché et un retour à aujourd'hui. Recommandation : (a), plus simple et fidèle à la décision ; le potentiel toute saison reste pour repérer des secteurs.
- [ ] **Découpage des dépôts.** Où vont `pipeline/`, `mapping/` et `shared/` (palette, vecteurs de parité, textes) ? Recommandation : le référentiel `champis` garde tous les contrats partagés (`species/`, `SCHEMA.md`, `mapping/`, `shared/`) ; le pipeline rejoint `champis-api`, qui en dépend déjà comme paquet.
- [ ] **Licences avant ouverture.** Code (MIT ?) et données (fichiers d'espèces, textes du Guide : CC BY 4.0 ?), compatibles avec les sources (Etalab, CC BY de SoilGrids et d'Open-Meteo).
- [ ] **Structure juridique du soutien** (point du 30 oct.) : RevenueCat verse à un compte Apple et à un compte Stripe au nom d'une personne ou d'une entité ; particulier ou association.
- [ ] **Icônes en récompense** : quelles espèces, à partir de quel soutien, ponctuel ou récurrent.
- [ ] **Adresse de contact dédiée**, à créer pour les mentions légales.
- [ ] **Calendrier de l'app Android native.**

### Plan proposé

Proposé, à valider : cinq temps calibrés sur 2 à 10 heures par semaine, sans lancement marketing ; il remplace pour la suite le contenu de la phase « 4 bis — Ouverture » du plan de réalisation, dont le critère final est gardé.

1. **Maintenant, sans code (nov. 2026)** : partager le **site** avec trois à cinq proches pour les dernières sorties de la saison et noter leurs réactions (critère de la phase 3) ; publier les tuiles du lactaire ; relever les coûts ; créer l'adresse de contact. L'app attend l'étape A, parce que son accueil saute l'avertissement légal.
2. **A · Corriger (déc. 2026)** : accueil de l'app, bandeau des jours retiré de la carte, dates avec leur numéro, notification en mots, textes faux, fraîcheur de la météo sur le site, site mobile, réglages depuis la carte. Critère : plus rien de faux à l'écran.
3. **B · Clarifier (janv.–févr. 2027)** : nouvelle palette, phrases d'action, fiche d'un point avec les onze jours, la tendance, le meilleur jour et le statut public ou privé de la forêt, fiche d'un coin expliquée, position et recherche de commune sur le site, bouton « Noter » à ma position, messages d'erreur en clair, contrastes. Critère : quatre proches sur cinq décident « samedi ou pas » en moins d'une minute et savent dire ce qu'une couleur veut dire.
4. **C · Préparer la publication (mars–mai 2027)** : pages légales et contact, mesure minimale, soutien RevenueCat sur iOS et le web avec ses icônes, dépôts découpés et ouverts avec leurs licences, fiche App Store et étiquettes de confidentialité, accueil du site avec la promesse, espèce d'arrière-saison rédigée. Critère : un inconnu comprend Champis et ses règles sans explication.
5. **D · Publication et saison 2027 (juin–nov.)** : app sur l'App Store public avant la fin août, noindex levé le même jour, compteurs suivis chaque semaine ; Android natif selon son calendrier. Bilan fin nov. 2027 : un mois d'infrastructure couvert par le soutien, et les notifications « bon » confirmées par les observations.

Chaque étape commence par ses lignes dans la spec, comme les lots du 1er nov.
