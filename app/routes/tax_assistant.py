"""Routes for Tax Preparation Assistant"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response
from datetime import datetime
from app import db
from app.models import TaxTag, Transaction
from app.services.tax_assistant import (
    suggest_tax_deductions,
    add_tax_tag,
    remove_tax_tag,
    get_tax_summary,
    generate_tax_report,
    get_year_end_summary,
    export_tax_data_csv,
    TAX_DEDUCTION_CATEGORIES
)

bp = Blueprint('tax_assistant', __name__, url_prefix='/tax-assistant')

@bp.route('/')
def index():
    """Tax assistant dashboard"""
    # Get current and previous tax years
    current_year = datetime.now().year
    selected_year = int(request.args.get('year', current_year))

    # Get tax summary
    summary = get_tax_summary(selected_year)

    # Get recent tags
    recent_tags = TaxTag.query.filter_by(tax_year=selected_year)\
        .order_by(TaxTag.created_at.desc())\
        .limit(10)\
        .all()

    # Get suggestions count
    suggestions = suggest_tax_deductions(selected_year)
    suggestions_count = len(suggestions)

    # Available years (current and past 5 years)
    available_years = list(range(current_year, current_year - 6, -1))

    return render_template('tax_assistant/index.html',
                         summary=summary,
                         recent_tags=recent_tags,
                         suggestions_count=suggestions_count,
                         selected_year=selected_year,
                         available_years=available_years,
                         deduction_categories=TAX_DEDUCTION_CATEGORIES)

@bp.route('/suggestions')
def suggestions():
    """View suggested tax deductions"""
    current_year = datetime.now().year
    selected_year = int(request.args.get('year', current_year))

    suggestions = suggest_tax_deductions(selected_year)

    # Available years
    available_years = list(range(current_year, current_year - 6, -1))

    return render_template('tax_assistant/suggestions.html',
                         suggestions=suggestions,
                         selected_year=selected_year,
                         available_years=available_years,
                         deduction_categories=TAX_DEDUCTION_CATEGORIES)

@bp.route('/tag', methods=['POST'])
def tag_transaction():
    """Tag a transaction as deductible"""
    transaction_id = request.form.get('transaction_id')
    tax_year = int(request.form.get('tax_year'))
    deduction_type = request.form.get('deduction_type')
    deduction_percentage = int(request.form.get('deduction_percentage', 100))
    notes = request.form.get('notes', '')

    try:
        tag = add_tax_tag(transaction_id, tax_year, deduction_type, deduction_percentage, notes)
        flash(f'Transaction tagged as {deduction_type} deduction.', 'success')
    except Exception as e:
        flash(f'Error tagging transaction: {str(e)}', 'danger')

    # Redirect back
    return redirect(request.referrer or url_for('tax_assistant.index'))

@bp.route('/untag/<int:tag_id>', methods=['POST'])
def untag_transaction(tag_id):
    """Remove tax tag from transaction"""
    if remove_tax_tag(tag_id):
        flash('Tax tag removed.', 'success')
    else:
        flash('Error removing tag.', 'danger')

    return redirect(request.referrer or url_for('tax_assistant.index'))

@bp.route('/tagged-transactions')
def tagged_transactions():
    """View all tagged transactions"""
    current_year = datetime.now().year
    selected_year = int(request.args.get('year', current_year))
    deduction_type = request.args.get('type')

    # Build query
    query = TaxTag.query.filter_by(tax_year=selected_year)

    if deduction_type:
        query = query.filter_by(deduction_type=deduction_type)

    tags = query.order_by(TaxTag.created_at.desc()).all()

    # Calculate totals
    total_deductible = sum(
        abs(tag.transaction.amount) * (tag.deduction_percentage / 100)
        for tag in tags if tag.transaction
    )

    # Available years
    available_years = list(range(current_year, current_year - 6, -1))

    return render_template('tax_assistant/tagged_transactions.html',
                         tags=tags,
                         total_deductible=total_deductible,
                         selected_year=selected_year,
                         available_years=available_years,
                         deduction_categories=TAX_DEDUCTION_CATEGORIES,
                         selected_type=deduction_type)

@bp.route('/year-end-summary')
def year_end_summary():
    """Year-end summary report"""
    current_year = datetime.now().year
    selected_year = int(request.args.get('year', current_year - 1))  # Default to last year

    summary = get_year_end_summary(selected_year)

    # Available years
    available_years = list(range(current_year, current_year - 6, -1))

    return render_template('tax_assistant/year_end_summary.html',
                         summary=summary,
                         selected_year=selected_year,
                         available_years=available_years)

@bp.route('/export/<int:tax_year>')
def export_csv(tax_year):
    """Export tax deductions to CSV"""
    csv_content = export_tax_data_csv(tax_year)

    response = make_response(csv_content)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=tax_deductions_{tax_year}.csv'

    return response

@bp.route('/report/<int:tax_year>')
def tax_report(tax_year):
    """Generate printable tax report"""
    report = generate_tax_report(tax_year, format='detailed')

    return render_template('tax_assistant/report.html',
                         report=report,
                         tax_year=tax_year,
                         deduction_categories=TAX_DEDUCTION_CATEGORIES)

@bp.route('/api/summary/<int:tax_year>')
def api_summary(tax_year):
    """API endpoint for tax summary"""
    summary = get_tax_summary(tax_year)

    return jsonify({
        'tax_year': summary['tax_year'],
        'total_deductions': summary['total_deductions'],
        'total_transactions': summary['total_transactions'],
        'by_type': {k: v['total'] for k, v in summary['by_type'].items()}
    })
