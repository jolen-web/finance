# Schema Sync Agent

Ensures Cloud SQL database has the same schema as the local development database. Detects schema drift, validates synchronization, and applies pending migrations safely.

## Purpose

The Schema Sync Agent prevents deployment failures caused by schema mismatches between local development and Cloud SQL production databases. It provides:

- **Schema Comparison**: Detect all differences (missing tables, columns, constraints, indexes)
- **Safe Synchronization**: Apply migrations with dry-run mode by default
- **Automated Validation**: Verify schemas are perfectly synchronized
- **Detailed Reports**: Generate JSON and human-readable difference reports
- **Migration Tracking**: Ensure migration versions are aligned

## When to Use

Use the Schema Sync Agent:

1. **Before Deployments**: Verify schemas match before pushing to production
2. **After Migrations**: Confirm migrations were successfully applied to Cloud SQL
3. **In CI/CD Pipelines**: Automatically validate schema synchronization
4. **Debugging Schema Issues**: Generate detailed reports of differences
5. **Database Maintenance**: Track schema drift over time

## Quick Start

### Check for Differences

```bash
# Local terminal
python schema_sync_agent.py --check

# Output:
# SCHEMA COMPARISON RESULTS
# Missing tables (in local, not in Cloud SQL): 0
# Schemas in sync: ✓ YES
```

### Validate Schemas Match

```bash
# Exit code 0 if synced, 1 if not (useful for CI/CD)
python schema_sync_agent.py --validate
```

### Generate Detailed Report

```bash
# Creates JSON file with complete schema analysis
python schema_sync_agent.py --report --output schema_debug.json
```

### Apply Pending Migrations

```bash
# Dry-run (shows what would happen)
python schema_sync_agent.py --sync

# Apply changes
python schema_sync_agent.py --sync --apply
```

## Technical Details

### Architecture

**Core Components:**

- `schema_compare.py` - SQLAlchemy-based schema introspection and comparison
- `schema_sync_agent.py` - CLI interface and orchestration
- Uses Alembic migration tracking from existing Flask-Migrate setup

**Comparison Capabilities:**

- ✓ Table existence and structure
- ✓ Column names, data types, nullability
- ✓ Primary key definitions
- ✓ Foreign key constraints
- ✓ Unique constraints
- ✓ Indexes (including multi-column)
- ✓ Migration version history

### How It Works

1. **Introspection**: Connects to both databases and inspects schema using SQLAlchemy
2. **Comparison**: Identifies all structural differences between databases
3. **Analysis**: Categorizes differences (missing tables, column mismatches, etc.)
4. **Reporting**: Generates human-readable and JSON reports
5. **Sync**: Optionally applies pending migrations to Cloud SQL using Flask-Migrate

### Database Support

- **Local**: SQLite, PostgreSQL
- **Cloud SQL**: PostgreSQL (primary), MySQL (with limitations)
- **Comparison**: Works across different database types

## Configuration

### Environment Variables

```bash
# Required
DATABASE_URL=sqlite:///data/finance.db        # Local database
CLOUD_SQL_URL=postgresql://...                # Cloud SQL (remote or proxy)

# Optional
VERBOSE=true                                   # Enable debug output
```

### Setup

```bash
# 1. Ensure databases are accessible
# Local: SQLite or PostgreSQL (Docker)
docker-compose up -d

# Cloud SQL: Set up proxy if remote
cloud_sql_proxy -instances=jinolen:us-central1:finance-db=tcp:5432

# 2. Configure environment
export DATABASE_URL=sqlite:///data/finance.db
export CLOUD_SQL_URL=postgresql://postgres:password@localhost:5432/finance

# 3. Run agent
python schema_sync_agent.py --check
```

## Use Cases

### Use Case 1: Pre-Deployment Verification

```bash
#!/bin/bash
# pre-deploy.sh

echo "Verifying schemas are synchronized..."
python schema_sync_agent.py --validate

if [ $? -ne 0 ]; then
  echo "ERROR: Schemas don't match! Fix before deploying."
  exit 1
fi

echo "✓ Schemas verified. Safe to deploy."
./deploy.sh
```

### Use Case 2: Automated CI/CD Check

```yaml
# GitHub Actions
- name: Validate Schema Sync
  env:
    CLOUD_SQL_URL: ${{ secrets.CLOUD_SQL_URL }}
  run: |
    python schema_sync_agent.py --validate
    # Fails workflow if schemas don't match
```

### Use Case 3: Post-Migration Verification

```bash
#!/bin/bash
# After running migrations locally...

# Apply to Cloud SQL
python schema_sync_agent.py --sync --apply

# Verify success
python schema_sync_agent.py --validate
echo "✓ Migration synced to Cloud SQL"
```

### Use Case 4: Schema Drift Detection

```bash
#!/bin/bash
# Weekly schema audit

python schema_sync_agent.py --report \
  --output "reports/schema_$(date +%Y-%m-%d).json"

# Parse report for issues
jq '.summary' reports/schema_*.json
```

## Command Reference

### `--check`
Compare schemas between local and Cloud SQL (read-only)

```bash
python schema_sync_agent.py --check
```

**Output**: Summary of missing/extra tables, structural differences

### `--report`
Generate detailed JSON report of all schema differences

```bash
python schema_sync_agent.py --report
python schema_sync_agent.py --report --output custom.json
```

**Output**: JSON file with complete schema analysis

### `--validate`
Verify schemas are perfectly synchronized

```bash
python schema_sync_agent.py --validate
```

**Exit Code**: 0 (synced), 1 (differences found)

### `--sync` with `--apply`
Apply pending migrations to Cloud SQL

```bash
# Dry-run (safe, shows what would happen)
python schema_sync_agent.py --sync

# Apply changes (requires --apply flag)
python schema_sync_agent.py --sync --apply
```

**Safety**: Requires explicit `--apply` flag; defaults to dry-run

### `--status`
Get current synchronization status as JSON

```bash
python schema_sync_agent.py --status
```

**Output**: JSON with sync status and migration history

### Options

- `--local-db URL` - Override local database URL
- `--cloud-db URL` - Override Cloud SQL URL
- `--output FILE` - Save report to specific file
- `-v, --verbose` - Print detailed debug output

## Understanding Output

### Check Command Output Example

```
Missing tables (in local, not in Cloud SQL): 1
  • feedback

Tables with differences: 2
  accounts:
    Missing columns:
      • updated_at (DateTime)
  transactions:
    Column type changes:
      • amount: Float → Numeric

Schemas in sync: ✗ NO
```

### Status JSON Output

```json
{
  "timestamp": "2025-11-01T21:30:00",
  "synced": false,
  "issues": {
    "missing_tables": ["feedback"],
    "extra_tables": [],
    "table_differences": ["accounts", "transactions"]
  },
  "migration_history": {
    "source_versions": ["add_feedback", "e6dc16bff2b7"],
    "target_versions": ["e6dc16bff2b7"],
    "synced": false
  }
}
```

## Troubleshooting

### Connection Issues

```bash
# Verify local database is accessible
sqlite3 data/finance.db ".tables"
# or
psql -h localhost -U postgres -d finance_db

# Verify Cloud SQL is accessible
psql -h 127.0.0.1 -U postgres -d finance
```

### Permission Errors

```bash
# Ensure user has schema introspection permissions
GRANT CONNECT ON DATABASE finance TO postgres;
GRANT USAGE ON SCHEMA public TO postgres;
```

### Schema Differences Not Being Applied

```bash
# Check if migrations are pending
flask db current
flask db heads

# If migrations are pending, apply directly
export DATABASE_URL=postgresql://...cloud-sql...
flask db upgrade
```

## Integration Examples

### GitHub Actions Workflow

```yaml
name: Schema Validation
on: [pull_request, push]

jobs:
  schema:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Check schema sync
        env:
          CLOUD_SQL_URL: ${{ secrets.CLOUD_SQL_URL }}
        run: python schema_sync_agent.py --validate
```

### Cloud Run Scheduled Job

```bash
# Create scheduled schema check
gcloud run jobs create schema-sync-check \
  --image gcr.io/jinolen/finance-tracker:latest \
  --region us-central1 \
  --command python \
  --args "schema_sync_agent.py,--validate"

# Schedule with Cloud Scheduler
gcloud scheduler jobs create app-engine schema-check \
  --schedule="0 2 * * *" \
  --http-method POST \
  --uri "https://..."
```

## Performance

**Typical execution times:**

- Schema check: 1-2 seconds
- Detailed report: 2-3 seconds
- Validation: 1-2 seconds
- Migration application: Varies by migration size (10-30 seconds)

For large databases (100+ tables):
- Comparison: 3-5 seconds
- Full synchronization: 15-45 seconds

## Safety Features

- **Read-only by default**: `--check` and `--report` don't modify anything
- **Explicit apply flag**: `--sync` requires `--apply` to make changes
- **Dry-run mode**: Shows what would be done before applying
- **Validation**: Re-checks after applying to confirm success
- **No destructive operations**: Never drops tables/columns without user confirmation

## Files

- `schema_compare.py` - Core comparison logic
- `schema_sync_agent.py` - CLI interface
- `SCHEMA_SYNC.md` - Full documentation
- Generated reports: `schema_report_*.json`

## Related Tools

- Flask-Migrate: Alembic wrapper for managing migrations
- Alembic: Database migration tool (underlying system)
- SQLAlchemy: ORM and introspection (used for schema analysis)

## Limitations

1. **SQLite ↔ PostgreSQL**: Some features are database-specific
2. **Custom Constraints**: Some database-specific constraints may not be detected
3. **Permissions**: Requires SELECT access to system tables
4. **Performance**: Very large databases may take longer
5. **Data Changes**: Schema tool doesn't handle data migration, only schema

## Future Enhancements

- Auto-generate migration fixes
- HTML report generation with visual diffs
- Slack/email notifications for schema drift
- Per-table synchronization
- Rollback/downgrade support
- Performance profiling per table

## Support

For issues or questions:

1. Run with `--verbose` flag for detailed output
2. Check generated JSON reports
3. Review the full documentation in `SCHEMA_SYNC.md`
4. Check Flask-Migrate and Alembic documentation

---

**Version**: 1.0
**Status**: Production Ready
**Last Updated**: November 1, 2025
