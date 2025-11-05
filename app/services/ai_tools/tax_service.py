"""
Tax Assistant Service

Wrapper around existing tax functionality with enhanced service interface.
"""

from app.services.tax_assistant import TaxAssistant as ExistingTaxAssistant


class TaxService:
    """Service for tax planning and assistance."""

    @staticmethod
    def get_tax_summary(user_id):
        """Get tax summary for a user."""
        return ExistingTaxAssistant.get_summary(user_id)

    @staticmethod
    def get_deductible_transactions(user_id):
        """Get transactions marked as tax-deductible."""
        return ExistingTaxAssistant.get_deductible_transactions(user_id)

    @staticmethod
    def get_income_summary(user_id):
        """Get income summary for tax purposes."""
        return ExistingTaxAssistant.get_income_summary(user_id)

    @staticmethod
    def get_expense_summary(user_id):
        """Get expense summary for tax purposes."""
        return ExistingTaxAssistant.get_expense_summary(user_id)
