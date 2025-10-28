from app import db
from app.models import Transaction, Category, Account
from sqlalchemy import func
from datetime import datetime, timedelta

class DashboardService:
    def __init__(self, user_id):
        self.user_id = user_id

    def get_dashboard_data(self, start_date, end_date):
        # Financial Summary
        total_income = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == self.user_id,
            Transaction.is_income == True,
            Transaction.date.between(start_date, end_date)
        ).scalar() or 0

        total_expenses = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == self.user_id,
            Transaction.is_income == False,
            Transaction.date.between(start_date, end_date)
        ).scalar() or 0

        net_savings = total_income - total_expenses

        # Recent Transactions
        recent_transactions = Transaction.query.filter(
            Transaction.user_id == self.user_id
        ).order_by(Transaction.date.desc()).limit(5).all()

        # Income vs Expense Chart Data
        income_by_month = self._get_monthly_summary(start_date, end_date, is_income=True)
        expense_by_month = self._get_monthly_summary(start_date, end_date, is_income=False)

        # Expense Categories Chart Data
        expense_categories = self._get_category_summary(start_date, end_date)

        # Account Balances
        accounts = Account.query.filter_by(user_id=self.user_id).all()

        return {
            'start_date': start_date,
            'end_date': end_date,
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_savings': net_savings,
            'recent_transactions': recent_transactions,
            'income_by_month': income_by_month,
            'expense_by_month': expense_by_month,
            'expense_categories': expense_categories,
            'accounts': accounts
        }

    def _get_monthly_summary(self, start_date, end_date, is_income):
        return db.session.query(
            func.strftime('%Y-%m', Transaction.date),
            func.sum(Transaction.amount)
        ).filter(
            Transaction.user_id == self.user_id,
            Transaction.is_income == is_income,
            Transaction.date.between(start_date, end_date)
        ).group_by(func.strftime('%Y-%m', Transaction.date)).all()

    def _get_category_summary(self, start_date, end_date):
        return db.session.query(
            Category.name,
            func.sum(Transaction.amount)
        ).join(Category).filter(
            Transaction.user_id == self.user_id,
            Transaction.is_income == False,
            Transaction.date.between(start_date, end_date)
        ).group_by(Category.name).order_by(func.sum(Transaction.amount).desc()).all()

    def get_net_worth_data(self):
        accounts = Account.query.filter_by(user_id=self.user_id, is_active=True).all()

        total_assets = sum(acc.current_balance for acc in accounts if acc.account_type in ['checking', 'savings', 'cash'])
        total_liabilities = sum(abs(acc.current_balance) for acc in accounts if acc.account_type == 'credit_card')
        net_worth = total_assets - total_liabilities

        recent_transactions = Transaction.query.filter_by(user_id=self.user_id).order_by(Transaction.date.desc()).limit(10).all()

        return {
            'accounts': accounts,
            'recent_transactions': recent_transactions,
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'net_worth': net_worth
        }
