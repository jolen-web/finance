from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.models import Category, DashboardPreferences
from app import db
import json
from pathlib import Path

bp = Blueprint('settings', __name__, url_prefix='/settings')

SETTINGS_FILE = Path(__file__).parent.parent.parent / 'data' / 'settings' / 'app_settings.json'

def load_settings():
    """Load application settings from file"""
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return {'currency': current_app.config['DEFAULT_CURRENCY']}

def save_settings(settings):
    """Save application settings to file"""
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

def get_current_currency():
    """Get the currently selected currency code"""
    settings = load_settings()
    return settings.get('currency', current_app.config['DEFAULT_CURRENCY'])

def get_currency_info(currency_code=None):
    """Get currency information for the current or specified currency"""
    if currency_code is None:
        currency_code = get_current_currency()
    return current_app.config['CURRENCIES'].get(currency_code,
                                                 current_app.config['CURRENCIES']['PHP'])

@bp.route('/')
def index():
    """Settings page"""
    settings = load_settings()
    currencies = current_app.config['CURRENCIES']
    current_currency = settings.get('currency', current_app.config['DEFAULT_CURRENCY'])
    categories = Category.query.all()

    return render_template('settings/index.html',
                         settings=settings,
                         currencies=currencies,
                         current_currency=current_currency,
                         categories=categories)

@bp.route('/update', methods=['POST'])
def update():
    """Update settings"""
    settings = load_settings()

    # Update currency
    new_currency = request.form.get('currency')
    if new_currency in current_app.config['CURRENCIES']:
        settings['currency'] = new_currency
        save_settings(settings)
        flash(f'Currency updated to {current_app.config["CURRENCIES"][new_currency]["name"]}', 'success')
    else:
        flash('Invalid currency selection', 'danger')

    return redirect(url_for('settings.index'))

@bp.route('/account-types', methods=['GET', 'POST'])
def account_types():
    """Manage custom account types"""
    settings = load_settings()

    # Initialize account types if not present
    if 'account_types' not in settings:
        settings['account_types'] = [
            'checking', 'savings', 'credit_card', 'cash', 'digital_wallet'
        ]

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            new_type = request.form.get('new_type', '').lower().strip()
            if new_type and new_type not in settings['account_types']:
                settings['account_types'].append(new_type)
                save_settings(settings)
                flash(f'Account type "{new_type}" added successfully!', 'success')
            else:
                flash('Account type already exists or is invalid', 'danger')

        elif action == 'delete':
            type_to_delete = request.form.get('type_to_delete')
            if type_to_delete in settings['account_types']:
                settings['account_types'].remove(type_to_delete)
                save_settings(settings)
                flash(f'Account type "{type_to_delete}" removed successfully!', 'success')
            else:
                flash('Account type not found', 'danger')

        return redirect(url_for('settings.account_types'))

    return render_template('settings/account_types.html', account_types=settings['account_types'])

@bp.route('/categories/new', methods=['GET', 'POST'])
def new_category():
    """Create a new category from settings"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        is_income = request.form.get('is_income') == 'on'
        parent_id = request.form.get('parent_id')
        parent_id = int(parent_id) if parent_id else None

        if not name:
            flash('Category name is required', 'danger')
            return redirect(url_for('settings.index'))

        # Check if category name already exists
        existing = Category.query.filter_by(name=name).first()
        if existing:
            flash('Category with this name already exists', 'danger')
            return redirect(url_for('settings.index'))

        category = Category(name=name, is_income=is_income, parent_id=parent_id)
        db.session.add(category)
        db.session.commit()

        flash(f'Category "{name}" created successfully!', 'success')
        return redirect(url_for('settings.index'))

    categories = Category.query.all()
    return render_template('settings/category_form.html', category=None, categories=categories)

@bp.route('/categories/<int:id>/edit', methods=['GET', 'POST'])
def edit_category(id):
    """Edit a category from settings"""
    category = Category.query.get_or_404(id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        is_income = request.form.get('is_income') == 'on'
        parent_id = request.form.get('parent_id')
        parent_id = int(parent_id) if parent_id else None

        if not name:
            flash('Category name is required', 'danger')
            return redirect(url_for('settings.index'))

        # Check if another category has the same name
        existing = Category.query.filter_by(name=name).filter(Category.id != id).first()
        if existing:
            flash('Category with this name already exists', 'danger')
            return redirect(url_for('settings.index'))

        category.name = name
        category.is_income = is_income
        category.parent_id = parent_id
        db.session.commit()

        flash(f'Category "{name}" updated successfully!', 'success')
        return redirect(url_for('settings.index'))

    categories = Category.query.all()
    return render_template('settings/category_form.html', category=category, categories=categories)

@bp.route('/categories/<int:id>/delete', methods=['POST'])
def delete_category(id):
    """Delete a category from settings"""
    category = Category.query.get_or_404(id)

    # Check if category has transactions
    if category.transactions.count() > 0:
        flash('Cannot delete category that has associated transactions', 'danger')
        return redirect(url_for('settings.index'))

    # If category has subcategories, don't allow deletion
    if category.subcategories:
        flash('Cannot delete category that has subcategories', 'danger')
        return redirect(url_for('settings.index'))

    name = category.name
    db.session.delete(category)
    db.session.commit()

    flash(f'Category "{name}" deleted successfully!', 'success')
    return redirect(url_for('settings.index'))

@bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard_preferences():
    """Manage dashboard display preferences"""
    prefs = DashboardPreferences.query.filter_by(user_id=current_user.id).first()
    if not prefs:
        prefs = DashboardPreferences(user_id=current_user.id)
        db.session.add(prefs)
        db.session.commit()

    if request.method == 'POST':
        # Update preferences based on form data
        prefs.show_accounts = request.form.get('show_accounts') == 'on'
        prefs.show_transactions = request.form.get('show_transactions') == 'on'
        prefs.show_investments = request.form.get('show_investments') == 'on'
        prefs.show_assets = request.form.get('show_assets') == 'on'
        prefs.show_receipts = request.form.get('show_receipts') == 'on'

        db.session.commit()
        flash('Dashboard preferences updated successfully!', 'success')
        return redirect(url_for('settings.dashboard_preferences'))

    return render_template('settings/dashboard.html', prefs=prefs)
