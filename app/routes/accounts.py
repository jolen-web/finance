from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Account, Transaction
from app import db

bp = Blueprint('accounts', __name__, url_prefix='/accounts')

@bp.route('/')
@login_required
def list_accounts():
    """List all accounts"""
    accounts = Account.query.filter_by(is_active=True).all()
    total_balance = sum(account.current_balance for account in accounts)
    return render_template('accounts/list.html', accounts=accounts, total_balance=total_balance)

@bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_account():
    """Create new account"""
    if request.method == 'POST':
        name = request.form.get('name')
        account_type = request.form.get('account_type')
        starting_balance = float(request.form.get('starting_balance', 0))

        account = Account(
            name=name,
            account_type=account_type,
            starting_balance=starting_balance,
            current_balance=starting_balance
        )

        db.session.add(account)
        db.session.commit()

        flash(f'Account "{name}" created successfully!', 'success')
        return redirect(url_for('accounts.list_accounts'))

    return render_template('accounts/form.html', account=None)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_account(id):
    """Edit existing account"""
    account = Account.query.get_or_404(id)

    if request.method == 'POST':
        account.name = request.form.get('name')
        account.account_type = request.form.get('account_type')
        old_starting = account.starting_balance
        account.starting_balance = float(request.form.get('starting_balance', 0))

        # Update current balance if starting balance changed
        if old_starting != account.starting_balance:
            account.update_balance()

        db.session.commit()

        flash(f'Account "{account.name}" updated successfully!', 'success')
        return redirect(url_for('accounts.list_accounts'))

    return render_template('accounts/form.html', account=account)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_account(id):
    """Delete account"""
    account = Account.query.get_or_404(id)
    account.is_active = False  # Soft delete
    db.session.commit()

    flash(f'Account "{account.name}" deleted successfully!', 'success')
    return redirect(url_for('accounts.list_accounts'))

@bp.route('/<int:id>')
@login_required
def view_account(id):
    """View account details with transactions"""
    account = Account.query.get_or_404(id)
    transactions = account.transactions.all()
    # Sort transactions by date in descending order
    transactions = sorted(transactions, key=lambda t: t.date, reverse=True)
    return render_template('accounts/view.html', account=account, transactions=transactions)
