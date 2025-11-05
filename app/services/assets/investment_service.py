"""
Investment Management Service

Provides CRUD operations for tracking investments and portfolio performance.
"""

from app import db
from app.models import Investment, InvestmentCategory


class InvestmentService:
    """Service for managing investments."""

    @staticmethod
    def create_investment(user_id, symbol, name, shares, purchase_price, current_price, category_id=None):
        """Create a new investment."""
        investment = Investment(
            user_id=user_id,
            symbol=symbol,
            name=name,
            shares=shares,
            purchase_price=purchase_price,
            current_price=current_price,
            category_id=category_id
        )
        db.session.add(investment)
        db.session.commit()
        return investment

    @staticmethod
    def get_investment(investment_id):
        """Get an investment by ID."""
        return Investment.query.get(investment_id)

    @staticmethod
    def get_user_investments(user_id):
        """Get all investments for a user."""
        return Investment.query.filter_by(user_id=user_id).all()

    @staticmethod
    def update_investment(investment_id, **kwargs):
        """Update investment information."""
        investment = InvestmentService.get_investment(investment_id)
        if not investment:
            raise ValueError(f"Investment {investment_id} not found")

        allowed_fields = {'symbol', 'name', 'shares', 'purchase_price', 'current_price', 'category_id'}
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(investment, field, value)

        db.session.commit()
        return investment

    @staticmethod
    def delete_investment(investment_id):
        """Delete an investment."""
        investment = InvestmentService.get_investment(investment_id)
        if not investment:
            raise ValueError(f"Investment {investment_id} not found")

        db.session.delete(investment)
        db.session.commit()

    @staticmethod
    def update_price(investment_id, current_price):
        """Update current price of an investment."""
        return InvestmentService.update_investment(investment_id, current_price=current_price)

    @staticmethod
    def get_portfolio_value(user_id):
        """Get total current value of investment portfolio."""
        investments = InvestmentService.get_user_investments(user_id)
        return sum(inv.shares * inv.current_price for inv in investments)

    @staticmethod
    def get_portfolio_performance(user_id):
        """Get gain/loss and percentage return on portfolio."""
        investments = InvestmentService.get_user_investments(user_id)

        total_invested = sum(inv.shares * inv.purchase_price for inv in investments)
        total_current = sum(inv.shares * inv.current_price for inv in investments)

        gain_loss = total_current - total_invested

        if total_invested == 0:
            return_percent = 0
        else:
            return_percent = (gain_loss / total_invested) * 100

        return {
            'total_invested': total_invested,
            'total_current': total_current,
            'gain_loss': gain_loss,
            'return_percent': return_percent
        }

    @staticmethod
    def create_category(user_id, name):
        """Create an investment category."""
        category = InvestmentCategory(user_id=user_id, name=name)
        db.session.add(category)
        db.session.commit()
        return category

    @staticmethod
    def get_user_investment_categories(user_id):
        """Get all investment categories for a user."""
        return InvestmentCategory.query.filter_by(user_id=user_id).all()
