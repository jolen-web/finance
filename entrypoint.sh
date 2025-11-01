#!/bin/bash
set -e

# Try to run database migrations with a timeout
echo "Running database migrations..."
timeout 30 python -m flask db upgrade || {
  migration_status=$?
  if [ $migration_status -eq 124 ]; then
    echo "Warning: Migration timed out after 30 seconds, continuing without migrations..."
  elif [ $migration_status -ne 0 ]; then
    echo "Warning: Migration failed with status $migration_status, continuing anyway..."
  fi
}

echo "Starting application..."
exec gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --threads 8 --worker-class gevent --timeout 120 wsgi:app
