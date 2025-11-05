"""Transaction and TaxTag models for tracking financial transactions"""
from datetime import datetime
from app import db


class Transaction(db.Model):
    """User financial transaction"""
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payee = db.Column(db.String(200), nullable=True)
    memo = db.Column(db.Text, nullable=True)
    transaction_type = db.Column(db.String(20), nullable=False)  # deposit, withdrawal, transfer
    is_cleared = db.Column(db.Boolean, default=False)
    is_reconciled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign keys
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)

    # For transfers: link to the corresponding transaction in the other account
    transfer_to_transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=True)

    # Relationship
    user = db.relationship('User', backref='transactions')

    def __repr__(self):
        return f'<Transaction {self.payee} - ${self.amount}>'


class TaxTag(db.Model):
    """Tax deduction metadata for transactions"""
    __tablename__ = 'tax_tags'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=False)
    tax_year = db.Column(db.Integer, nullable=False)
    is_deductible = db.Column(db.Boolean, default=True)
    deduction_type = db.Column(db.String(100), nullable=False)  # home_office, mileage, charitable, medical, business_expense
    deduction_percentage = db.Column(db.Numeric(5, 2), default=100.0)  # For partial deductions
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='tax_tags')
    transaction = db.relationship('Transaction', backref='tax_tags')

    def __repr__(self):
        return f'<TaxTag {self.deduction_type} - {self.tax_year}>'
