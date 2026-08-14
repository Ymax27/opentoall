<div align="center">

<img src="static/img/logo.svg" width="72" alt="OpenToAll logo" />

# OpenToAll

**L'open source, ouvert à tous.**

Plateforme de découverte et de valorisation de la contribution open source,
pensée pour les développeurs africains.

[Signaler un bug](https://github.com/Ymax27/opentoall/issues) ·
[Proposer une fonctionnalité](https://github.com/Ymax27/opentoall/issues) ·
[Contribuer](CONTRIBUTING.md)

</div>

---

## 🌍 Pourquoi ?

Des agrégateurs de « good first issues » existent déjà. Ce qui n'existait pas :
une plateforme qui **s'adresse spécifiquement aux développeurs africains**, les
rend visibles, et tient compte de leurs contraintes réelles :

- **Réactivité** des mainteneurs (temps de réponse, temps jusqu'au merge)
- **Bienveillance** envers les débutants (présence de `CONTRIBUTING.md`, PR de
  primo-contributeurs effectivement mergées)
- **Poids du dépôt** (pour cloner facilement avec une connexion limitée)

## ✨ Fonctionnalités

| Bloc | Description |
|------|-------------|
| **Agrégateur d'issues** | Issues `good first issue` / `help wanted` récupérées via l'API GitHub, filtrées par langage, niveau et statut d'assignation |
| **Tri par contraintes réelles** | Métriques calculées automatiquement : réactivité, bienveillance débutants, poids du dépôt |
| **Visibilité des contributeurs** | Profils publics, mur des contributeurs et classement filtrable par pays |

## 🛠️ Stack technique

- **Django 6** + **HTMX** (rendu serveur, 100 % Python — interactions sans SPA)
- **PostgreSQL** (prod) / **SQLite** (dev, zéro configuration)
- **Celery** + **Redis** pour l'ingestion périodique des issues
- **django-allauth** pour l'authentification **OAuth GitHub**
- **Tailwind CSS** avec un design system maison (voir [`DESIGN.md`](DESIGN.md))
- **WhiteNoise** + **Gunicorn** pour le déploiement

## 🚀 Démarrage rapide (local)

```bash
# 1. Cloner et créer l'environnement
git clone https://github.com/Ymax27/opentoall.git
cd opentoall
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Configurer l'environnement
cp .env.example .env        # éditez si besoin (SQLite par défaut, aucune config requise)

# 3. Base de données + données de démonstration
python manage.py migrate
python manage.py seed_demo  # remplit la base avec des données réalistes

# 4. Lancer
python manage.py runserver
```

Rendez-vous sur **http://localhost:8000** 🎉

> Astuce : `python manage.py createsuperuser` pour accéder à l'admin sur `/admin/`.

## 🐳 Démarrage avec Docker

```bash
cp .env.example .env
docker compose up --build
```

Le stack complet (web + PostgreSQL + Redis + worker Celery + beat) démarre, les
migrations s'appliquent automatiquement. L'app est disponible sur le port `8000`.

## 🔑 Configurer l'OAuth GitHub (optionnel en dev)

1. Créez une **OAuth App** sur https://github.com/settings/developers
   - *Homepage URL* : `http://localhost:8000`
   - *Authorization callback URL* : `http://localhost:8000/accounts/github/login/callback/`
2. Renseignez `GITHUB_CLIENT_ID` et `GITHUB_CLIENT_SECRET` dans `.env`.
3. Pour l'ingestion d'issues, créez un **Personal Access Token** (aucun scope
   nécessaire pour les données publiques) et renseignez `GITHUB_PAT`.

## 🔄 Ingestion des issues (données réelles GitHub)

GitHub limite son API (1000 résultats max par recherche, ~30 req/min, quota
horaire). OpenToAll **agrège donc périodiquement** les issues dans sa propre base
plutôt que d'interroger GitHub à chaque visite — d'où la pagination locale.

**Sans Celery** (le plus simple, il suffit d'un `GITHUB_PAT` dans `.env`) :

```bash
python manage.py fetch_issues                     # langages & labels par défaut, 2 pages
python manage.py fetch_issues --pages 5           # plus d'issues
python manage.py fetch_issues --languages Python Go --labels "good first issue"
```

**Avec Celery** (production) : le worker + beat rafraîchissent automatiquement
toutes les 6 h (voir `CELERY_BEAT_SCHEDULE`). `docker compose up` démarre le tout.

## ✅ Tests

```bash
pytest
```

## ☁️ Déploiement gratuit (Render + Neon)

Ce chemin ne nécessite **pas** Oracle ni Redis/Celery. Le site peut s’endormir
après inactivité (cold start ~30–60 s sur le plan free).

### 1. Neon (Postgres)

1. Crée un projet sur [neon.tech](https://neon.tech)
2. Copie la **connection string** (`DATABASE_URL`)

### 2. Secrets GitHub

- **OAuth App** : Homepage + callback = `https://TON-SERVICE.onrender.com`  
  Callback exact : `https://TON-SERVICE.onrender.com/accounts/github/login/callback/`
- **PAT** (`ghp_…`) pour l’ingestion

### 3. Render

1. [render.com](https://render.com) → New → **Blueprint** (fichier `render.yaml`)  
   **ou** New → **Web Service** → repo `Ymax27/opentoall` → Runtime **Docker** → plan **Free**
2. Variables d’environnement :

| Variable | Valeur |
|----------|--------|
| `DATABASE_URL` | string Neon |
| `SECRET_KEY` | long secret (ou généré par Blueprint) |
| `DEBUG` | `False` |
| `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` | OAuth App |
| `GITHUB_PAT` | token ingestion |
| `FETCH_ISSUES_TOKEN` | secret cron |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | crée le superuser au boot |
| `ADMIN_EMAIL` | optionnel |

`ALLOWED_HOSTS` / CSRF sont enrichis automatiquement via `RENDER_EXTERNAL_HOSTNAME`.

3. Deploy → ouvre l’URL `.onrender.com`

### 4. Admin + OAuth

- Mets à jour l’OAuth App avec l’URL Render réelle
- Admin → **Sites** → domain = `ton-service.onrender.com`

### 5. Ingestion + cron (remplace Celery)

Premier run (après deploy, via cron « Run now » ou navigateur) :

```text
https://TON-SERVICE.onrender.com/internal/fetch-issues/?token=FETCH_ISSUES_TOKEN&pages=1
```

Réponse attendue : **202** `{ "started": true }` (crawl en arrière-plan).

Puis sur [cron-job.org](https://cron-job.org) : même URL, toutes les **6 heures**.

> Ne lance **pas** `seed_demo` en production.

### 6. Mises à jour

Push sur `main` → Render rebuild automatique (si auto-deploy activé).

## 🤝 Contribuer

Les contributions sont les bienvenues ! Lisez le guide
[**CONTRIBUTING.md**](CONTRIBUTING.md) et le
[**Code de conduite**](CODE_OF_CONDUCT.md).

## 📄 Licence

Distribué sous licence **MIT**. Voir [`LICENSE`](LICENSE).
