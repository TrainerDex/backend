![Django Lint & CI (Development)](https://github.com/TrainerDex/backend/workflows/Django%20Lint%20&%20CI%20(Development)/badge.svg?branch=develop)

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
