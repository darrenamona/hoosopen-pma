release: python manage.py migrate && python manage.py loaddata hoosopen/fixtures/initial.json
web: gunicorn mysite.wsgi