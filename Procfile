web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn config.wsgi --bind [::]:${PORT:-8000}
