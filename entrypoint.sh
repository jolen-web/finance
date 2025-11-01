#!/bin/bash
set -e

# Run database migrations to ensure schema is up to date
echo "Running database migrations..."
python -m flask db upgrade

echo "Starting application..."
exec gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --threads 8 --worker-class gevent --timeout 120 wsgi:app
