#!/bin/sh
set -e

cd /app

if [ ! -f /app/data/.env ]; then
    echo "Creating .env file..."
    cp /app/.env.example /app/data/.env
    echo "Please fill in the .env file!"
    exit 1
fi

uv run manage.py migrate
uv run manage.py collectstatic --noinput
uv run daphne blendify.asgi:application -b 0.0.0.0 -p 8000