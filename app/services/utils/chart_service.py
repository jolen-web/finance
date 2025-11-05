"""
Chart Generation Service

Wrapper around existing chart functionality with enhanced service interface.
"""

from app.services.chart_service import ChartService as ExistingChartService


class ChartService:
    """Service for generating financial charts and visualizations."""

    @staticmethod
    def generate_spending_chart(user_id, period='month'):
        """Generate spending chart for a user."""
        return ExistingChartService.generate_spending_chart(user_id, period)

    @staticmethod
    def generate_income_chart(user_id, period='month'):
        """Generate income chart for a user."""
        return ExistingChartService.generate_income_chart(user_id, period)

    @staticmethod
    def generate_account_balance_chart(account_id):
        """Generate balance over time chart for an account."""
        return ExistingChartService.generate_account_balance_chart(account_id)

    @staticmethod
    def generate_category_breakdown(user_id):
        """Generate pie chart of spending by category."""
        return ExistingChartService.generate_category_breakdown(user_id)

    @staticmethod
    def generate_portfolio_allocation(user_id):
        """Generate pie chart of investment portfolio allocation."""
        return ExistingChartService.generate_portfolio_allocation(user_id)
