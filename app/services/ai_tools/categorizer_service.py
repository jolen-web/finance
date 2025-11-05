"""
AI Transaction Categorizer Service

Wrapper around existing categorizer functionality with enhanced service interface.
"""

from app.services.categorizer import CategorizerService as ExistingCategorizer


class CategorizerService:
    """Service for AI-powered transaction categorization."""

    @staticmethod
    def categorize_transaction(transaction_id, user_id):
        """Categorize a transaction using AI."""
        # Delegate to existing categorizer
        return ExistingCategorizer.categorize_transaction(transaction_id, user_id)

    @staticmethod
    def auto_categorize_user_transactions(user_id):
        """Auto-categorize all uncategorized transactions for a user."""
        # Delegate to existing categorizer
        return ExistingCategorizer.auto_categorize_user_transactions(user_id)

    @staticmethod
    def get_category_suggestion(transaction):
        """Get category suggestion for a transaction."""
        # Delegate to existing categorizer
        return ExistingCategorizer.get_category_suggestion(transaction)
