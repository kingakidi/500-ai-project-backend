#!/bin/bash

set -e

echo "Waiting for database..."
python manage.py migrate --noinput

echo "Starting server..."
exec uvicorn config.asgi:application --host 0.0.0.0 --port 8000

