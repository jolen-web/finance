from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.models import Account, Transaction
from app import db, limiter

bp = Blueprint('accounts', __name__, url_prefix='/accounts')

@bp.route('/')
@login_required
def list_accounts():
    """List all accounts"""
    accounts = Account.query.filter_by(user_id=current_user.id, is_active=True).all()
    
    total_assets = 0
    total_liabilities = 0
    for account in accounts:
        if account.account_type == 'credit_card':
            total_liabilities += account.current_balance
        else:
            total_assets += account.current_balance
            
    net_worth = total_assets - total_liabilities
    
    return render_template('accounts/list.html', 
                           accounts=accounts, 
                           total_assets=total_assets,
                           total_liabilities=total_liabilities,
                           net_worth=net_worth)

@bp.route('/new', methods=['GET', 'POST'])
@login_required
@limiter.limit("20 per hour")
def new_account():
    """Create new account"""
    if request.method == 'POST':
        name = request.form.get('name')
        account_type = request.form.get('account_type')
        try:
            starting_balance = float(request.form.get('starting_balance', 0))
        except ValueError:
            flash('Starting balance must be a valid number.', 'danger')
            return redirect(url_for('accounts.new_account'))

        account = Account(
            user_id=current_user.id,
            name=name,
            account_type=account_type,
            starting_balance=starting_balance,
            current_balance=starting_balance
        )

        try:
            db.session.add(account)
            db.session.commit()
            current_app.logger.debug(f"Account '{name}' created with ID: {account.id}")

            flash(f'Account "{name}" created successfully!', 'success')
            return redirect(url_for('accounts.list_accounts'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating account '{name}': {e}", exc_info=True)
            flash(f'Error creating account: {e}', 'danger')
            return redirect(url_for('accounts.new_account'))

    return render_template('accounts/form.html', account=None)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@limiter.limit("20 per hour")
def edit_account(id):
    """Edit existing account"""
    account = Account.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        try:
            starting_balance = float(request.form.get('starting_balance', 0))
        except (ValueError, TypeError):
            flash('Starting balance must be a valid number.', 'danger')
            return redirect(url_for('accounts.edit_account', id=id))

        account.name = request.form.get('name')
        account.account_type = request.form.get('account_type')
        old_starting = account.starting_balance
        account.starting_balance = starting_balance

        # Update current balance if starting balance changed
        if old_starting != account.starting_balance:
            account.update_balance()

        db.session.commit()

        flash(f'Account "{account.name}" updated successfully!', 'success')
        return redirect(url_for('accounts.list_accounts'))

    return render_template('accounts/form.html', account=account)

@bp.route('/<int:id>/delete', methods=['POST'])
@limiter.limit("20 per hour")
@login_required
def delete_account(id):
    """Delete account"""
    account = Account.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    account.is_active = False  # Soft delete
    db.session.commit()

    flash(f'Account "{account.name}" deleted successfully!', 'success')
    return redirect(url_for('accounts.list_accounts'))

@bp.route('/<int:id>')
@login_required
def view_account(id):
    """View account details with transactions"""
    account = Account.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    transactions = account.transactions.all()
    # Sort transactions by date in descending order
    transactions = sorted(transactions, key=lambda t: t.date, reverse=True)
    return render_template('accounts/view.html', account=account, transactions=transactions)
