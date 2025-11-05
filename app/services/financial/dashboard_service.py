"""
Dashboard Service

Provides aggregated financial data and insights for the dashboard.
"""

from app import db
from app.models import Account, Transaction, Asset, Investment
from app.services.financial.account_service import AccountService


class DashboardService:
    """Service for dashboard data aggregation."""

    @staticmethod
    def get_dashboard_summary(user_id):
        """Get complete dashboard summary for a user."""
        return {
            'net_worth': DashboardService.get_net_worth(user_id),
            'account_summary': DashboardService.get_account_summary(user_id),
            'recent_transactions': DashboardService.get_recent_transactions(user_id, limit=5),
            'assets_total': DashboardService.get_assets_total(user_id),
            'investments_total': DashboardService.get_investments_total(user_id),
        }

    @staticmethod
    def get_net_worth(user_id):
        """Calculate total net worth."""
        return AccountService.calculate_net_worth(user_id)

    @staticmethod
    def get_account_summary(user_id):
        """Get summary of all user accounts."""
        accounts = Account.query.filter_by(user_id=user_id).all()
        return [
            {
                'id': acc.id,
                'name': acc.name,
                'type': acc.account_type,
                'balance': acc.current_balance
            }
            for acc in accounts
        ]

    @staticmethod
    def get_recent_transactions(user_id, limit=10):
        """Get recent transactions across all accounts."""
        accounts = Account.query.filter_by(user_id=user_id).all()
        account_ids = [acc.id for acc in accounts]

        transactions = Transaction.query.filter(
            Transaction.account_id.in_(account_ids)
        ).order_by(Transaction.date.desc()).limit(limit).all()

        return [
            {
                'id': t.id,
                'description': t.description,
                'amount': t.amount,
                'type': t.type,
                'date': t.date,
                'account_id': t.account_id
            }
            for t in transactions
        ]

    @staticmethod
    def get_assets_total(user_id):
        """Get total value of assets."""
        assets = Asset.query.filter_by(user_id=user_id).all()
        return sum(asset.current_value for asset in assets)

    @staticmethod
    def get_investments_total(user_id):
        """Get total value of investments."""
        investments = Investment.query.filter_by(user_id=user_id).all()
        return sum(inv.current_value for inv in investments)

    @staticmethod
    def get_spending_by_category(user_id, days=30):
        """Get spending breakdown by category for last N days."""
        from datetime import datetime, timedelta
        from app.models import Category

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        accounts = Account.query.filter_by(user_id=user_id).all()
        account_ids = [acc.id for acc in accounts]

        transactions = Transaction.query.filter(
            Transaction.account_id.in_(account_ids),
            Transaction.type == 'expense',
            Transaction.date >= cutoff_date
        ).all()

        spending = {}
        for transaction in transactions:
            category = transaction.category
            category_name = category.name if category else 'Uncategorized'

            if category_name not in spending:
                spending[category_name] = 0
            spending[category_name] += transaction.amount

        return spending
