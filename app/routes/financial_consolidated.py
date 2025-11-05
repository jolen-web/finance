"""
Consolidated Financial Routes

Combines accounts, transactions, and categories routes into a single
organized blueprint using Phase 2 services.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.models import Account, Transaction, Category
from app import db, limiter
from decimal import Decimal, InvalidOperation

# Import new services from Phase 2
from app.services.financial.account_service import AccountService
from app.services.financial.transaction_service import TransactionService
from app.services.financial.category_service import CategoryService
from app.services.financial.dashboard_service import DashboardService
from app.services.utils.validation_service import ValidationService

bp = Blueprint('financial', __name__, url_prefix='/financial')

# ============================================================================
# ACCOUNT ROUTES
# ============================================================================

@bp.route('/accounts')
@login_required
def list_accounts():
    """List all user accounts with net worth calculation."""
    accounts = AccountService.get_user_accounts(current_user.id)
    net_worth = AccountService.calculate_net_worth(current_user.id)

    total_assets = sum(a.current_balance for a in accounts if a.account_type != 'credit_card')
    total_liabilities = sum(a.current_balance for a in accounts if a.account_type == 'credit_card')

    return render_template('financial/accounts/list.html',
                         accounts=accounts,
                         net_worth=net_worth,
                         total_assets=total_assets,
                         total_liabilities=total_liabilities)

@bp.route('/accounts/new', methods=['GET', 'POST'])
@login_required
@limiter.limit("20 per hour")
def create_account():
    """Create new account."""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            account_type = request.form.get('account_type')
            starting_balance = Decimal(request.form.get('starting_balance', '0'))

            ValidationService.validate_account_name(name)
            ValidationService.validate_amount(starting_balance)

            account = AccountService.create_account(
                current_user.id,
                name,
                account_type,
                starting_balance
            )

            flash(f'Account "{name}" created successfully.', 'success')
            return redirect(url_for('financial.list_accounts'))
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash('Error creating account.', 'danger')

    return render_template('financial/accounts/new.html')

@bp.route('/accounts/<int:account_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_account(account_id):
    """Edit account details."""
    account = AccountService.get_account(account_id)
    if not account or account.user_id != current_user.id:
        flash('Account not found.', 'danger')
        return redirect(url_for('financial.list_accounts'))

    if request.method == 'POST':
        try:
            name = request.form.get('name')
            ValidationService.validate_account_name(name)

            AccountService.update_account(account_id, name=name)
            flash('Account updated successfully.', 'success')
            return redirect(url_for('financial.list_accounts'))
        except ValueError as e:
            flash(str(e), 'danger')

    return render_template('financial/accounts/edit.html', account=account)

@bp.route('/accounts/<int:account_id>/delete', methods=['POST'])
@login_required
def delete_account(account_id):
    """Delete an account."""
    account = AccountService.get_account(account_id)
    if not account or account.user_id != current_user.id:
        flash('Account not found.', 'danger')
        return redirect(url_for('financial.list_accounts'))

    AccountService.delete_account(account_id)
    flash('Account deleted successfully.', 'success')
    return redirect(url_for('financial.list_accounts'))

# ============================================================================
# TRANSACTION ROUTES
# ============================================================================

@bp.route('/transactions')
@login_required
def list_transactions():
    """List all transactions."""
    accounts = AccountService.get_user_accounts(current_user.id)
    all_transactions = []

    for account in accounts:
        transactions = TransactionService.get_account_transactions(account.id)
        all_transactions.extend(transactions)

    # Sort by date descending
    all_transactions.sort(key=lambda t: t.date, reverse=True)

    return render_template('financial/transactions/list.html',
                         transactions=all_transactions)

@bp.route('/transactions/new', methods=['GET', 'POST'])
@login_required
@limiter.limit("30 per hour")
def create_transaction():
    """Create new transaction."""
    accounts = AccountService.get_user_accounts(current_user.id)
    categories = CategoryService.get_user_categories(current_user.id)

    if request.method == 'POST':
        try:
            amount = Decimal(request.form.get('amount', '0'))
            description = request.form.get('description')
            account_id = request.form.get('account_id')
            category_id = request.form.get('category_id') or None
            transaction_type = request.form.get('type', 'expense')

            ValidationService.validate_transaction_data(amount, description, account_id)

            transaction = TransactionService.create_transaction(
                int(account_id),
                amount,
                description,
                category_id,
                transaction_type
            )

            flash('Transaction created successfully.', 'success')
            return redirect(url_for('financial.list_transactions'))
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash('Error creating transaction.', 'danger')

    return render_template('financial/transactions/new.html',
                         accounts=accounts,
                         categories=categories)

@bp.route('/transactions/<int:transaction_id>/toggle-cleared', methods=['POST'])
@login_required
def toggle_cleared(transaction_id):
    """Toggle transaction cleared status."""
    transaction = TransactionService.get_transaction(transaction_id)
    if not transaction:
        return jsonify({'error': 'Transaction not found'}), 404

    TransactionService.toggle_cleared(transaction_id)
    return jsonify({'cleared': transaction.is_cleared})

# ============================================================================
# CATEGORY ROUTES
# ============================================================================

@bp.route('/categories')
@login_required
def list_categories():
    """List all categories."""
    categories = CategoryService.get_user_categories(current_user.id)
    return render_template('financial/categories/list.html', categories=categories)

@bp.route('/categories/new', methods=['GET', 'POST'])
@login_required
@limiter.limit("20 per hour")
def create_category():
    """Create new category."""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            category_type = request.form.get('type', 'expense')
            parent_id = request.form.get('parent_id') or None

            ValidationService.validate_category_name(name)

            category = CategoryService.create_category(
                current_user.id,
                name,
                category_type,
                parent_id
            )

            flash('Category created successfully.', 'success')
            return redirect(url_for('financial.list_categories'))
        except ValueError as e:
            flash(str(e), 'danger')

    parent_categories = CategoryService.get_root_categories(current_user.id)
    return render_template('financial/categories/new.html',
                         parent_categories=parent_categories)

@bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    """Edit category."""
    category = CategoryService.get_category(category_id)
    if not category or category.user_id != current_user.id:
        flash('Category not found.', 'danger')
        return redirect(url_for('financial.list_categories'))

    if request.method == 'POST':
        try:
            name = request.form.get('name')
            ValidationService.validate_category_name(name)

            CategoryService.update_category(category_id, name=name)
            flash('Category updated successfully.', 'success')
            return redirect(url_for('financial.list_categories'))
        except ValueError as e:
            flash(str(e), 'danger')

    return render_template('financial/categories/edit.html', category=category)

@bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
def delete_category(category_id):
    """Delete category."""
    category = CategoryService.get_category(category_id)
    if not category or category.user_id != current_user.id:
        flash('Category not found.', 'danger')
        return redirect(url_for('financial.list_categories'))

    CategoryService.delete_category(category_id)
    flash('Category deleted successfully.', 'success')
    return redirect(url_for('financial.list_categories'))

# ============================================================================
# DASHBOARD ROUTE
# ============================================================================

@bp.route('/dashboard')
@login_required
def dashboard():
    """Financial dashboard with aggregated data."""
    summary = DashboardService.get_dashboard_summary(current_user.id)
    spending_by_category = DashboardService.get_spending_by_category(current_user.id)

    return render_template('financial/dashboard.html',
                         summary=summary,
                         spending_by_category=spending_by_category)
