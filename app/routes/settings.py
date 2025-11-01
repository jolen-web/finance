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
@login_required
def index():
    """Settings page"""
    settings = load_settings()
    currencies = current_app.config['CURRENCIES']
    current_currency = settings.get('currency')
    if not current_currency:
        current_currency = current_app.config['DEFAULT_CURRENCY']

    categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()

    # Get user's dashboard preferences
    prefs = DashboardPreferences.query.filter_by(user_id=current_user.id).first()

    try:
        return render_template('settings/index.html',
                             settings=settings,
                             currencies=currencies,
                             current_currency=current_currency,
                             categories=categories,
                             prefs=prefs)
    except Exception as e:
        current_app.logger.error(f"Error rendering settings index: {e}", exc_info=True)
        flash('An error occurred while loading the settings page.', 'danger')
        return redirect(url_for('main.index'))

@bp.route('/update', methods=['POST'])
@login_required
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

    # Update default page
    new_default_page = request.form.get('default_page')
    if new_default_page:
        valid_pages = ['dashboard', 'accounts', 'transactions', 'assets', 'investments', 'receipts', 'feedback']
        if new_default_page in valid_pages:
            prefs = DashboardPreferences.query.filter_by(user_id=current_user.id).first()
            if prefs:
                prefs.default_page = new_default_page
                db.session.commit()
                flash(f'Default page updated to {new_default_page.capitalize()}', 'success')
            else:
                flash('User preferences not found', 'danger')
        else:
            flash('Invalid page selection', 'danger')

    return redirect(url_for('settings.index'))

@bp.route('/account-types', methods=['GET', 'POST'])
@login_required
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
@login_required
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

        # Check if category name already exists for this user
        existing = Category.query.filter_by(name=name, user_id=current_user.id).first()
        if existing:
            flash('Category with this name already exists', 'danger')
            return redirect(url_for('settings.index'))

        category = Category(name=name, is_income=is_income, parent_id=parent_id, user_id=current_user.id)
        db.session.add(category)
        db.session.commit()

        flash(f'Category "{name}" created successfully!', 'success')
        return redirect(url_for('settings.index'))

    categories = Category.query.all()
    return render_template('settings/category_form.html', category=None, categories=categories)

@bp.route('/categories/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    category = Category.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        is_income = request.form.get('is_income') == 'on'
        parent_id = request.form.get('parent_id')
        parent_id = int(parent_id) if parent_id else None

        if not name:
            flash('Category name is required', 'danger')
            return redirect(url_for('settings.index'))

        # Check if another category has the same name for this user
        existing = Category.query.filter_by(name=name, user_id=current_user.id).filter(Category.id != id).first()
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
@login_required
def delete_category(id):
    """Delete a category from settings"""
    category = Category.query.filter_by(id=id, user_id=current_user.id).first_or_404()

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

@bp.route('/regex-patterns', methods=['GET', 'POST'])
@login_required
def regex_patterns():
    from app.models import RegexPattern
    patterns = RegexPattern.query.filter_by(user_id=current_user.id).order_by(RegexPattern.created_at.desc()).all()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add' or action == 'edit':
            pattern_id = request.form.get('pattern_id')
            pattern_str = request.form.get('pattern').strip()
            account_type = request.form.get('account_type')

            try:
                confidence_score = float(request.form.get('confidence_score', 0.5))
            except (ValueError, TypeError):
                flash('Confidence score must be a valid number.', 'danger')
                return redirect(url_for('settings.regex_patterns'))

            if not pattern_str:
                flash('Regex pattern cannot be empty.', 'danger')
                return redirect(url_for('settings.regex_patterns'))
            
            if pattern_id: # Edit existing
                regex_pattern = RegexPattern.query.get_or_404(pattern_id)
                if regex_pattern.user_id != current_user.id:
                    flash('Access denied.', 'danger')
                    return redirect(url_for('settings.regex_patterns'))
                regex_pattern.pattern = pattern_str
                regex_pattern.account_type = account_type if account_type else None
                regex_pattern.confidence_score = confidence_score
                flash('Regex pattern updated successfully!', 'success')
            else: # Add new
                regex_pattern = RegexPattern(
                    user_id=current_user.id,
                    pattern=pattern_str,
                    account_type=account_type if account_type else None,
                    confidence_score=confidence_score
                )
                db.session.add(regex_pattern)
                flash('Regex pattern added successfully!', 'success')
            
            db.session.commit()
            return redirect(url_for('settings.regex_patterns'))
            
        elif action == 'delete':
            pattern_id = request.form.get('pattern_id')
            regex_pattern = RegexPattern.query.get_or_404(pattern_id)
            if regex_pattern.user_id != current_user.id:
                flash('Access denied.', 'danger')
                return redirect(url_for('settings.regex_patterns'))
            
            db.session.delete(regex_pattern)
            db.session.commit()
            flash('Regex pattern deleted successfully!', 'success')
            return redirect(url_for('settings.regex_patterns'))
            
    return render_template('settings/regex_patterns.html', patterns=patterns)
