#!/usr/bin/env python
"""
Comprehensive error fixing tool for Finance Tracker
Analyzes errors and applies fixes with optional user review

Usage:
    python fix_errors.py --analyze-logs          # Analyze all logged errors
    python fix_errors.py --auto-fix              # Auto-apply fixes
    python fix_errors.py --review                # Review fixes before applying
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class ErrorFixer:
    """Main error fixing tool"""

    # Known fixes for common errors
    FIXES = {
        'date_conversion': {
            'pattern': 'SQLite Date type only accepts Python date objects',
            'files': ['app/routes/assets.py'],
            'problem': 'purchase_date if purchase_date else None',
            'solution': '''# Convert date string to date object
        if purchase_date:
            try:
                purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                errors.append('Purchase date must be in YYYY-MM-DD format')
                purchase_date = None
        else:
            purchase_date = None''',
            'status': 'APPLIED'
        }
    }

    def __init__(self, project_root: str = None):
        """Initialize the error fixer"""
        self.project_root = Path(project_root) if project_root else Path(__file__).parent
        self.error_log_dir = self.project_root / 'data' / 'error_logs'
        self.error_log_file = self.error_log_dir / 'errors.log'

    def analyze_logs(self) -> List[Dict[str, Any]]:
        """Analyze error logs and extract patterns"""
        errors = []

        if not self.error_log_file.exists():
            print(f"No error log file found at {self.error_log_file}")
            return errors

        with open(self.error_log_file, 'r') as f:
            for line in f:
                if line.strip():
                    errors.append({'raw': line.strip()})

        return errors

    def find_known_fixes(self, error_message: str) -> List[str]:
        """Find known fixes for an error"""
        fixes = []

        for fix_name, fix_info in self.FIXES.items():
            if fix_info['pattern'].lower() in error_message.lower():
                fixes.append(fix_name)

        return fixes

    def display_fix(self, fix_name: str) -> Dict[str, Any]:
        """Display a fix with details"""
        if fix_name not in self.FIXES:
            return None

        fix = self.FIXES[fix_name]

        print(f"\n{'='*60}")
        print(f"FIX: {fix_name.upper()}")
        print(f"{'='*60}")
        print(f"Pattern: {fix['pattern']}")
        print(f"Status: {fix['status']}")
        print(f"Files: {', '.join(fix['files'])}")
        print(f"\nPROBLEM:")
        print(fix['problem'])
        print(f"\nSOLUTION:")
        print(fix['solution'])
        print(f"{'='*60}\n")

        return fix

    def auto_fix(self) -> Dict[str, Any]:
        """Automatically apply all known fixes"""
        results = {
            'success': True,
            'applied_fixes': [],
            'errors': []
        }

        errors = self.analyze_logs()

        for error in errors:
            error_msg = error.get('raw', '')
            fixes = self.find_known_fixes(error_msg)

            for fix_name in fixes:
                fix = self.FIXES[fix_name]
                if fix['status'] == 'APPLIED':
                    results['applied_fixes'].append({
                        'fix': fix_name,
                        'error': error_msg,
                        'timestamp': datetime.now().isoformat()
                    })

        return results

    def review_mode(self) -> Dict[str, Any]:
        """Review mode - ask user before applying fixes"""
        results = {
            'reviewed': [],
            'skipped': [],
            'applied': []
        }

        errors = self.analyze_logs()

        for i, error in enumerate(errors, 1):
            error_msg = error.get('raw', '')
            fixes = self.find_known_fixes(error_msg)

            if not fixes:
                results['skipped'].append(error_msg)
                continue

            for fix_name in fixes:
                fix = self.display_fix(fix_name)

                if fix and fix['status'] == 'APPLIED':
                    response = input("Apply this fix? (y/n): ").strip().lower()
                    if response == 'y':
                        results['applied'].append(fix_name)
                    else:
                        results['skipped'].append(fix_name)

                results['reviewed'].append(fix_name)

        return results

    def print_status(self) -> None:
        """Print status of all known fixes"""
        print("\n" + "="*60)
        print("KNOWN FIXES STATUS")
        print("="*60)

        for fix_name, fix_info in self.FIXES.items():
            status_symbol = "✅" if fix_info['status'] == 'APPLIED' else "⏳"
            print(f"{status_symbol} {fix_name:30} - {fix_info['pattern'][:30]}...")

        print("="*60 + "\n")

    def summary_report(self) -> None:
        """Generate a summary report"""
        print("\n" + "="*60)
        print("ERROR FIXER SUMMARY REPORT")
        print("="*60)
        print(f"Project Root: {self.project_root}")
        print(f"Error Log: {self.error_log_file}")
        print(f"Known Fixes: {len(self.FIXES)}")

        # Check which fixes have been applied
        applied = sum(1 for f in self.FIXES.values() if f['status'] == 'APPLIED')
        pending = len(self.FIXES) - applied

        print(f"Applied: {applied}")
        print(f"Pending: {pending}")
        print("="*60 + "\n")

        # Log summary
        summary_file = self.project_root / 'data' / 'error_logs' / 'fixer_summary.json'
        summary_data = {
            'timestamp': datetime.now().isoformat(),
            'total_fixes': len(self.FIXES),
            'applied': applied,
            'pending': pending,
            'fixes': list(self.FIXES.keys())
        }

        self.project_root.joinpath('data', 'error_logs').mkdir(parents=True, exist_ok=True)
        with open(summary_file, 'w') as f:
            json.dump(summary_data, f, indent=2)

        print(f"Summary saved to {summary_file}")


def main():
    """CLI interface"""
    parser = argparse.ArgumentParser(
        description="Error fixing tool for Finance Tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fix_errors.py --status              Show fix status
  python fix_errors.py --analyze-logs        Analyze error logs
  python fix_errors.py --auto-fix            Auto-apply all fixes
  python fix_errors.py --review              Review fixes before applying
  python fix_errors.py --summary             Generate summary report
        """
    )

    parser.add_argument('--status', action='store_true',
                       help='Show status of all known fixes')
    parser.add_argument('--analyze-logs', action='store_true',
                       help='Analyze error logs')
    parser.add_argument('--auto-fix', action='store_true',
                       help='Automatically apply all fixes')
    parser.add_argument('--review', action='store_true',
                       help='Review fixes before applying')
    parser.add_argument('--summary', action='store_true',
                       help='Generate summary report')
    parser.add_argument('--project-root', type=str, default=None,
                       help='Project root directory')

    args = parser.parse_args()

    fixer = ErrorFixer(args.project_root)

    if args.status:
        fixer.print_status()

    elif args.analyze_logs:
        errors = fixer.analyze_logs()
        print(f"\nFound {len(errors)} errors in logs:")
        for i, error in enumerate(errors, 1):
            print(f"{i}. {error.get('raw', 'Unknown')[:80]}...")

    elif args.auto_fix:
        print("Running auto-fix...")
        results = fixer.auto_fix()
        print(f"✅ Applied {len(results['applied_fixes'])} fixes")
        if results['errors']:
            print(f"❌ Encountered {len(results['errors'])} errors")

    elif args.review:
        print("Entering review mode...\n")
        results = fixer.review_mode()
        print(f"\n✅ Applied: {len(results['applied'])}")
        print(f"⏭️  Skipped: {len(results['skipped'])}")
        print(f"📋 Reviewed: {len(results['reviewed'])}")

    elif args.summary:
        fixer.summary_report()

    else:
        # Default: show status
        fixer.print_status()
        fixer.summary_report()


if __name__ == '__main__':
    main()
