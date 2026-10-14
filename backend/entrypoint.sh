#!/bin/sh
set -e

# In production server mode (gunicorn), ensure static assets are collected into STATIC_ROOT
if [ "$1" = "gunicorn" ]; then
    echo "[SkillSphere Entrypoint] Running collectstatic..."
    python manage.py collectstatic --noinput
fi

exec "$@"
