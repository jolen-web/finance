"""
Account Management Service

Provides CRUD operations and business logic for financial accounts.
"""

from app import db
from app.models import Account, Transaction
from flask_login import current_user


class AccountService:
    """Service for managing financial accounts."""

    @staticmethod
    def create_account(user_id, name, account_type, starting_balance=0):
        """Create a new account for a user."""
        account = Account(
            user_id=user_id,
            name=name,
            account_type=account_type,
            current_balance=starting_balance
        )
        db.session.add(account)
        db.session.commit()
        return account

    @staticmethod
    def get_account(account_id):
        """Get an account by ID."""
        return Account.query.get(account_id)

    @staticmethod
    def get_user_accounts(user_id):
        """Get all accounts for a user."""
        return Account.query.filter_by(user_id=user_id).all()

    @staticmethod
    def update_account(account_id, **kwargs):
        """Update account information."""
        account = AccountService.get_account(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")

        allowed_fields = {'name', 'account_type', 'current_balance'}
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(account, field, value)

        db.session.commit()
        return account

    @staticmethod
    def delete_account(account_id):
        """Delete an account."""
        account = AccountService.get_account(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")

        # Delete associated transactions
        Transaction.query.filter_by(account_id=account_id).delete()

        db.session.delete(account)
        db.session.commit()

    @staticmethod
    def calculate_net_worth(user_id):
        """Calculate total net worth across all accounts."""
        accounts = AccountService.get_user_accounts(user_id)
        return sum(account.current_balance for account in accounts)

    @staticmethod
    def get_account_balance(account_id):
        """Get current balance for an account."""
        account = AccountService.get_account(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")
        return account.current_balance

    @staticmethod
    def update_balance(account_id, amount):
        """Update account balance to specific amount."""
        account = AccountService.get_account(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")

        account.current_balance = amount
        db.session.commit()
        return account
