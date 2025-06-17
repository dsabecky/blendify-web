#!/bin/sh
set -e

cd /app

uv run manage.py migrate
uv run manage.py collectstatic --noinput
uv run daphne blendify.asgi:application -b 0.0.0.0 -p 8000