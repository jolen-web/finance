from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)


class Account(db.Model):
    __tablename__ = 'accounts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    account_type = db.Column(db.String(20), nullable=False)  # checking, savings, credit_card, cash
    starting_balance = db.Column(db.Float, default=0.0)
    current_balance = db.Column(db.Float, default=0.0)
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


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    is_income = db.Column(db.Boolean, default=False)  # True for income categories
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='categories')
    # Self-referential relationship for subcategories
    subcategories = db.relationship('Category', backref=db.backref('parent', remote_side=[id]))

    # Relationships
    transactions = db.relationship('Transaction', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'


class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    amount = db.Column(db.Float, nullable=False)
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


class Receipt(db.Model):
    __tablename__ = 'receipts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id', ondelete='CASCADE'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(20), nullable=False)  # image/jpeg, image/png, application/pdf
    extracted_merchant = db.Column(db.String(200), nullable=True)
    extracted_date = db.Column(db.Date, nullable=True)
    extracted_amount = db.Column(db.Float, nullable=True)
    extracted_items = db.Column(db.Text, nullable=True)  # JSON string of line items
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    user = db.relationship('User', backref='receipts')
    transaction = db.relationship('Transaction', backref=db.backref('receipts', cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<Receipt {self.filename}>'


class TaxTag(db.Model):
    __tablename__ = 'tax_tags'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=False)
    tax_year = db.Column(db.Integer, nullable=False)
    is_deductible = db.Column(db.Boolean, default=True)
    deduction_type = db.Column(db.String(100), nullable=False)  # home_office, mileage, charitable, medical, business_expense
    deduction_percentage = db.Column(db.Float, default=100.0)  # For partial deductions
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='tax_tags')
    transaction = db.relationship('Transaction', backref='tax_tags')

    def __repr__(self):
        return f'<TaxTag {self.deduction_type} - {self.tax_year}>'


class CategorizationRule(db.Model):
    __tablename__ = 'categorization_rules'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    payee_pattern = db.Column(db.String(200), nullable=False)  # Pattern to match payee
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    confidence_score = db.Column(db.Float, default=1.0)  # ML confidence (0-1)
    usage_count = db.Column(db.Integer, default=0)  # How many times this rule was applied
    is_auto_learned = db.Column(db.Boolean, default=False)  # Auto-learned vs manual rule
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    user = db.relationship('User', backref='categorization_rules')
    category = db.relationship('Category', backref='categorization_rules')

    def __repr__(self):
        return f'<CategorizationRule {self.payee_pattern} -> {self.category.name}>'


class FinancialInsight(db.Model):
    __tablename__ = 'financial_insights'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    insight_type = db.Column(db.String(50), nullable=False)  # spending_spike, savings_opportunity, subscription_alert, etc.
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), nullable=False)  # info, warning, critical
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    amount_impact = db.Column(db.Float, nullable=True)  # Dollar amount relevant to insight
    is_dismissed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='financial_insights')
    category = db.relationship('Category', backref='insights')

    def __repr__(self):
        return f'<FinancialInsight {self.insight_type} - {self.title}>'


class Scenario(db.Model):
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


class Investment(db.Model):
    __tablename__ = 'investments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    ticker = db.Column(db.String(10), nullable=True)  # Stock ticker or investment code
    investment_type = db.Column(db.String(50), nullable=False)  # stock, bond, etf, mutual_fund, cryptocurrency, real_estate, other
    category_id = db.Column(db.Integer, db.ForeignKey('investment_categories.id'), nullable=True)
    quantity = db.Column(db.Float, nullable=False, default=0)
    purchase_price = db.Column(db.Float, nullable=False, default=0)
    current_price = db.Column(db.Float, nullable=True)
    current_value = db.Column(db.Float, nullable=True)  # Current price * quantity
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
    __tablename__ = 'investment_categories'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    color = db.Column(db.String(7), default='#0066cc')  # Hex color for display
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    user = db.relationship('User', backref='investment_categories')


class Asset(db.Model):
    __tablename__ = 'assets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)  # e.g., "My House", "Toyota Camry", "Laptop"
    asset_type = db.Column(db.String(50), nullable=False)  # house, lot, vehicle, electronics, jewelry, art, collectible, other
    purchase_price = db.Column(db.Float, nullable=True)  # Original cost
    current_value = db.Column(db.Float, nullable=False, default=0)  # Current estimated value
    purchase_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = db.relationship('User', backref='assets')

    def __repr__(self):
        return f'<Asset {self.name}>'

    def get_gain_loss(self):
        """Calculate gain/loss on asset"""
        if self.purchase_price:
            return self.current_value - self.purchase_price
        return 0

    def get_gain_loss_percentage(self):
        """Calculate gain/loss percentage"""
        if self.purchase_price and self.purchase_price > 0:
            return ((self.current_value - self.purchase_price) / self.purchase_price) * 100
        return 0


class DashboardPreferences(db.Model):
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


class RegexPattern(db.Model):
    __tablename__ = 'regex_patterns'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    pattern = db.Column(db.String(500), nullable=False)
    account_type = db.Column(db.String(50), nullable=True)
    confidence_score = db.Column(db.Float, default=0.5)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='regex_patterns')

    def __repr__(self):
        return f'<RegexPattern {self.pattern}>'


class Feedback(db.Model):
    __tablename__ = 'feedback'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    feedback_type = db.Column(db.String(20), nullable=False)  # bug, feature, improvement, other
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='open')  # open, in_progress, resolved, closed
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref='feedback_items')

    def __repr__(self):
        return f'<Feedback {self.title}>'
