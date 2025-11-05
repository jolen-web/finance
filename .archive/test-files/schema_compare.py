"""
Schema Comparison Tool for Finance Tracker

Compares database schemas between two databases (local and Cloud SQL)
and provides detailed differences report.
"""

import sys
from sqlalchemy import inspect, MetaData, create_engine, text
from typing import Dict, List, Tuple, Set
import json
from datetime import datetime


class SchemaComparator:
    """Compare schemas between two databases"""

    def __init__(self, source_url: str, target_url: str, echo: bool = False):
        """
        Initialize schema comparator

        Args:
            source_url: SQLAlchemy connection string for source DB (local)
            target_url: SQLAlchemy connection string for target DB (Cloud SQL)
            echo: Print SQL statements if True
        """
        self.source_engine = create_engine(source_url, echo=echo)
        self.target_engine = create_engine(target_url, echo=echo)

        self.source_inspector = inspect(self.source_engine)
        self.target_inspector = inspect(self.target_engine)

        self.differences = {
            'missing_tables': [],
            'extra_tables': [],
            'table_differences': {},
            'migration_history': {}
        }

    def get_table_names(self, inspector) -> Set[str]:
        """Get all table names from database"""
        return set(inspector.get_table_names())

    def get_table_structure(self, inspector, table_name: str) -> Dict:
        """Get detailed structure of a table"""
        structure = {
            'columns': {},
            'primary_key': None,
            'foreign_keys': [],
            'indexes': [],
            'constraints': []
        }

        # Get columns
        for column in inspector.get_columns(table_name):
            col_name = column['name']
            structure['columns'][col_name] = {
                'type': str(column['type']),
                'nullable': column['nullable'],
                'default': column['default'],
                'autoincrement': column.get('autoincrement', False)
            }

        # Get primary key
        pk = inspector.get_pk_constraint(table_name)
        if pk and pk['constrained_columns']:
            structure['primary_key'] = pk['constrained_columns']

        # Get foreign keys
        for fk in inspector.get_foreign_keys(table_name):
            structure['foreign_keys'].append({
                'name': fk.get('name'),
                'constrained_columns': fk['constrained_columns'],
                'referred_table': fk['referred_table'],
                'referred_columns': fk['referred_columns']
            })

        # Get indexes
        for idx in inspector.get_indexes(table_name):
            structure['indexes'].append({
                'name': idx['name'],
                'unique': idx['unique'],
                'columns': idx['column_names']
            })

        # Get constraints
        for constraint in inspector.get_unique_constraints(table_name):
            structure['constraints'].append({
                'name': constraint.get('name'),
                'columns': constraint['column_names']
            })

        return structure

    def compare_tables(self) -> None:
        """Compare table definitions between source and target"""
        source_tables = self.get_table_names(self.source_inspector)
        target_tables = self.get_table_names(self.target_inspector)

        # Find missing tables (in source but not in target)
        self.differences['missing_tables'] = list(source_tables - target_tables)

        # Find extra tables (in target but not in source)
        self.differences['extra_tables'] = list(target_tables - source_tables)

        # Compare common tables
        common_tables = source_tables & target_tables
        for table_name in sorted(common_tables):
            source_struct = self.get_table_structure(self.source_inspector, table_name)
            target_struct = self.get_table_structure(self.target_inspector, table_name)

            diff = self._compare_table_structures(table_name, source_struct, target_struct)
            if diff:
                self.differences['table_differences'][table_name] = diff

    def _compare_table_structures(self, table_name: str, source: Dict, target: Dict) -> Dict:
        """Compare two table structures"""
        diff = {
            'missing_columns': [],
            'extra_columns': [],
            'column_changes': {},
            'primary_key_diff': False,
            'foreign_key_diff': False,
            'index_diff': False
        }

        source_cols = set(source['columns'].keys())
        target_cols = set(target['columns'].keys())

        # Missing columns
        for col in source_cols - target_cols:
            diff['missing_columns'].append({
                'name': col,
                'type': source['columns'][col]['type'],
                'nullable': source['columns'][col]['nullable']
            })

        # Extra columns
        for col in target_cols - source_cols:
            diff['extra_columns'].append({
                'name': col,
                'type': target['columns'][col]['type']
            })

        # Column type changes
        for col in source_cols & target_cols:
            source_type = source['columns'][col]['type']
            target_type = target['columns'][col]['type']

            if source_type != target_type:
                diff['column_changes'][col] = {
                    'source_type': source_type,
                    'target_type': target_type
                }

        # Check primary key
        if source['primary_key'] != target['primary_key']:
            diff['primary_key_diff'] = True
            diff['primary_key'] = {
                'source': source['primary_key'],
                'target': target['primary_key']
            }

        # Check foreign keys
        if source['foreign_keys'] != target['foreign_keys']:
            diff['foreign_key_diff'] = True
            diff['foreign_keys'] = {
                'source': source['foreign_keys'],
                'target': target['foreign_keys']
            }

        # Check indexes
        if source['indexes'] != target['indexes']:
            diff['index_diff'] = True
            diff['indexes'] = {
                'source': source['indexes'],
                'target': target['indexes']
            }

        # Return only if there are differences
        return diff if any([
            diff['missing_columns'],
            diff['extra_columns'],
            diff['column_changes'],
            diff['primary_key_diff'],
            diff['foreign_key_diff'],
            diff['index_diff']
        ]) else None

    def check_migration_history(self) -> Dict:
        """Check Alembic migration history alignment"""
        history = {}

        try:
            with self.source_engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT version_num, installed_on FROM alembic_version ORDER BY installed_on DESC LIMIT 5"
                ))
                source_versions = [row[0] for row in result.fetchall()]
                history['source_versions'] = source_versions
        except Exception as e:
            history['source_versions'] = f"Error reading source: {str(e)}"

        try:
            with self.target_engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT version_num, installed_on FROM alembic_version ORDER BY installed_on DESC LIMIT 5"
                ))
                target_versions = [row[0] for row in result.fetchall()]
                history['target_versions'] = target_versions
        except Exception as e:
            history['target_versions'] = f"Error reading target: {str(e)}"

        # Check if versions match
        if isinstance(history.get('source_versions'), list) and isinstance(history.get('target_versions'), list):
            source_latest = history['source_versions'][0] if history['source_versions'] else None
            target_latest = history['target_versions'][0] if history['target_versions'] else None
            history['synced'] = source_latest == target_latest

        self.differences['migration_history'] = history
        return history

    def get_report(self) -> Dict:
        """Get complete comparison report"""
        self.compare_tables()
        self.check_migration_history()

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'source_database': str(self.source_engine.url).split('@')[1] if '@' in str(self.source_engine.url) else 'local',
            'target_database': str(self.target_engine.url).split('@')[1] if '@' in str(self.target_engine.url) else 'cloud',
            'differences': self.differences,
            'summary': {
                'missing_tables_count': len(self.differences['missing_tables']),
                'extra_tables_count': len(self.differences['extra_tables']),
                'tables_with_differences': len(self.differences['table_differences']),
                'schemas_match': (
                    len(self.differences['missing_tables']) == 0 and
                    len(self.differences['extra_tables']) == 0 and
                    len(self.differences['table_differences']) == 0
                )
            }
        }

    def print_report(self) -> None:
        """Print human-readable comparison report"""
        report = self.get_report()

        print("\n" + "="*80)
        print("DATABASE SCHEMA COMPARISON REPORT")
        print("="*80)
        print(f"Generated: {report['timestamp']}")
        print(f"Source: {report['source_database']}")
        print(f"Target: {report['target_database']}")
        print()

        summary = report['summary']
        print("SUMMARY:")
        print(f"  Missing tables (in source, not in target): {summary['missing_tables_count']}")
        print(f"  Extra tables (in target, not in source): {summary['extra_tables_count']}")
        print(f"  Tables with structural differences: {summary['tables_with_differences']}")
        print(f"  Schemas match: {'✓ YES' if summary['schemas_match'] else '✗ NO'}")
        print()

        # Missing tables
        if self.differences['missing_tables']:
            print("MISSING TABLES (need to create in Cloud SQL):")
            for table in self.differences['missing_tables']:
                print(f"  • {table}")
            print()

        # Extra tables
        if self.differences['extra_tables']:
            print("EXTRA TABLES (exist in Cloud SQL but not locally):")
            for table in self.differences['extra_tables']:
                print(f"  • {table}")
            print()

        # Table differences
        if self.differences['table_differences']:
            print("TABLE STRUCTURE DIFFERENCES:")
            for table_name, diff in self.differences['table_differences'].items():
                print(f"\n  {table_name}:")

                if diff.get('missing_columns'):
                    print(f"    Missing columns:")
                    for col in diff['missing_columns']:
                        print(f"      • {col['name']} ({col['type']}, nullable={col['nullable']})")

                if diff.get('extra_columns'):
                    print(f"    Extra columns:")
                    for col in diff['extra_columns']:
                        print(f"      • {col['name']} ({col['type']})")

                if diff.get('column_changes'):
                    print(f"    Column type changes:")
                    for col_name, change in diff['column_changes'].items():
                        print(f"      • {col_name}: {change['source_type']} → {change['target_type']}")

                if diff.get('primary_key_diff'):
                    print(f"    Primary key differs")

                if diff.get('foreign_key_diff'):
                    print(f"    Foreign keys differ")

                if diff.get('index_diff'):
                    print(f"    Indexes differ")

        # Migration history
        print("\nMIGRATION HISTORY:")
        mh = self.differences['migration_history']
        if isinstance(mh.get('source_versions'), list):
            print(f"  Source latest versions: {mh['source_versions'][:3]}")
        else:
            print(f"  Source: {mh.get('source_versions')}")

        if isinstance(mh.get('target_versions'), list):
            print(f"  Target latest versions: {mh['target_versions'][:3]}")
        else:
            print(f"  Target: {mh.get('target_versions')}")

        if 'synced' in mh:
            print(f"  Migrations synced: {'✓ YES' if mh['synced'] else '✗ NO'}")

        print("\n" + "="*80 + "\n")

    def to_json(self, filepath: str = None) -> str:
        """Export report as JSON"""
        report = self.get_report()
        json_str = json.dumps(report, indent=2, default=str)

        if filepath:
            with open(filepath, 'w') as f:
                f.write(json_str)
            print(f"Report saved to {filepath}")

        return json_str


if __name__ == '__main__':
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Get connection strings
    local_db = os.getenv('DATABASE_URL', 'sqlite:///data/finance.db')
    cloud_sql = os.getenv('CLOUD_SQL_URL')

    if not cloud_sql:
        print("Error: CLOUD_SQL_URL environment variable not set")
        sys.exit(1)

    print(f"Comparing schemas...")
    print(f"  Local: {local_db}")
    print(f"  Cloud SQL: {cloud_sql}")

    comparator = SchemaComparator(local_db, cloud_sql)
    comparator.print_report()

    # Optionally save JSON report
    comparator.to_json('schema_comparison_report.json')
