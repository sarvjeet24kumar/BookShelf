#!/bin/bash

# entrypoint.sh — Routes to the correct service based on $SERVICE env variable
set -e

# Standard Django commands for the 'web' service
if [ "$SERVICE" = "web" ]; then
    echo "[entrypoint] Running database migrations..."
    uv run python manage.py migrate --noinput

    echo "[entrypoint] Seeding super admin..."
    uv run python manage.py create_superadmin

    echo "[entrypoint] Collecting static files..."
    uv run python manage.py collectstatic --noinput

    echo "[entrypoint] Starting Gunicorn..."
    exec uv run gunicorn config.wsgi:application \
      --bind 0.0.0.0:8000 \
      --workers 3 \
      --timeout 120 \
      --log-level info \
      --access-logfile - \
      --error-logfile -

elif [ "$SERVICE" = "celery_worker" ]; then
    echo "[entrypoint] Starting Celery Worker..."
    exec uv run celery -A config worker --loglevel=info

elif [ "$SERVICE" = "celery_beat" ]; then
    echo "[entrypoint] Starting Celery Beat..."
    exec uv run celery -A config beat --loglevel=info

else
    # Default fallback: Execute whatever was passed to the container
    echo "[entrypoint] Executing default command: $@"
    exec "$@"
fi
