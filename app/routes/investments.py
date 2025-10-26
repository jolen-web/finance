from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models import Investment, InvestmentCategory, Account
from app import db
from datetime import datetime

bp = Blueprint('investments', __name__, url_prefix='/investments')

@bp.route('/')
def index():
    """Investments dashboard"""
    investments = Investment.query.all()
    categories = InvestmentCategory.query.all()

    # Calculate portfolio totals
    total_invested = sum(inv.purchase_price * inv.quantity for inv in investments if inv.purchase_price and inv.quantity)
    total_current_value = sum(inv.current_value for inv in investments if inv.current_value)
    total_gain_loss = total_current_value - total_invested if total_current_value else 0

    return render_template('investments/index.html',
                         investments=investments,
                         categories=categories,
                         total_invested=total_invested,
                         total_current_value=total_current_value,
                         total_gain_loss=total_gain_loss)

@bp.route('/new', methods=['GET', 'POST'])
def new_investment():
    """Create new investment"""
    categories = InvestmentCategory.query.all()
    accounts = Account.query.filter_by(is_active=True).all()

    if request.method == 'POST':
        name = request.form.get('name')
        ticker = request.form.get('ticker')
        investment_type = request.form.get('investment_type')
        category_id = request.form.get('category_id') or None
        quantity = float(request.form.get('quantity', 0))
        purchase_price = float(request.form.get('purchase_price', 0))
        current_price = request.form.get('current_price')
        current_price = float(current_price) if current_price else None
        purchase_date_str = request.form.get('purchase_date')
        account_id = request.form.get('account_id') or None
        notes = request.form.get('notes')

        # Calculate current value
        current_value = None
        if current_price:
            current_value = current_price * quantity

        # Parse purchase date
        purchase_date = None
        if purchase_date_str:
            purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d').date()

        investment = Investment(
            name=name,
            ticker=ticker,
            investment_type=investment_type,
            category_id=category_id if category_id else None,
            quantity=quantity,
            purchase_price=purchase_price,
            current_price=current_price,
            current_value=current_value,
            purchase_date=purchase_date,
            account_id=account_id if account_id else None,
            notes=notes
        )

        db.session.add(investment)
        db.session.commit()

        flash(f'Investment "{name}" created successfully!', 'success')
        return redirect(url_for('investments.index'))

    return render_template('investments/form.html', investment=None, categories=categories, accounts=accounts)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit_investment(id):
    """Edit investment"""
    investment = Investment.query.get_or_404(id)
    categories = InvestmentCategory.query.all()
    accounts = Account.query.filter_by(is_active=True).all()

    if request.method == 'POST':
        investment.name = request.form.get('name')
        investment.ticker = request.form.get('ticker')
        investment.investment_type = request.form.get('investment_type')
        investment.category_id = request.form.get('category_id') or None
        investment.quantity = float(request.form.get('quantity', 0))
        investment.purchase_price = float(request.form.get('purchase_price', 0))

        current_price = request.form.get('current_price')
        investment.current_price = float(current_price) if current_price else None

        if investment.current_price:
            investment.current_value = investment.current_price * investment.quantity

        purchase_date_str = request.form.get('purchase_date')
        if purchase_date_str:
            investment.purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d').date()

        investment.account_id = request.form.get('account_id') or None
        investment.notes = request.form.get('notes')
        investment.updated_at = datetime.utcnow()

        db.session.commit()

        flash(f'Investment "{investment.name}" updated successfully!', 'success')
        return redirect(url_for('investments.index'))

    return render_template('investments/form.html', investment=investment, categories=categories, accounts=accounts)

@bp.route('/<int:id>/delete', methods=['POST'])
def delete_investment(id):
    """Delete investment"""
    investment = Investment.query.get_or_404(id)
    name = investment.name

    db.session.delete(investment)
    db.session.commit()

    flash(f'Investment "{name}" deleted successfully!', 'success')
    return redirect(url_for('investments.index'))

@bp.route('/categories')
def categories():
    """Manage investment categories"""
    categories = InvestmentCategory.query.all()
    return render_template('investments/categories.html', categories=categories)

@bp.route('/categories/new', methods=['GET', 'POST'])
def new_category():
    """Create new investment category"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        color = request.form.get('color', '#0066cc')

        # Check if category already exists
        existing = InvestmentCategory.query.filter_by(name=name).first()
        if existing:
            flash('Category already exists!', 'danger')
            return redirect(url_for('investments.categories'))

        category = InvestmentCategory(
            name=name,
            description=description,
            color=color
        )

        db.session.add(category)
        db.session.commit()

        flash(f'Category "{name}" created successfully!', 'success')
        return redirect(url_for('investments.categories'))

    return render_template('investments/category_form.html', category=None)

@bp.route('/categories/<int:id>/edit', methods=['GET', 'POST'])
def edit_category(id):
    """Edit investment category"""
    category = InvestmentCategory.query.get_or_404(id)

    if request.method == 'POST':
        category.name = request.form.get('name')
        category.description = request.form.get('description')
        category.color = request.form.get('color')

        db.session.commit()

        flash(f'Category "{category.name}" updated successfully!', 'success')
        return redirect(url_for('investments.categories'))

    return render_template('investments/category_form.html', category=category)

@bp.route('/categories/<int:id>/delete', methods=['POST'])
def delete_category(id):
    """Delete investment category"""
    category = InvestmentCategory.query.get_or_404(id)
    name = category.name

    # Check if category is in use
    investments_count = Investment.query.filter_by(category_id=id).count()
    if investments_count > 0:
        flash(f'Cannot delete category "{name}" - it has {investments_count} investment(s) assigned to it', 'danger')
        return redirect(url_for('investments.categories'))

    db.session.delete(category)
    db.session.commit()

    flash(f'Category "{name}" deleted successfully!', 'success')
    return redirect(url_for('investments.categories'))
