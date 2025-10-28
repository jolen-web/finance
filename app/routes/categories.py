from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Category
from app import db

bp = Blueprint('categories', __name__, url_prefix='/categories')

@bp.route('/')
@login_required
def list_categories():
    """List all categories"""
    categories = Category.query.filter_by(parent_id=None, user_id=current_user.id).all()
    return render_template('categories/list.html', categories=categories)

@bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_category():
    """Create new category"""
    if request.method == 'POST':
        name = request.form.get('name')
        is_income = request.form.get('is_income') == 'on'
        parent_id = request.form.get('parent_id')
        parent_id = int(parent_id) if parent_id else None

        category = Category(
            name=name,
            is_income=is_income,
            parent_id=parent_id,
            user_id=current_user.id
        )

        db.session.add(category)
        db.session.commit()

        flash(f'Category "{name}" created successfully!', 'success')
        return redirect(url_for('categories.list_categories'))

    parent_categories = Category.query.filter_by(parent_id=None, user_id=current_user.id).all()
    return render_template('categories/form.html', category=None, parent_categories=parent_categories)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    """Edit existing category"""
    category = Category.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        category.name = request.form.get('name')
        category.is_income = request.form.get('is_income') == 'on'
        parent_id = request.form.get('parent_id')
        category.parent_id = int(parent_id) if parent_id else None

        db.session.commit()

        flash(f'Category "{category.name}" updated successfully!', 'success')
        return redirect(url_for('categories.list_categories'))

    parent_categories = Category.query.filter_by(parent_id=None, user_id=current_user.id).filter(Category.id != id).all()
    return render_template('categories/form.html', category=category, parent_categories=parent_categories)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_category(id):
    """Delete category"""
    category = Category.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    # Check if category has transactions
    if category.transactions.count() > 0:
        flash(f'Cannot delete category "{category.name}" - it has associated transactions', 'danger')
        return redirect(url_for('categories.list_categories'))

    db.session.delete(category)
    db.session.commit()

    flash(f'Category "{category.name}" deleted successfully!', 'success')
    return redirect(url_for('categories.list_categories'))
