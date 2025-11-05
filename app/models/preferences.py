"""User dashboard preferences model"""
from datetime import datetime
from app import db


class DashboardPreferences(db.Model):
    """User dashboard preferences and settings"""
    __tablename__ = 'dashboard_preferences'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    show_accounts = db.Column(db.Boolean, default=True)
    show_transactions = db.Column(db.Boolean, default=True)
    show_investments = db.Column(db.Boolean, default=False)
    show_assets = db.Column(db.Boolean, default=False)
    show_receipts = db.Column(db.Boolean, default=True)
    default_page = db.Column(db.String(50), default='dashboard')  # dashboard, accounts, transactions, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<DashboardPreferences(user_id={self.user_id})>'
