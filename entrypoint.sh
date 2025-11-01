#!/bin/bash
set -e

# Skip automatic migrations - database is already initialized with all required schema
echo "Skipping migrations (database already initialized)..."

echo "Starting application..."
exec gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --threads 8 --worker-class gevent --timeout 120 wsgi:app
