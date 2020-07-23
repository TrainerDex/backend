![Django Lint & CI (Development)](https://github.com/TrainerDex/backend/workflows/Django%20Lint%20&%20CI%20(Development)/badge.svg?branch=develop)

## Environment setup
```
source env/bin/activate
```

### Hot-reloads for development
```
python manage.py runserver
```

### Compiles for production
```
python manage.py makemessages --no-wrap --ignore=env/* -l en-GB -l de -l es -l fr -l it -l ja -l ko -l pt-BR -l zh-TW --keep-pot
```

### Local Production
```
python manage.py collectstatic --clear
python manage.py migrate
python manage.py compilemessages
```
