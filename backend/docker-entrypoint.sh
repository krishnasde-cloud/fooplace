#!/bin/sh
set -eu

python manage.py migrate --noinput
python manage.py seedlistings
exec python manage.py runserver 0.0.0.0:8000
