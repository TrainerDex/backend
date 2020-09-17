![Django Tests, Migrations, & System Check](https://github.com/TrainerDex/backend/workflows/Django%20Tests,%20Migrations,%20&%20System%20Check/badge.svg)
![Lint & Style Check](https://github.com/TrainerDex/backend/workflows/Lint%20&%20Style%20Check/badge.svg)
![Discord](https://img.shields.io/discord/364313717720219651?logo=discord)
![Repo Size](https://img.shields.io/github/repo-size/TrainerDex/backend?logo=github)
![Code Size](https://img.shields.io/github/languages/code-size/TrainerDex/backend?logo=python)
![Status](https://img.shields.io/website?url=https%3A%2F%2Fbeta.trainerdex.co.uk)

## Environment setup
```
source env/bin/activate
```

### Hot-reloads for development
```
python manage.py runserver
```

### Local Production
```
python manage.py collectstatic --clear
python manage.py migrate
python manage.py compilemessages
```
