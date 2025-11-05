#!/usr/bin/env python3
"""
Cloud SQL Schema Sync Agent

Ensures Cloud SQL database has the same schema as local database.
Provides comparison, validation, and automatic sync capabilities.

Usage:
    # Check schema differences (read-only)
    python schema_sync_agent.py --check

    # Generate detailed report
    python schema_sync_agent.py --report

    # Sync migrations to Cloud SQL
    python schema_sync_agent.py --sync

    # Validate schemas match
    python schema_sync_agent.py --validate
"""

import os
import sys
import argparse
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, List
from dotenv import load_dotenv
from schema_compare import SchemaComparator


class SchemaSyncAgent:
    """Main agent for schema synchronization"""

    def __init__(self, local_db: str = None, cloud_db: str = None, verbose: bool = False):
        """
        Initialize schema sync agent

        Args:
            local_db: Local database URL
            cloud_db: Cloud SQL database URL
            verbose: Print debug information
        """
        load_dotenv()

        self.local_db = local_db or os.getenv('DATABASE_URL', 'sqlite:///data/finance.db')
        self.cloud_db = cloud_db or os.getenv('CLOUD_SQL_URL')
        self.verbose = verbose

        # Determine if we're in a git repo
        self.repo_root = Path(__file__).parent
        self.migrations_dir = self.repo_root / 'migrations' / 'versions'

        if not self.cloud_db:
            raise ValueError("CLOUD_SQL_URL environment variable not set")

    def check_differences(self) -> Dict:
        """Check for schema differences between local and Cloud SQL"""
        print("Comparing database schemas...")

        comparator = SchemaComparator(self.local_db, self.cloud_db, echo=self.verbose)
        report = comparator.get_report()

        print("\n" + "="*80)
        print("SCHEMA COMPARISON RESULTS")
        print("="*80)

        summary = report['summary']
        print(f"\nMissing tables (in local, not in Cloud SQL): {summary['missing_tables_count']}")
        print(f"Extra tables (in Cloud SQL, not in local): {summary['extra_tables_count']}")
        print(f"Tables with differences: {summary['tables_with_differences']}")
        print(f"Schemas in sync: {'✓ YES' if summary['schemas_match'] else '✗ NO'}")

        if not summary['schemas_match']:
            print("\nDifferences found:")
            comparator.print_report()

        return report

    def generate_report(self, output_file: str = None) -> str:
        """Generate detailed schema comparison report"""
        print("Generating schema comparison report...")

        comparator = SchemaComparator(self.local_db, self.cloud_db, echo=self.verbose)
        report = comparator.get_report()

        output_file = output_file or f"schema_report_{report['timestamp'].split('T')[0]}.json"

        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"Report saved to: {output_file}")
        comparator.print_report()

        return output_file

    def get_pending_migrations(self) -> List[str]:
        """Get list of pending migrations not applied to Cloud SQL"""
        print("Checking pending migrations...")

        try:
            # Get current revision in Cloud SQL
            comparator = SchemaComparator(self.local_db, self.cloud_db, echo=self.verbose)
            history = comparator.check_migration_history()

            if isinstance(history.get('source_versions'), list):
                source_latest = history['source_versions'][0] if history['source_versions'] else None
            else:
                source_latest = None

            if isinstance(history.get('target_versions'), list):
                target_latest = history['target_versions'][0] if history['target_versions'] else None
            else:
                target_latest = None

            if source_latest == target_latest:
                print("✓ All migrations are up to date")
                return []

            print(f"Source (local) latest: {source_latest}")
            print(f"Target (Cloud SQL) latest: {target_latest}")

            # In a real scenario, you'd track which migrations are pending
            # For now, we just report the difference
            pending = [source_latest] if source_latest and source_latest != target_latest else []
            return pending

        except Exception as e:
            print(f"Error checking migrations: {e}")
            return []

    def validate_schemas(self) -> bool:
        """Validate that schemas match exactly"""
        print("Validating schemas...")

        report = self.check_differences()
        summary = report['summary']

        if summary['schemas_match']:
            print("✓ Schemas are in perfect sync!")
            return True
        else:
            print("✗ Schemas do NOT match. Differences found:")
            print(f"  - Missing tables: {summary['missing_tables_count']}")
            print(f"  - Extra tables: {summary['extra_tables_count']}")
            print(f"  - Structure differences: {summary['tables_with_differences']}")
            return False

    def sync_schemas(self, dry_run: bool = True) -> bool:
        """
        Sync schemas by applying pending migrations

        Args:
            dry_run: If True, show what would be done without making changes

        Returns:
            True if successful, False otherwise
        """
        print("="*80)
        print("SCHEMA SYNCHRONIZATION")
        print("="*80)

        # First check differences
        report = self.check_differences()

        if report['summary']['schemas_match']:
            print("\n✓ Schemas are already in sync!")
            return True

        # Check for pending migrations
        pending = self.get_pending_migrations()

        if not pending:
            print("\n⚠ Schema differences detected but no pending migrations found.")
            print("This may require manual intervention or custom migrations.")
            return False

        if dry_run:
            print("\n[DRY RUN] The following migrations would be applied to Cloud SQL:")
            for migration in pending:
                print(f"  • {migration}")
            print("\nRun with --apply to actually apply migrations")
            return True
        else:
            print("\nApplying migrations to Cloud SQL...")
            try:
                # Set up Cloud SQL connection
                cloud_sql_url = os.getenv('CLOUD_SQL_URL')
                if not cloud_sql_url:
                    raise ValueError("CLOUD_SQL_URL not configured")

                # Run Flask migrations against Cloud SQL
                env = os.environ.copy()
                env['DATABASE_URL'] = cloud_sql_url

                result = subprocess.run(
                    ['flask', 'db', 'upgrade'],
                    env=env,
                    capture_output=True,
                    text=True,
                    cwd=str(self.repo_root)
                )

                if result.returncode == 0:
                    print("✓ Migrations applied successfully")
                    print(result.stdout)

                    # Validate the sync
                    if self.validate_schemas():
                        print("\n✓ Schema synchronization complete!")
                        return True
                    else:
                        print("\n⚠ Migrations applied but schema still differs")
                        return False
                else:
                    print("✗ Migration failed:")
                    print(result.stderr)
                    return False

            except Exception as e:
                print(f"✗ Error applying migrations: {e}")
                return False

    def get_status(self) -> Dict:
        """Get current sync status"""
        print("Getting synchronization status...")

        comparator = SchemaComparator(self.local_db, self.cloud_db, echo=self.verbose)
        report = comparator.get_report()

        summary = report['summary']

        status = {
            'timestamp': report['timestamp'],
            'synced': summary['schemas_match'],
            'issues': {
                'missing_tables': report['differences']['missing_tables'],
                'extra_tables': report['differences']['extra_tables'],
                'table_differences': list(report['differences']['table_differences'].keys())
            },
            'migration_history': report['differences'].get('migration_history', {})
        }

        return status


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Cloud SQL Schema Sync Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check for differences (no changes)
  python schema_sync_agent.py --check

  # Generate detailed report
  python schema_sync_agent.py --report

  # Apply pending migrations (with confirmation)
  python schema_sync_agent.py --sync --apply

  # Validate schemas match
  python schema_sync_agent.py --validate

  # Get current status
  python schema_sync_agent.py --status
        """
    )

    parser.add_argument(
        '--check',
        action='store_true',
        help='Check for schema differences (read-only)'
    )
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate detailed comparison report'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate that schemas match exactly'
    )
    parser.add_argument(
        '--sync',
        action='store_true',
        help='Synchronize schemas (requires --apply to make changes)'
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Actually apply changes (use with --sync)'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Get current synchronization status'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file for reports'
    )
    parser.add_argument(
        '--local-db',
        type=str,
        help='Local database URL'
    )
    parser.add_argument(
        '--cloud-db',
        type=str,
        help='Cloud SQL database URL'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    try:
        agent = SchemaSyncAgent(
            local_db=args.local_db,
            cloud_db=args.cloud_db,
            verbose=args.verbose
        )

        if args.check:
            agent.check_differences()

        elif args.report:
            agent.generate_report(args.output)

        elif args.validate:
            success = agent.validate_schemas()
            sys.exit(0 if success else 1)

        elif args.sync:
            if args.apply:
                success = agent.sync_schemas(dry_run=False)
                sys.exit(0 if success else 1)
            else:
                agent.sync_schemas(dry_run=True)
                print("\nUse --apply flag to apply these changes")

        elif args.status:
            status = agent.get_status()
            print("\nSYNCHRONIZATION STATUS:")
            print(json.dumps(status, indent=2, default=str))

        else:
            # Default: show check
            agent.check_differences()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
