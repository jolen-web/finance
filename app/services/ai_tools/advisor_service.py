"""
Financial Advisor Service

Wrapper around existing advisor functionality with enhanced service interface.
"""

from app.services.financial_advisor import (
    get_spending_summary,
    get_financial_insights,
    get_savings_opportunities
)


class AdvisorService:
    """Service for AI-powered financial advice."""

    @staticmethod
    def get_spending_analysis(user_id):
        """Get spending analysis for a user."""
        return get_spending_summary(user_id)

    @staticmethod
    def get_financial_insights(user_id):
        """Get AI-powered financial insights."""
        return get_financial_insights(user_id)

    @staticmethod
    def get_savings_opportunities(user_id):
        """Get personalized savings recommendations."""
        return get_savings_opportunities(user_id)

    @staticmethod
    def analyze_spending_patterns(user_id, days=30):
        """Analyze spending patterns over time."""
        # Would implement pattern analysis logic
        pass
