"""
Transaction Management Service

Provides CRUD operations and business logic for financial transactions.
"""

from app import db
from app.models import Transaction, Category
from datetime import datetime


class TransactionService:
    """Service for managing financial transactions."""

    @staticmethod
    def create_transaction(account_id, amount, description, category_id=None, transaction_type='expense'):
        """Create a new transaction."""
        transaction = Transaction(
            account_id=account_id,
            amount=amount,
            description=description,
            category_id=category_id,
            type=transaction_type,
            date=datetime.utcnow()
        )
        db.session.add(transaction)
        db.session.commit()
        return transaction

    @staticmethod
    def get_transaction(transaction_id):
        """Get a transaction by ID."""
        return Transaction.query.get(transaction_id)

    @staticmethod
    def get_account_transactions(account_id, limit=None):
        """Get transactions for an account."""
        query = Transaction.query.filter_by(account_id=account_id).order_by(Transaction.date.desc())
        if limit:
            query = query.limit(limit)
        return query.all()

    @staticmethod
    def update_transaction(transaction_id, **kwargs):
        """Update transaction information."""
        transaction = TransactionService.get_transaction(transaction_id)
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")

        allowed_fields = {'amount', 'description', 'category_id', 'date', 'type', 'is_cleared', 'is_reconciled'}
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(transaction, field, value)

        db.session.commit()
        return transaction

    @staticmethod
    def delete_transaction(transaction_id):
        """Delete a transaction."""
        transaction = TransactionService.get_transaction(transaction_id)
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")

        db.session.delete(transaction)
        db.session.commit()

    @staticmethod
    def bulk_delete_transactions(transaction_ids):
        """Delete multiple transactions."""
        Transaction.query.filter(Transaction.id.in_(transaction_ids)).delete()
        db.session.commit()

    @staticmethod
    def get_transactions_by_category(account_id, category_id):
        """Get all transactions for a category in an account."""
        return Transaction.query.filter_by(
            account_id=account_id,
            category_id=category_id
        ).all()

    @staticmethod
    def categorize_transaction(transaction_id, category_id):
        """Assign a category to a transaction."""
        return TransactionService.update_transaction(transaction_id, category_id=category_id)

    @staticmethod
    def toggle_cleared(transaction_id):
        """Toggle cleared status of a transaction."""
        transaction = TransactionService.get_transaction(transaction_id)
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")

        transaction.is_cleared = not transaction.is_cleared
        db.session.commit()
        return transaction

    @staticmethod
    def toggle_reconciled(transaction_id):
        """Toggle reconciled status of a transaction."""
        transaction = TransactionService.get_transaction(transaction_id)
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")

        transaction.is_reconciled = not transaction.is_reconciled
        db.session.commit()
        return transaction
