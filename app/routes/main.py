from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models import Account, Transaction, DashboardPreferences
from app import db

bp = Blueprint('main', __name__)

@bp.route('/')
@login_required
def index():
    """Dashboard view showing account summary and recent transactions"""
    # Get or create dashboard preferences for user
    prefs = DashboardPreferences.query.first()
    if not prefs:
        prefs = DashboardPreferences()
        db.session.add(prefs)
        db.session.commit()

    accounts = Account.query.filter_by(is_active=True).all()
    recent_transactions = Transaction.query.order_by(Transaction.date.desc()).limit(10).all()

    # Calculate total net worth
    total_assets = sum(acc.current_balance for acc in accounts if acc.account_type in ['checking', 'savings', 'cash'])
    total_liabilities = sum(abs(acc.current_balance) for acc in accounts if acc.account_type == 'credit_card')
    net_worth = total_assets - total_liabilities

    return render_template('dashboard.html',
                         accounts=accounts,
                         recent_transactions=recent_transactions,
                         total_assets=total_assets,
                         total_liabilities=total_liabilities,
                         net_worth=net_worth,
                         prefs=prefs)
