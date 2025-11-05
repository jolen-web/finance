"""Account model for tracking user accounts"""
from datetime import datetime
from app import db


class Account(db.Model):
    """User financial account (checking, savings, credit card, cash)"""
    __tablename__ = 'accounts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    account_type = db.Column(db.String(20), nullable=False)  # checking, savings, credit_card, cash
    starting_balance = db.Column(db.Numeric(10, 2), default=0.0)
    current_balance = db.Column(db.Numeric(10, 2), default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    user = db.relationship('User', backref='accounts')
    transactions = db.relationship('Transaction', backref='account', lazy='dynamic',
                                   cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Account {self.name}>'

    def update_balance(self):
        """Calculate current balance based on starting balance and all transactions"""
        total = self.starting_balance

        for transaction in self.transactions:
            if self.account_type == 'credit_card':
                # For credit cards, balance represents debt (positive = money owed)
                # Charges (withdrawals) increase debt, payments (deposits) decrease debt
                if transaction.transaction_type == 'withdrawal':
                    # Charge/purchase increases debt
                    total += transaction.amount
                elif transaction.transaction_type == 'deposit':
                    # Payment decreases debt
                    total -= transaction.amount
            else:
                # For checking, savings, cash accounts: standard logic
                # Deposits increase balance, withdrawals decrease balance
                if transaction.transaction_type == 'deposit':
                    total += transaction.amount
                elif transaction.transaction_type == 'withdrawal' or transaction.transaction_type == 'transfer':
                    total -= transaction.amount

        self.current_balance = total
        return self.current_balance
