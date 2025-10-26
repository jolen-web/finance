from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user, login_required
from app.models import Transaction, Account, Category
from app import db
from datetime import datetime

bp = Blueprint('transactions', __name__, url_prefix='/transactions')

@bp.route('/')
@login_required
def list_transactions():
    """List all transactions with filtering"""
    page = request.args.get('page', 1, type=int)
    account_id = request.args.get('account_id', type=int)
    category_id = request.args.get('category_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    search = request.args.get('search', '')

    query = Transaction.query

    # Apply filters
    if account_id:
        query = query.filter_by(account_id=account_id)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if start_date:
        query = query.filter(Transaction.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(Transaction.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    if search:
        query = query.filter(Transaction.payee.ilike(f'%{search}%'))

    transactions = query.order_by(Transaction.date.desc()).paginate(
        page=page, per_page=50, error_out=False)

    accounts = Account.query.filter_by(is_active=True).all()
    categories = Category.query.all()

    return render_template('transactions/list.html',
                         transactions=transactions,
                         accounts=accounts,
                         categories=categories)

@bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_transaction():
    """Create new transaction"""
    if request.method == 'POST':
        date_str = request.form.get('date')
        amount = float(request.form.get('amount'))
        payee = request.form.get('payee')
        memo = request.form.get('memo', '')
        transaction_type = request.form.get('transaction_type')
        account_id = int(request.form.get('account_id'))
        category_id = request.form.get('category_id')
        category_id = int(category_id) if category_id else None

        transaction = Transaction(
            date=datetime.strptime(date_str, '%Y-%m-%d').date(),
            amount=amount,
            payee=payee,
            memo=memo,
            transaction_type=transaction_type,
            account_id=account_id,
            category_id=category_id,
            user_id=current_user.id
        )

        db.session.add(transaction)

        # Update account balance
        account = Account.query.get(account_id)
        account.update_balance()

        db.session.commit()

        payee_display = payee if payee else 'Transaction'
        flash(f'{payee_display} added successfully!', 'success')
        return redirect(url_for('transactions.list_transactions'))

    accounts = Account.query.filter_by(is_active=True).all()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('transactions/form.html',
                         transaction=None,
                         accounts=accounts,
                         categories=categories)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_transaction(id):
    """Edit existing transaction"""
    transaction = Transaction.query.get_or_404(id)

    if request.method == 'POST':
        date_str = request.form.get('date')
        transaction.date = datetime.strptime(date_str, '%Y-%m-%d').date()
        transaction.amount = float(request.form.get('amount'))
        transaction.payee = request.form.get('payee')
        transaction.memo = request.form.get('memo', '')
        transaction.transaction_type = request.form.get('transaction_type')
        old_account_id = transaction.account_id
        transaction.account_id = int(request.form.get('account_id'))
        category_id = request.form.get('category_id')
        transaction.category_id = int(category_id) if category_id else None

        # Update balances for affected accounts
        if old_account_id != transaction.account_id:
            old_account = Account.query.get(old_account_id)
            old_account.update_balance()

        account = Account.query.get(transaction.account_id)
        account.update_balance()

        db.session.commit()

        flash(f'Transaction updated successfully!', 'success')
        return redirect(url_for('transactions.list_transactions'))

    accounts = Account.query.filter_by(is_active=True).all()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('transactions/form.html',
                         transaction=transaction,
                         accounts=accounts,
                         categories=categories)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_transaction(id):
    """Delete transaction"""
    transaction = Transaction.query.get_or_404(id)
    account = transaction.account

    db.session.delete(transaction)

    # Update account balance
    account.update_balance()

    db.session.commit()

    flash('Transaction deleted successfully!', 'success')
    return redirect(url_for('transactions.list_transactions'))

@bp.route('/<int:id>/toggle_cleared', methods=['POST'])
@login_required
def toggle_cleared(id):
    """Toggle transaction cleared status"""
    transaction = Transaction.query.get_or_404(id)
    transaction.is_cleared = not transaction.is_cleared
    db.session.commit()

    return redirect(request.referrer or url_for('transactions.list_transactions'))

@bp.route('/<int:id>/toggle_reconciled', methods=['POST'])
@login_required
def toggle_reconciled(id):
    """Toggle transaction reconciled status"""
    transaction = Transaction.query.get_or_404(id)
    transaction.is_reconciled = not transaction.is_reconciled
    if transaction.is_reconciled:
        transaction.is_cleared = True  # Reconciled implies cleared
    db.session.commit()

    return redirect(request.referrer or url_for('transactions.list_transactions'))

@bp.route('/bulk-delete', methods=['POST'])
@login_required
def bulk_delete():
    """Delete multiple transactions at once"""
    try:
        data = request.get_json()
        transaction_ids = data.get('transaction_ids', [])

        if not transaction_ids:
            return jsonify({'error': 'No transactions selected'}), 400

        # Get all transactions to be deleted
        transactions = Transaction.query.filter(Transaction.id.in_(transaction_ids)).all()

        if not transactions:
            return jsonify({'error': 'No transactions found'}), 404

        # Collect affected accounts
        affected_accounts = set()

        # Delete transactions and track affected accounts
        for transaction in transactions:
            affected_accounts.add(transaction.account_id)
            db.session.delete(transaction)

        # Update balances for all affected accounts
        for account_id in affected_accounts:
            account = Account.query.get(account_id)
            if account:
                account.update_balance()

        db.session.commit()

        return jsonify({
            'success': True,
            'deleted_count': len(transactions),
            'message': f'Successfully deleted {len(transactions)} transaction(s)'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
