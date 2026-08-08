# Contribuer à OpenToAll

Merci de vouloir contribuer ! 🎉 OpenToAll est un projet communautaire : chaque
contribution, petite ou grande, compte.

## Comment contribuer

1. **Trouvez une issue** — regardez les issues étiquetées
   [`good first issue`](https://github.com/OpenToAllRepo/opentoall/labels/good%20first%20issue)
   ou [`help wanted`](https://github.com/OpenToAllRepo/opentoall/labels/help%20wanted).
2. **Ouvrez une discussion** — commentez l'issue pour signaler que vous la prenez,
   afin d'éviter les doublons.
3. **Forkez** le dépôt et créez une branche : `git checkout -b feat/ma-fonctionnalite`.
4. **Développez** en suivant les conventions ci-dessous.
5. **Testez** : `pytest` doit passer.
6. **Ouvrez une Pull Request** claire, liée à l'issue concernée.

## Mettre en place l'environnement

Voir la section « Démarrage rapide » du [README](README.md). En résumé :

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

## Conventions de code

- **Python** : suivez la [PEP 8](https://peps.python.org/pep-0008/). Fonctions et
  variables explicites, docstrings pour les modules et services.
- **Templates** : respectez le design system décrit dans [`DESIGN.md`](DESIGN.md)
  (couleurs sémantiques, `rounded-xl`, icônes Material Symbols).
- **Commits** : format [Conventional Commits](https://www.conventionalcommits.org/)
  recommandé (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`…).
- **Tests** : ajoutez un test pour toute nouvelle logique métier.

## Structure du projet

```
config/          # Réglages Django, Celery, URLs racine
core/
  ├── models.py          # Issue, Profile, Contribution
  ├── views.py           # Vues (home, explore, détail, profil, classement)
  ├── services/          # Client GitHub + calcul des métriques
  ├── tasks.py           # Tâches Celery (ingestion périodique)
  ├── templates/         # Templates Django + design system
  └── management/        # Commande seed_demo
```

## Signaler un bug ou proposer une idée

Ouvrez une [issue](https://github.com/OpenToAllRepo/opentoall/issues) en décrivant :
- ce que vous attendiez,
- ce qui s'est passé,
- les étapes pour reproduire (pour un bug).

## Code de conduite

Ce projet adhère au [Code de conduite](CODE_OF_CONDUCT.md). En participant, vous
vous engagez à le respecter.
