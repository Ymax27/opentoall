<div align="center">

<img src="static/img/logo.png" width="72" alt="OpenToAll logo" />

# OpenToAll

**L'open source, ouvert à tous.**

Plateforme de découverte et de valorisation de la contribution open source,
pensée pour les développeurs africains.

[Signaler un bug](https://github.com/Ymax27/opentoall/issues) ·
[Proposer une fonctionnalité](https://github.com/Ymax27/opentoall/issues) ·
[Contribuer](CONTRIBUTING.md)

</div>

---

## Pourquoi ?

Des agrégateurs de « good first issues » existent déjà. OpenToAll ajoute ce qui
manquait pour beaucoup de contributeurs africains :

- **Réactivité** des mainteneurs
- **Bienveillance** envers les débutants (`CONTRIBUTING.md`, score débutant)
- **Poids du dépôt** (clone réaliste avec une connexion limitée)
- **Visibilité** : profils + classement par pays

## Fonctionnalités

| Bloc | Description |
|------|-------------|
| **Agrégateur** | Issues `good first issue` / `help wanted` via l’API GitHub, filtrées (langage, niveau, non assignées) |
| **Contraintes réelles** | Réactivité, bienveillance, poids du clone |
| **Profils & classement** | Profil public + leaderboard alimentés par les **PR mergées** GitHub du compte connecté |

## Comment marche le classement ? (important)

Le bouton **« Ouvre sur GitHub »** ouvre seulement l’issue sur GitHub. Il **ne
crée pas** une contribution sur OpenToAll.

Le flux réel aujourd’hui :

1. Tu te **connectes avec GitHub** (OAuth).
2. OpenToAll enregistre ton profil (`login`, avatar, bio…).
3. À la connexion, la plateforme interroge l’API GitHub pour tes **PR publiques
   mergées** (`author:toi type:pr is:merged`) et les enregistre dans la table
   `Contribution`.
4. Le **classement** compte ces contributions par utilisateur / pays.

Donc : merge une PR sur GitHub → reconnecte-toi (ou attends la prochaine sync à
la connexion) → tu apparais / montes dans le classement.

> Ce n’est **pas** un webhook temps réel ni un tracking du clic « Contribuer ».
> C’est une sync des PR déjà mergées liées à ton compte GitHub.

## Stack

- Django 6 + HTMX + templates
- PostgreSQL (prod) / SQLite (dev)
- Celery + Redis (optionnel ; en prod légère : cron + `/internal/fetch-issues/`)
- django-allauth (**OAuth App** GitHub — pas une GitHub App)
- Tailwind (CDN) + WhiteNoise + Gunicorn
- Déploiement typique : **Fly.io** + **Neon** (Postgres)

## Démarrage local

```bash
git clone https://github.com/Ymax27/opentoall.git
cd opentoall
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_demo   # démo UI uniquement — pas pour la prod
python manage.py runserver
```

→ http://localhost:8000

Docker (web + Postgres + Redis + Celery) :

```bash
cp .env.example .env
docker compose up --build
```

## Auth GitHub : OAuth App (pas GitHub App)

django-allauth attend une **OAuth App** classique :

[GitHub → Settings → Developer settings → OAuth Apps](https://github.com/settings/developers)

| Champ | Local | Prod (exemple Fly) |
|-------|-------|--------------------|
| Homepage URL | `http://localhost:8000` | `https://opentoall.fly.dev` |
| Authorization callback URL | `http://localhost:8000/accounts/github/login/callback/` | `https://opentoall.fly.dev/accounts/github/login/callback/` |

Puis dans les secrets / `.env` :

- `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` → ceux de l’**OAuth App**
- `GITHUB_PAT` → Personal Access Token pour l’**ingestion** d’issues (données publiques)

### Pourquoi « GitHub App » casse souvent le login

Une **GitHub App** (onglet *GitHub Apps*) n’est **pas** interchangeable avec une
OAuth App pour ce projet. Client ID / secret d’une GitHub App, callbacks
d’installation, ou mauvais type d’app → erreurs OAuth (`redirect_uri_mismatch`,
`incorrect_client_credentials`, boucle de login, etc.).

**À faire :** créer / utiliser une **OAuth App**, pas une GitHub App.

### Checklist login en prod (à vérifier une par une)

1. L’app GitHub est bien une **OAuth App** (pas GitHub App).
2. Callback URL **exacte** (https, domaine, `/accounts/github/login/callback/`, slash final).
3. `GITHUB_CLIENT_ID` et `GITHUB_CLIENT_SECRET` sur Fly = ceux de **cette** OAuth App.
4. Django **Sites** (`/admin/` → Sites) : domaine = `opentoall.fly.dev` (sans `https://`).
5. Pas de doublon contradictoire : si une entrée *Social applications* existe dans
   l’admin allauth, ses credentials doivent être **identiques** aux secrets Fly
   (sinon allauth peut utiliser les mauvais).
6. `DEBUG=False`, cookies sécurisés, site servi en **HTTPS**.
7. Après fix : vider cookies du site / refaire un login en navigation privée.

## Ingestion des issues (vraies données)

```bash
# Local (GITHUB_PAT requis)
python manage.py fetch_issues --pages 1
python manage.py fetch_issues --pages 2 --languages Python Go JavaScript TypeScript Rust Java
```

En prod (Fly), sans Celery :

```text
https://opentoall.fly.dev/internal/fetch-issues/?token=FETCH_ISSUES_TOKEN&pages=1
```

Réponse attendue : **202**. Relancer si le rate limit GitHub a stoppé après le
premier langage (ex. seulement Python dans les filtres) — la progression est
sauvegardée, un second run complète les autres langages.

> Ne lance **jamais** `seed_demo` en production (liens GitHub factices / issues fermées).

## Déploiement (Fly + Neon) — résumé

1. Neon → `DATABASE_URL`
2. Secrets Fly : `SECRET_KEY`, `DATABASE_URL`, `GITHUB_CLIENT_ID`,
   `GITHUB_CLIENT_SECRET`, `GITHUB_PAT`, `FETCH_ISSUES_TOKEN`, `DEBUG=False`,
   `USE_REDIS_CACHE=0` (tant qu’il n’y a pas de Redis distant)
3. `fly deploy`
4. Configurer l’OAuth App + Site Django (checklist ci-dessus)
5. Premier `fetch-issues` + cron toutes les 6 h (cron-job.org)

Détails machines / `fly.toml` : voir le fichier à la racine du repo.

## Tests

```bash
pytest
```

## Contribuer

Voir [CONTRIBUTING.md](CONTRIBUTING.md) et le [Code de conduite](CODE_OF_CONDUCT.md).

## Licence

MIT — voir [`LICENSE`](LICENSE).
