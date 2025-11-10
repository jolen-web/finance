#!/bin/bash
set -e

# Set default PORT if not provided
export PORT=${PORT:-5000}

# Create data directory if it doesn't exist (for SQLite in development)
mkdir -p /app/data

# Try to run database migrations with a timeout
echo "Running database migrations..."
timeout 30 python -m flask db upgrade || {
  migration_status=$?
  if [ $migration_status -eq 124 ]; then
    echo "Warning: Migration timed out after 30 seconds, continuing without migrations..."
  elif [ $migration_status -ne 0 ]; then
    echo "Warning: Migration failed with status $migration_status"
    echo "Attempting to resolve conflicting migration heads..."

    # Try to fix conflicting migration heads by updating the database directly
    python << 'PYEOF'
import os
from app import create_app, db
from sqlalchemy import text

try:
    app = create_app()
    with app.app_context():
        # Check if there are conflicting migration heads
        result = db.session.execute(text("SELECT version_num FROM alembic_version ORDER BY version_num"))
        current_versions = [row[0] for row in result]

        if len(current_versions) > 1:
            print(f"Found {len(current_versions)} migration heads. Consolidating...")
            print(f"Current versions: {current_versions}")

            # Delete all migration records
            db.session.execute(text("DELETE FROM alembic_version"))
            # Insert only the merge_branches head
            db.session.execute(text("INSERT INTO alembic_version (version_num) VALUES ('merge_branches')"))
            db.session.commit()

            print("Migration heads consolidated. Now trying upgrade again...")

            # Try upgrade again
            import subprocess
            result = subprocess.run(['python', '-m', 'flask', 'db', 'upgrade'],
                                  env=dict(os.environ, FLASK_APP='app'))
            if result.returncode == 0:
                print("Migration successful after consolidation!")
            else:
                print("Migration still failed after consolidation, continuing anyway...")
except Exception as e:
    print(f"Error resolving migration conflict: {e}")
    print("Continuing with application startup anyway...")
PYEOF
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
