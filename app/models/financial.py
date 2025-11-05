"""Financial insight and scenario planning models"""
from datetime import datetime
from app import db


class FinancialInsight(db.Model):
    """AI-generated financial insight for user"""
    __tablename__ = 'financial_insights'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    insight_type = db.Column(db.String(50), nullable=False)  # spending_spike, savings_opportunity, subscription_alert, etc.
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), nullable=False)  # info, warning, critical
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    amount_impact = db.Column(db.Numeric(10, 2), nullable=True)  # Dollar amount relevant to insight
    is_dismissed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='financial_insights')
    category = db.relationship('Category', backref='insights')

    def __repr__(self):
        return f'<FinancialInsight {self.insight_type} - {self.title}>'


class Scenario(db.Model):
    """Financial scenario for "what-if" planning"""
    __tablename__ = 'scenarios'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    scenario_type = db.Column(db.String(50), nullable=False)  # income_change, expense_change, debt_payoff, savings_goal
    base_month = db.Column(db.Date, nullable=False)  # Starting point for forecast
    duration_months = db.Column(db.Integer, nullable=False)  # How many months to forecast
    parameters = db.Column(db.Text, nullable=False)  # JSON string of scenario parameters
    results = db.Column(db.Text, nullable=True)  # JSON string of calculated results
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = db.relationship('User', backref='scenarios')

    def __repr__(self):
        return f'<Scenario {self.name}>'
