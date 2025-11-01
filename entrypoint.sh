#!/bin/bash
set -e

echo "Running database migrations..."
flask db upgrade

echo "Migrations complete. Starting application..."
exec gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --threads 8 --worker-class gevent --timeout 120 wsgi:app
