# Cahier des charges — OpenToAll

**Plateforme de découverte et de valorisation de la contribution open source, pensée pour les développeurs africains**

Version 1.0 — MVP

---

## 1. Contexte et origine du projet

Le projet naît d'un constat vécu directement par le porteur du projet : lors d'une candidature à une bourse d'inscription à un événement organisé par la CNCF (Cloud Native Computing Foundation) à Salt Lake City, il était exigé d'être contributeur à un projet open source de la fondation (Kubernetes, Helm, Argo, etc.).

La recherche du bon projet auquel contribuer s'est révélée longue et confuse :
- Difficulté à savoir par où commencer et quels projets existent
- Difficulté à trouver un projet correspondant à son langage de programmation (Python)
- Difficulté à trouver des issues encore ouvertes et non assignées
- Absence d'outil centralisant ces critères de façon simple

Une fois la première contribution réalisée, un fort sentiment de satisfaction et de valeur (personnelle et professionnelle) en est ressorti — mais le chemin pour y arriver reste aujourd'hui semé d'obstacles, en particulier pour les développeurs africains, sous-représentés dans l'open source mondial et souvent moins accompagnés dans cette démarche.

## 2. Constat marché

Des agrégateurs de « good first issues » existent déjà (goodfirstissue.dev, up-for-grabs.net, CodeTriage, First Timers Only, l'outil natif de GitHub via `/contribute`). Le besoin d'agrégation basique est donc déjà couvert par le marché.

**Ce qui n'existe pas :** une plateforme qui s'adresse spécifiquement aux développeurs africains, qui les rend visibles entre eux et vis-à-vis du reste du monde, et qui tient compte de leurs contraintes réelles (bienveillance des mainteneurs envers les débutants, réactivité des projets, poids des dépôts sur une connexion internet limitée).

C'est cet angle — le « pour qui » plutôt que le « quoi » — qui constitue la proposition de valeur différenciante de Baokod.

## 3. Objectifs du projet

- Simplifier et centraliser la recherche de projets et d'issues open source auxquels contribuer, quel que soit le niveau (débutant à senior) et la fondation (CNCF, Apache, Linux Foundation, ou aucune)
- Réduire drastiquement le temps perdu à chercher un projet adapté à son langage et à son niveau
- Donner de la visibilité aux développeurs africains qui contribuent déjà, pour créer un effet d'entraînement et de fierté collective
- Aider à choisir des projets adaptés aux contraintes réelles du continent (réactivité des mainteneurs, bienveillance, poids des dépôts)

## 4. Public cible

- Développeurs africains, débutants comme confirmés, cherchant à faire leurs premiers pas ou à approfondir leur pratique de l'open source
- Développeurs cherchant à justifier une contribution open source dans le cadre d'une candidature (bourse, événement, recrutement)
- Dans un second temps : toute la communauté open source mondiale intéressée par la découverte de projets et de contributeurs

## 5. Périmètre du MVP

Le MVP se concentre sur trois blocs fonctionnels. Les deux premiers constituent le socle technique indispensable ; les deux derniers constituent la différenciation du projet.

### 5.1 Bloc 1 — Agrégateur d'issues (socle)

Fonctionnalité centrale sans laquelle le reste ne peut pas exister.

- Connexion à l'API GitHub (REST et/ou GraphQL) pour récupérer les issues taguées comme accessibles aux contributeurs (`good first issue`, `help wanted`, `beginner friendly`, etc.)
- Pas de restriction à une fondation en particulier : couverture large (projets CNCF, Apache, Linux Foundation, projets indépendants)
- Filtrage des issues déjà assignées, pour n'afficher que celles réellement disponibles
- Rafraîchissement périodique des données (job planifié, pas de scraping en temps réel à chaque visite)

**Critères de tri disponibles :**
- Langage de programmation
- Niveau requis (débutant / intermédiaire / confirmé — déduit des labels ou d'une heuristique simple)
- Popularité du dépôt (nombre d'étoiles, de contributeurs actifs)
- Fondation ou organisation d'appartenance (optionnel, filtrable)
- Statut d'assignation (assigné / libre)
- S'il y a d'autre tri possible, je laisse le choix a cursor de les ajouter

### 5.2 Bloc 2 — Tri par contraintes réelles (différenciation)

Filtres avancés absents des plateformes concurrentes, construits à partir de métriques calculées automatiquement via l'API GitHub :

- **Réactivité du projet** : temps moyen de réponse à une issue, temps moyen jusqu'au merge d'une PR
- **Bienveillance envers les débutants** : proportion de PR de primo-contributeurs effectivement mergées (par opposition à fermées sans suite), présence d'un fichier `CONTRIBUTING.md` clair, existence d'un label dédié aux débutants
- **Poids du dépôt** : taille du dépôt en Mo, pour identifier les projets clonables facilement avec une connexion limitée

Ces métriques peuvent être calculées automatiquement dans un premier temps ; une brique de retour d'expérience communautaire (notation par les utilisateurs) pourra être envisagée en V2.

### 5.3 Bloc 3 — Visibilité des développeurs africains (différenciation)

- Création de profils publics pour les développeurs qui le souhaitent (rattachés à leur compte GitHub)
- Mise en avant des contributions réalisées via la plateforme (projet, type de contribution, date)
- Classement ou mur des contributeurs, filtrable par pays
- Objectif : créer une preuve sociale et un effet d'entraînement (« untel l'a fait dans mon pays, je peux le faire aussi »)

## 6. Fonctionnalités repoussées à une V2

- **Mentorat par les pairs** : mise en relation de développeurs expérimentés avec des débutants pour un accompagnement sur leur première contribution
- **Lien direct avec bourses et événements** : génération de preuves de contribution vérifiables et adaptées aux critères de bourses type CNCF, Linux Foundation, Google Summer of Code

## 7. Stack technique proposée

Le porteur du projet développant principalement en Python, la stack est construite autour de cet écosystème.

| Composant | Choix proposé | Justification |
|---|---|---|
| Backend / API | **FastAPI** | Performant, typé, génération automatique de documentation OpenAPI, adapté à un projet qui interroge beaucoup une API externe (GitHub) |
| Traitement asynchrone | **Celery** + **Redis** | Nécessaire pour les jobs planifiés de récupération périodique des issues sans bloquer l'application |
| Base de données | **PostgreSQL** | Fiable, gère bien les requêtes de filtrage complexes (langage, niveau, statut) |
| ORM | **SQLAlchemy** (ou **SQLModel**, plus proche de FastAPI) | Standard robuste de l'écosystème Python |
| Frontend | **Next.js** (React) ou **HTMX + Jinja2** | Next.js si l'on vise une interface riche dès le MVP ; HTMX + Jinja2 si l'on veut rester 100 % Python côté rendu et limiter la complexité au démarrage |
| Authentification | **OAuth GitHub** | Cohérent avec l'usage (les utilisateurs ont de toute façon un compte GitHub), évite de gérer des mots de passe |
| Hébergement (MVP) | **Railway** ou **Render** pour le backend, **Vercel** pour le frontend si Next.js | Offres gratuites ou très économiques suffisantes à l'échelle du MVP |
| Cache | **Redis** | Réduction des appels répétés à l'API GitHub (rate limit à surveiller) |

**Point d'attention technique :** l'API GitHub impose des limites de requêtes (rate limiting), notamment en usage non authentifié. Il faudra prévoir une authentification applicative (GitHub App ou token) et une stratégie de cache dès le MVP pour ne pas être bloqué.

## 8. Indicateurs de succès du MVP

- Nombre de développeurs inscrits sur la plateforme
- Nombre de contributions effectivement réalisées et tracées via la plateforme
- Répartition géographique des utilisateurs (vérifier l'atteinte réelle du public africain visé)
- Taux de retour des utilisateurs ayant trouvé une issue pertinente en moins de 5 minutes

## 9. Prochaines étapes

1. Validation définitive du nom et réservation du nom de domaine
2. Maquettage des écrans principaux (liste d'issues, profil contributeur, classement)
3. Mise en place du socle technique (Bloc 1) en priorité
4. Développement du Bloc 2 (tri par contraintes réelles)
5. Développement du Bloc 3 (visibilité des contributeurs)
6. Tests avec un groupe restreint de développeurs avant ouverture publique
