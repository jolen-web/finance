"""Categorization rules and payee mapping models"""
from datetime import datetime
from app import db


class CategorizationRule(db.Model):
    """Rule for automatic transaction categorization"""
    __tablename__ = 'categorization_rules'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    payee_pattern = db.Column(db.String(200), nullable=False)  # Pattern to match payee
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    confidence_score = db.Column(db.Numeric(3, 2), default=1.0)  # ML confidence (0-1)
    usage_count = db.Column(db.Integer, default=0)  # How many times this rule was applied
    is_auto_learned = db.Column(db.Boolean, default=False)  # Auto-learned vs manual rule
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    user = db.relationship('User', backref='categorization_rules')
    category = db.relationship('Category', backref='categorization_rules')

    def __repr__(self):
        return f'<CategorizationRule {self.payee_pattern} -> {self.category.name}>'


class PayeeCategory(db.Model):
    """Cache of payee → category mappings for smart categorization"""
    __tablename__ = 'payee_categories'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    payee = db.Column(db.String(200), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    frequency = db.Column(db.Integer, default=1)  # How many times this mapping was used
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='payee_categories')
    category = db.relationship('Category', backref='payee_mappings')

    def __repr__(self):
        return f'<PayeeCategory {self.payee} → {self.category.name}>'
