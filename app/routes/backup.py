from flask import Blueprint, send_file, request, redirect, url_for, flash
from app.models import Account, Transaction, Category
from app import db
import json
import os
from datetime import datetime
from pathlib import Path

bp = Blueprint('backup', __name__, url_prefix='/backup')

@bp.route('/export')
def export_data():
    """Export all data to JSON file"""
    # Gather all data
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    categories = Category.query.filter_by(user_id=current_user.id).all()

    data = {
        'export_date': datetime.utcnow().isoformat(),
        'accounts': [{
            'id': acc.id,
            'name': acc.name,
            'account_type': acc.account_type,
            'starting_balance': acc.starting_balance,
            'current_balance': acc.current_balance,
            'is_active': acc.is_active,
            'created_at': acc.created_at.isoformat()
        } for acc in accounts],
        'categories': [{
            'id': cat.id,
            'name': cat.name,
            'parent_id': cat.parent_id,
            'is_income': cat.is_income,
            'created_at': cat.created_at.isoformat()
        } for cat in categories],
        'transactions': [{
            'id': trans.id,
            'date': trans.date.isoformat(),
            'amount': trans.amount,
            'payee': trans.payee,
            'memo': trans.memo,
            'transaction_type': trans.transaction_type,
            'is_cleared': trans.is_cleared,
            'is_reconciled': trans.is_reconciled,
            'account_id': trans.account_id,
            'category_id': trans.category_id,
            'created_at': trans.created_at.isoformat()
        } for trans in transactions]
    }

    # Create backup file
    backup_dir = Path(__file__).parent.parent.parent / 'data' / 'backups'
    backup_dir.mkdir(exist_ok=True)

    filename = f"finance_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = backup_dir / filename

    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

    return send_file(filepath, as_attachment=True, download_name=filename)

@bp.route('/import', methods=['POST'])
def import_data():
    """Import data from JSON file"""
    if 'backup_file' not in request.files:
        flash('No file selected', 'danger')
        return redirect(url_for('main.index'))

    file = request.files['backup_file']

    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('main.index'))

    if not file.filename.endswith('.json'):
        flash('Invalid file format. Please upload a JSON file', 'danger')
        return redirect(url_for('main.index'))

    try:
        data = json.load(file)

        # Clear existing data (optional - could add option to merge instead)
        if request.form.get('clear_existing') == 'yes':
            Transaction.query.filter_by(user_id=current_user.id).delete()
            Account.query.filter_by(user_id=current_user.id).delete()
            # Don't delete categories as they might be default ones

        # Import accounts
        account_id_map = {}
        for acc_data in data.get('accounts', []):
            old_id = acc_data['id']
            acc = Account(
                user_id=current_user.id,
                name=acc_data['name'],
                account_type=acc_data['account_type'],
                starting_balance=acc_data['starting_balance'],
                current_balance=acc_data['current_balance'],
                is_active=acc_data.get('is_active', True)
            )
            db.session.add(acc)
            db.session.flush()
            account_id_map[old_id] = acc.id

        # Import categories (only if they don't exist)
        category_id_map = {}
        for cat_data in data.get('categories', []):
            old_id = cat_data['id']
            existing = Category.query.filter_by(name=cat_data['name'], user_id=current_user.id).first()
            if existing:
                category_id_map[old_id] = existing.id
            else:
                cat = Category(
                    user_id=current_user.id,
                    name=cat_data['name'],
                    parent_id=cat_data.get('parent_id'),
                    is_income=cat_data.get('is_income', False)
                )
                db.session.add(cat)
                db.session.flush()
                category_id_map[old_id] = cat.id

        # Import transactions
        for trans_data in data.get('transactions', []):
            trans = Transaction(
                user_id=current_user.id,
                date=datetime.fromisoformat(trans_data['date']).date(),
                amount=trans_data['amount'],
                payee=trans_data['payee'],
                memo=trans_data.get('memo'),
                transaction_type=trans_data['transaction_type'],
                is_cleared=trans_data.get('is_cleared', False),
                is_reconciled=trans_data.get('is_reconciled', False),
                account_id=account_id_map.get(trans_data['account_id']),
                category_id=category_id_map.get(trans_data.get('category_id')) if trans_data.get('category_id') else None
            )
            db.session.add(trans)

        db.session.commit()

        flash(f'Data imported successfully! Imported {len(data.get("accounts", []))} accounts, '
              f'{len(data.get("transactions", []))} transactions', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error importing data: {str(e)}', 'danger')

    return redirect(url_for('main.index'))
