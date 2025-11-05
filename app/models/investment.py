"""Investment models for tracking investment portfolio"""
from datetime import datetime
from app import db


class Investment(db.Model):
    """User investment holding (stock, bond, ETF, mutual fund, cryptocurrency, etc.)"""
    __tablename__ = 'investments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    ticker = db.Column(db.String(10), nullable=True)  # Stock ticker or investment code
    investment_type = db.Column(db.String(50), nullable=False)  # stock, bond, etf, mutual_fund, cryptocurrency, real_estate, other
    category_id = db.Column(db.Integer, db.ForeignKey('investment_categories.id'), nullable=True)
    quantity = db.Column(db.Numeric(18, 8), nullable=False, default=0)
    purchase_price = db.Column(db.Numeric(18, 4), nullable=False, default=0)
    current_price = db.Column(db.Numeric(18, 8), nullable=True)
    current_value = db.Column(db.Numeric(18, 4), nullable=True)  # Current price * quantity
    purchase_date = db.Column(db.Date, nullable=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='investments')
    category = db.relationship('InvestmentCategory', backref='investments')
    account = db.relationship('Account', backref='investments')

    def __repr__(self):
        return f'<Investment {self.name}>'

    def calculate_gain_loss(self):
        """Calculate gain or loss on investment"""
        if self.current_value and self.purchase_price:
            initial_investment = self.purchase_price * self.quantity
            return self.current_value - initial_investment
        return 0

    def calculate_gain_loss_percentage(self):
        """Calculate gain or loss percentage"""
        if self.current_value and self.purchase_price:
            initial_investment = self.purchase_price * self.quantity
            if initial_investment > 0:
                return ((self.current_value - initial_investment) / initial_investment) * 100
        return 0


class InvestmentCategory(db.Model):
    """Category for organizing investments"""
    __tablename__ = 'investment_categories'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    color = db.Column(db.String(7), default='#0066cc')  # Hex color for display
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    user = db.relationship('User', backref='investment_categories')
