#!/bin/bash

# entrypoint.sh — Routes to the correct service based on $SERVICE env variable
set -e
SERVICE_TYPE=${SERVICE:-$1}
SERVICE_TYPE=${SERVICE_TYPE:-web}

echo "[entrypoint] Service: $SERVICE_TYPE"
# Standard Django commands for the 'web' service
if [ "$SERVICE_TYPE" = "web" ]; then
    if [ "$RUN_MIGRATIONS" = "true" ]; then
        echo "[entrypoint] Running database migrations..."
        uv run python manage.py migrate --noinput
    fi

    echo "[entrypoint] Seeding super admin..."
    uv run python manage.py create_superadmin

    echo "[entrypoint] Collecting static files..."
    uv run python manage.py collectstatic --noinput

    echo "[entrypoint] Starting Gunicorn with New Relic..."
    export NEW_RELIC_CONFIG_FILE=/app/newrelic.ini
    exec newrelic-admin run-program gunicorn config.wsgi:application \
      --bind 0.0.0.0:8000 \
      --workers 3 \
      --timeout 120 \
      --log-level info \
      --access-logfile - \
      --error-logfile -

elif [ "$SERVICE_TYPE" = "celery_worker" ]; then
    echo "[entrypoint] Starting Celery Worker with New Relic..."
    export NEW_RELIC_CONFIG_FILE=/app/newrelic.ini
    exec newrelic-admin run-program celery -A config worker --loglevel=info

elif [ "$SERVICE_TYPE" = "celery_beat" ]; then
    echo "[entrypoint] Starting Celery Beat with New Relic..."
    export NEW_RELIC_CONFIG_FILE=/app/newrelic.ini
    exec newrelic-admin run-program celery -A config beat --loglevel=info

else
    # Default fallback: Execute whatever was passed to the container
    echo "[entrypoint] Executing default command: $@"
    exec "$@"
fi
