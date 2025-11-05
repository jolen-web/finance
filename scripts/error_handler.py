"""
Error handling and logging middleware for the Finance Tracker
Captures and logs errors for later analysis or automatic fixing
"""

import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


class ErrorLogger:
    """Logs errors to a file for analysis and fixing"""

    def __init__(self, log_dir: str = None):
        """Initialize error logger"""
        if log_dir is None:
            log_dir = Path(__file__).parent / 'data' / 'error_logs'
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Set up logging
        self.logger = logging.getLogger('finance_tracker_errors')
        self.logger.setLevel(logging.ERROR)

        # File handler for error logs
        error_file = self.log_dir / 'errors.log'
        handler = logging.FileHandler(error_file)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Log an error with context

        Args:
            error: The exception that occurred
            context: Additional context about the error

        Returns:
            Dictionary with error information
        """
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {}
        }

        # Log to file
        self.logger.error(
            f"{error_info['error_type']}: {error_info['error_message']}"
        )

        # Save detailed error report as JSON
        error_file = self.log_dir / f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(error_file, 'w') as f:
            json.dump(error_info, f, indent=2)

        return error_info


class ErrorFixerTools:
    """Tools for analyzing and fixing errors"""

    # Known error patterns and their fixes
    KNOWN_PATTERNS = {
        'SQLite Date type only accepts Python date objects': {
            'error_type': 'TypeError',
            'root_cause': 'Date string passed to SQLAlchemy Date column instead of Python date object',
            'fix_description': 'Convert date string to Python date object using datetime.strptime()',
            'example_fix': 'purchase_date = datetime.strptime(purchase_date, "%Y-%m-%d").date()',
            'imports_needed': ['from datetime import datetime']
        },
        'NoneType': {
            'error_type': 'TypeError',
            'root_cause': 'Attempting to perform operations on None value',
            'fix_description': 'Add null/None checks before using the value'
        },
        'Module not found': {
            'error_type': 'ModuleNotFoundError',
            'root_cause': 'Required module not installed',
            'fix_description': 'Install the missing module using pip'
        }
    }

    @classmethod
    def analyze_error(cls, error_message: str, error_type: str = None) -> Dict[str, Any]:
        """
        Analyze an error and suggest a fix based on known patterns

        Args:
            error_message: The error message
            error_type: The type of error

        Returns:
            Dictionary with analysis and suggestions
        """
        analysis = {
            'error_message': error_message,
            'error_type': error_type,
            'known_pattern': False,
            'suggestion': None
        }

        # Check against known patterns
        for pattern_key, pattern_info in cls.KNOWN_PATTERNS.items():
            if pattern_key.lower() in error_message.lower():
                analysis['known_pattern'] = True
                analysis['suggestion'] = pattern_info
                analysis['fix_description'] = pattern_info.get('fix_description')
                break

        return analysis

    @classmethod
    def get_fix_suggestion(cls, error_message: str) -> str:
        """Get a suggested fix for an error"""
        analysis = cls.analyze_error(error_message)
        if analysis['suggestion']:
            return analysis['suggestion'].get('example_fix', 'No automatic fix available')
        return None


def register_error_handlers(app):
    """Register error handlers with Flask app"""
    error_logger = ErrorLogger()

    @app.errorhandler(Exception)
    def handle_error(error):
        """Handle all unhandled exceptions"""
        context = {
            'url': request.url if hasattr(request, 'url') else None,
            'method': request.method if hasattr(request, 'method') else None,
        }

        error_info = error_logger.log_error(error, context)

        # Analysis
        analysis = ErrorFixerTools.analyze_error(
            str(error),
            type(error).__name__
        )

        return {
            'error': str(error),
            'error_type': type(error).__name__,
            'known_pattern': analysis['known_pattern'],
            'suggestion': analysis.get('fix_description')
        }, 500
