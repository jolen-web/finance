"""
Chart Data Service - Provides formatted data for Chart.js visualizations
"""

from app import db
from app.models import Transaction, Category, Account
from sqlalchemy import func
from datetime import datetime, timedelta
import json


class ChartService:
    def __init__(self, user_id):
        self.user_id = user_id

    def get_income_expense_chart_data(self, months=12):
        """
        Get income vs expense data for line chart
        Returns data for the last N months
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30 * months)

        # Query income and expenses by month
        data = db.session.query(
            func.strftime('%Y-%m', Transaction.date).label('month'),
            func.sum(Transaction.amount).filter(Transaction.is_income == True).label('income'),
            func.sum(Transaction.amount).filter(Transaction.is_income == False).label('expenses')
        ).filter(
            Transaction.user_id == self.user_id,
            Transaction.date.between(start_date, end_date)
        ).group_by(
            func.strftime('%Y-%m', Transaction.date)
        ).order_by('month').all()

        months_list = []
        income_list = []
        expenses_list = []

        for month, income, expenses in data:
            months_list.append(month)
            income_list.append(float(income) if income else 0)
            expenses_list.append(float(expenses) if expenses else 0)

        return {
            'labels': months_list,
            'datasets': [
                {
                    'label': 'Income',
                    'data': income_list,
                    'borderColor': 'rgba(16, 185, 129, 1)',
                    'backgroundColor': 'rgba(16, 185, 129, 0.1)',
                    'borderWidth': 2,
                    'tension': 0.4,
                    'fill': True,
                },
                {
                    'label': 'Expenses',
                    'data': expenses_list,
                    'borderColor': 'rgba(239, 68, 68, 1)',
                    'backgroundColor': 'rgba(239, 68, 68, 0.1)',
                    'borderWidth': 2,
                    'tension': 0.4,
                    'fill': True,
                }
            ]
        }

    def get_spending_by_category_chart_data(self, months=3):
        """
        Get spending by category for doughnut/pie chart
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30 * months)

        data = db.session.query(
            Category.name,
            func.sum(Transaction.amount).label('total')
        ).join(Transaction).filter(
            Transaction.user_id == self.user_id,
            Transaction.is_income == False,
            Transaction.date.between(start_date, end_date)
        ).group_by(Category.name).order_by(
            func.sum(Transaction.amount).desc()
        ).all()

        # Color palette for categories
        colors = [
            'rgba(37, 99, 235, 0.8)',    # blue
            'rgba(239, 68, 68, 0.8)',    # red
            'rgba(16, 185, 129, 0.8)',   # green
            'rgba(245, 158, 11, 0.8)',   # yellow
            'rgba(6, 182, 212, 0.8)',    # cyan
            'rgba(139, 92, 246, 0.8)',   # purple
            'rgba(236, 72, 153, 0.8)',   # pink
            'rgba(100, 116, 139, 0.8)',  # slate
        ]

        labels = []
        amounts = []
        background_colors = []

        for i, (category_name, total) in enumerate(data):
            labels.append(category_name)
            amounts.append(float(total) if total else 0)
            background_colors.append(colors[i % len(colors)])

        return {
            'labels': labels,
            'datasets': [
                {
                    'data': amounts,
                    'backgroundColor': background_colors,
                    'borderColor': 'var(--bg-primary)',
                    'borderWidth': 2,
                }
            ]
        }

    def get_account_balance_chart_data(self):
        """
        Get current balances for all accounts as bar chart
        """
        accounts = Account.query.filter_by(
            user_id=self.user_id,
            is_active=True
        ).order_by(Account.current_balance.desc()).all()

        labels = []
        balances = []
        colors = []

        for account in accounts:
            labels.append(account.name)
            balances.append(float(account.current_balance))

            # Color based on balance and type
            if account.account_type == 'credit_card':
                colors.append('rgba(239, 68, 68, 0.8)')  # red for credit cards
            elif account.current_balance >= 0:
                colors.append('rgba(16, 185, 129, 0.8)')  # green for positive
            else:
                colors.append('rgba(239, 68, 68, 0.8)')   # red for negative

        return {
            'labels': labels,
            'datasets': [
                {
                    'label': 'Account Balance',
                    'data': balances,
                    'backgroundColor': colors,
                    'borderColor': 'var(--bg-primary)',
                    'borderWidth': 1,
                }
            ]
        }

    def get_net_worth_trend_data(self, months=12):
        """
        Get net worth trend over time
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30 * months)

        # Get daily account balances (simplified - using transaction dates)
        transactions = Transaction.query.filter(
            Transaction.user_id == self.user_id,
            Transaction.date.between(start_date, end_date)
        ).order_by(Transaction.date).all()

        # Calculate running net worth
        net_worth_data = {}

        # Start with current account balances
        accounts = Account.query.filter_by(user_id=self.user_id, is_active=True).all()
        current_net_worth = sum(
            acc.current_balance for acc in accounts
            if acc.account_type not in ['credit_card']
        ) - sum(
            abs(acc.current_balance) for acc in accounts
            if acc.account_type == 'credit_card'
        )

        # Work backwards
        for transaction in reversed(transactions):
            date_key = transaction.date.strftime('%Y-%m-%d')
            if date_key not in net_worth_data:
                # Undo the transaction to get previous value
                if transaction.is_income:
                    current_net_worth -= transaction.amount
                else:
                    current_net_worth += transaction.amount
                net_worth_data[date_key] = current_net_worth

        # Sort by date
        sorted_dates = sorted(net_worth_data.keys())
        sorted_values = [net_worth_data[date] for date in sorted_dates]

        return {
            'labels': sorted_dates,
            'datasets': [
                {
                    'label': 'Net Worth',
                    'data': sorted_values,
                    'borderColor': 'rgba(37, 99, 235, 1)',
                    'backgroundColor': 'rgba(37, 99, 235, 0.1)',
                    'borderWidth': 2,
                    'tension': 0.4,
                    'fill': True,
                }
            ]
        }

    def get_monthly_savings_rate(self, months=6):
        """
        Get monthly savings rate (income - expenses) / income
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30 * months)

        data = db.session.query(
            func.strftime('%Y-%m', Transaction.date).label('month'),
            func.sum(Transaction.amount).filter(Transaction.is_income == True).label('income'),
            func.sum(Transaction.amount).filter(Transaction.is_income == False).label('expenses')
        ).filter(
            Transaction.user_id == self.user_id,
            Transaction.date.between(start_date, end_date)
        ).group_by(
            func.strftime('%Y-%m', Transaction.date)
        ).order_by('month').all()

        months_list = []
        savings_rates = []

        for month, income, expenses in data:
            if income and income > 0:
                savings_rate = ((income - (expenses or 0)) / income) * 100
                months_list.append(month)
                savings_rates.append(round(savings_rate, 1))

        return {
            'labels': months_list,
            'datasets': [
                {
                    'label': 'Savings Rate (%)',
                    'data': savings_rates,
                    'borderColor': 'rgba(37, 99, 235, 1)',
                    'backgroundColor': 'rgba(37, 99, 235, 0.2)',
                    'borderWidth': 2,
                    'fill': True,
                    'tension': 0.4,
                }
            ]
        }
