#!/bin/bash
set -e

# Set default PORT if not provided
export PORT=${PORT:-5000}

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

# Check schema synchronization status (informational, non-blocking)
echo ""
echo "=========================================="
echo "SCHEMA SYNCHRONIZATION STATUS"
echo "=========================================="
if command -v python &> /dev/null; then
  timeout 10 python schema_sync_agent.py --check 2>&1 || {
    check_status=$?
    if [ $check_status -eq 124 ]; then
      echo "⏱ Schema check timed out (expected in ephemeral environments)"
    else
      echo "⚠ Schema check failed - see logs for details"
      echo "This is informational only; application will continue to run"
    fi
  }
else
  echo "ℹ Python not available for schema check"
fi
echo ""

echo "Starting application..."
exec gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --threads 8 --worker-class gevent --timeout 120 wsgi:app
