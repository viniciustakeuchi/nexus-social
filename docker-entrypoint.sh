#!/bin/sh
set -e

python manage.py migrate --noinput

if [ "${POPULAR_DEMO:-false}" = "true" ]; then
    python manage.py popular_demo
fi

exec "$@"
