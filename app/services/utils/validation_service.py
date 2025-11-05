"""
Data Validation Service

Provides validation for user inputs and data consistency.
"""

import re
from decimal import Decimal


class ValidationService:
    """Service for validating financial data."""

    @staticmethod
    def validate_email(email):
        """Validate email address format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_username(username):
        """Validate username format."""
        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise ValueError("Username can only contain letters, numbers, underscore, and hyphen")
        return True

    @staticmethod
    def validate_password(password):
        """Validate password strength."""
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return True

    @staticmethod
    def validate_amount(amount):
        """Validate transaction amount."""
        try:
            decimal_amount = Decimal(str(amount))
            if decimal_amount < 0:
                raise ValueError("Amount must be positive")
            return decimal_amount
        except:
            raise ValueError("Invalid amount format")

    @staticmethod
    def validate_account_name(name):
        """Validate account name."""
        if not name or len(name.strip()) == 0:
            raise ValueError("Account name cannot be empty")
        if len(name) > 100:
            raise ValueError("Account name is too long (max 100 characters)")
        return True

    @staticmethod
    def validate_category_name(name):
        """Validate category name."""
        if not name or len(name.strip()) == 0:
            raise ValueError("Category name cannot be empty")
        if len(name) > 50:
            raise ValueError("Category name is too long (max 50 characters)")
        return True

    @staticmethod
    def validate_transaction_data(amount, description, account_id):
        """Validate transaction data."""
        ValidationService.validate_amount(amount)

        if not description or len(description.strip()) == 0:
            raise ValueError("Description cannot be empty")

        if len(description) > 500:
            raise ValueError("Description is too long (max 500 characters)")

        if not account_id:
            raise ValueError("Account ID is required")

        return True
