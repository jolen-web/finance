"""
Backup and Data Export Service

Provides functionality for exporting and importing user financial data.
"""

import json
from datetime import datetime
from app import db
from app.models import Account, Transaction, Category, Asset, Investment


class BackupService:
    """Service for backing up and restoring user data."""

    @staticmethod
    def export_user_data(user_id):
        """Export all user financial data as JSON."""
        accounts = Account.query.filter_by(user_id=user_id).all()
        transactions = []
        for account in accounts:
            transactions.extend(Transaction.query.filter_by(account_id=account.id).all())

        categories = Category.query.filter_by(user_id=user_id).all()
        assets = Asset.query.filter_by(user_id=user_id).all()
        investments = Investment.query.filter_by(user_id=user_id).all()

        backup = {
            'timestamp': datetime.utcnow().isoformat(),
            'accounts': [BackupService._serialize_account(acc) for acc in accounts],
            'transactions': [BackupService._serialize_transaction(t) for t in transactions],
            'categories': [BackupService._serialize_category(c) for c in categories],
            'assets': [BackupService._serialize_asset(a) for a in assets],
            'investments': [BackupService._serialize_investment(i) for i in investments],
        }

        return json.dumps(backup, indent=2)

    @staticmethod
    def _serialize_account(account):
        """Serialize account to dictionary."""
        return {
            'id': account.id,
            'name': account.name,
            'type': account.account_type,
            'balance': float(account.current_balance),
        }

    @staticmethod
    def _serialize_transaction(transaction):
        """Serialize transaction to dictionary."""
        return {
            'id': transaction.id,
            'amount': float(transaction.amount),
            'description': transaction.description,
            'type': transaction.type,
            'date': transaction.date.isoformat(),
            'account_id': transaction.account_id,
            'category_id': transaction.category_id,
        }

    @staticmethod
    def _serialize_category(category):
        """Serialize category to dictionary."""
        return {
            'id': category.id,
            'name': category.name,
            'type': category.type,
            'parent_id': category.parent_id,
        }

    @staticmethod
    def _serialize_asset(asset):
        """Serialize asset to dictionary."""
        return {
            'id': asset.id,
            'name': asset.name,
            'type': asset.type,
            'value': float(asset.current_value),
            'description': asset.description,
        }

    @staticmethod
    def _serialize_investment(investment):
        """Serialize investment to dictionary."""
        return {
            'id': investment.id,
            'symbol': investment.symbol,
            'name': investment.name,
            'shares': float(investment.shares),
            'purchase_price': float(investment.purchase_price),
            'current_price': float(investment.current_price),
            'category_id': investment.category_id,
        }
