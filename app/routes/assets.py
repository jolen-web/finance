from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Asset
from app import db
from datetime import datetime

bp = Blueprint('assets', __name__, url_prefix='/assets')

ASSET_TYPES = [
    'house', 'lot', 'vehicle', 'electronics', 'jewelry', 'art', 'collectible', 'other'
]

@bp.route('/')
@login_required
def list_assets():
    """List all assets for current user"""
    page = request.args.get('page', 1, type=int)
    assets = Asset.query.filter_by(user_id=current_user.id).order_by(Asset.created_at.desc()).paginate(
        page=page, per_page=50)

    # Calculate totals
    all_assets = Asset.query.filter_by(user_id=current_user.id).all()
    total_value = sum(asset.current_value for asset in all_assets)
    total_invested = sum(asset.purchase_price or 0 for asset in all_assets)
    total_gain_loss = total_value - total_invested

    return render_template('assets/list.html',
                         assets=assets,
                         total_value=total_value,
                         total_invested=total_invested,
                         total_gain_loss=total_gain_loss,
                         asset_types=ASSET_TYPES)

@bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_asset():
    """Create new asset"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        asset_type = request.form.get('asset_type', '').strip()
        purchase_price = request.form.get('purchase_price')
        current_value = request.form.get('current_value', '0')
        purchase_date = request.form.get('purchase_date')
        notes = request.form.get('notes', '').strip()

        errors = []

        if not name:
            errors.append('Asset name is required')
        if not asset_type or asset_type not in ASSET_TYPES:
            errors.append('Valid asset type is required')

        try:
            current_value = float(current_value)
            if current_value < 0:
                errors.append('Current value cannot be negative')
        except (ValueError, TypeError):
            errors.append('Current value must be a valid number')

        if purchase_price:
            try:
                purchase_price = float(purchase_price)
                if purchase_price < 0:
                    errors.append('Purchase price cannot be negative')
            except (ValueError, TypeError):
                errors.append('Purchase price must be a valid number')
        else:
            purchase_price = None

        # Convert date string to date object
        if purchase_date:
            try:
                purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                errors.append('Purchase date must be in YYYY-MM-DD format')
                purchase_date = None
        else:
            purchase_date = None

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('assets/form.html', asset_types=ASSET_TYPES)

        try:
            asset = Asset(
                user_id=current_user.id,
                name=name,
                asset_type=asset_type,
                purchase_price=purchase_price,
                current_value=current_value,
                purchase_date=purchase_date if purchase_date else None,
                notes=notes
            )
            db.session.add(asset)
            db.session.commit()

            flash(f'Asset "{name}" created successfully!', 'success')
            return redirect(url_for('assets.list_assets'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating asset: {str(e)}', 'danger')
            return render_template('assets/form.html', asset_types=ASSET_TYPES)

    return render_template('assets/form.html', asset_types=ASSET_TYPES)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_asset(id):
    """Edit asset"""
    asset = Asset.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        asset_type = request.form.get('asset_type', '').strip()
        purchase_price = request.form.get('purchase_price')
        current_value = request.form.get('current_value', '0')
        purchase_date = request.form.get('purchase_date')
        notes = request.form.get('notes', '').strip()

        errors = []

        if not name:
            errors.append('Asset name is required')
        if not asset_type or asset_type not in ASSET_TYPES:
            errors.append('Valid asset type is required')

        try:
            current_value = float(current_value)
            if current_value < 0:
                errors.append('Current value cannot be negative')
        except (ValueError, TypeError):
            errors.append('Current value must be a valid number')

        if purchase_price:
            try:
                purchase_price = float(purchase_price)
                if purchase_price < 0:
                    errors.append('Purchase price cannot be negative')
            except (ValueError, TypeError):
                errors.append('Purchase price must be a valid number')
        else:
            purchase_price = None

        # Convert date string to date object
        if purchase_date:
            try:
                purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                errors.append('Purchase date must be in YYYY-MM-DD format')
                purchase_date = None
        else:
            purchase_date = None

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('assets/form.html', asset=asset, asset_types=ASSET_TYPES)

        try:
            asset.name = name
            asset.asset_type = asset_type
            asset.purchase_price = purchase_price
            asset.current_value = current_value
            asset.purchase_date = purchase_date if purchase_date else None
            asset.notes = notes

            db.session.commit()
            flash(f'Asset "{name}" updated successfully!', 'success')
            return redirect(url_for('assets.list_assets'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating asset: {str(e)}', 'danger')
            return render_template('assets/form.html', asset=asset, asset_types=ASSET_TYPES)

    return render_template('assets/form.html', asset=asset, asset_types=ASSET_TYPES)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_asset(id):
    """Delete asset"""
    asset = Asset.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    try:
        asset_name = asset.name
        db.session.delete(asset)
        db.session.commit()
        flash(f'Asset "{asset_name}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting asset: {str(e)}', 'danger')

    return redirect(url_for('assets.list_assets'))
