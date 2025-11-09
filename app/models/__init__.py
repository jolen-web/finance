"""
Finance Tracker Models Package

Modular model organization for the Finance Tracker application.
All models are imported here for centralized access.
"""

# Base classes and mixins
from app.models.base import TimestampMixin

# Core models
from app.models.user import User
from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction, TaxTag
from app.models.receipt import Receipt

# Asset and investment models
from app.models.asset import Asset
from app.models.investment import Investment, InvestmentCategory

# Financial planning models
from app.models.financial import FinancialInsight, Scenario

# Categorization and rules
from app.models.categorization import CategorizationRule, PayeeCategory
from app.models.regex_pattern import RegexPattern

# User preferences
from app.models.preferences import DashboardPreferences

# Feedback
from app.models.feedback import Feedback

# Deals and promotions
from app.models.deal import Deal

# Export all models
__all__ = [
    # Base
    'TimestampMixin',

    # Core
    'User',
    'Account',
    'Category',
    'Transaction',
    'TaxTag',
    'Receipt',

    # Assets and Investments
    'Asset',
    'Investment',
    'InvestmentCategory',

    # Financial
    'FinancialInsight',
    'Scenario',

    # Categorization
    'CategorizationRule',
    'PayeeCategory',
    'RegexPattern',

    # Preferences
    'DashboardPreferences',

    # Feedback
    'Feedback',

    # Deals
    'Deal',
]
