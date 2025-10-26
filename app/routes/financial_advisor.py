"""Routes for Financial Health Advisor"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user
from datetime import datetime, timedelta
from app import db
from app.models import FinancialInsight, Transaction, Account
from app.services.financial_advisor import (
    generate_all_insights,
    detect_spending_spikes,
    identify_subscription_creep,
    calculate_savings_rate,
    emergency_fund_check,
    find_duplicate_transactions
)

bp = Blueprint('financial_advisor', __name__, url_prefix='/financial-advisor')

@bp.route('/')
def index():
    """Financial advisor dashboard"""
    # Get date range from query params
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)  # Last 90 days by default

    if request.args.get('start_date'):
        start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d')
    if request.args.get('end_date'):
        end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d')

    # Generate fresh insights
    insights = generate_all_insights(start_date, end_date, user_id=current_user.id)

    # Get existing insights from database (last 30 days, not dismissed)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    saved_insights = FinancialInsight.query.filter(
        FinancialInsight.created_at >= thirty_days_ago,
        FinancialInsight.is_dismissed == False
    ).order_by(FinancialInsight.created_at.desc()).all()

    # Group insights by type
    insights_by_type = {
        'critical': [i for i in saved_insights if i.severity == 'critical'],
        'warning': [i for i in saved_insights if i.severity == 'warning'],
        'info': [i for i in saved_insights if i.severity == 'info']
    }

    # Calculate statistics
    total_insights = len(saved_insights)
    critical_count = len(insights_by_type['critical'])
    warning_count = len(insights_by_type['warning'])
    info_count = len(insights_by_type['info'])

    # Get account summary
    accounts = Account.query.all()
    total_balance = sum(acc.current_balance for acc in accounts)

    return render_template('financial_advisor/index.html',
                         insights_by_type=insights_by_type,
                         total_insights=total_insights,
                         critical_count=critical_count,
                         warning_count=warning_count,
                         info_count=info_count,
                         total_balance=total_balance,
                         start_date=start_date,
                         end_date=end_date)

@bp.route('/analyze', methods=['POST'])
def analyze():
    """Run fresh analysis"""
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')

    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    else:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)

    # Generate and save insights
    insights = generate_all_insights(start_date, end_date, user_id=current_user.id)

    flash(f'Analysis complete! Generated {len(insights)} new insights.', 'success')
    return redirect(url_for('financial_advisor.index'))

@bp.route('/insight/<int:insight_id>/dismiss', methods=['POST'])
def dismiss_insight(insight_id):
    """Dismiss an insight"""
    insight = FinancialInsight.query.get_or_404(insight_id)
    insight.is_dismissed = True
    db.session.commit()

    flash('Insight dismissed.', 'success')
    return redirect(url_for('financial_advisor.index'))

@bp.route('/insights/history')
def insights_history():
    """View all insights including dismissed ones"""
    # Get filter parameters
    severity = request.args.get('severity')
    insight_type = request.args.get('type')
    show_dismissed = request.args.get('show_dismissed') == 'true'

    # Build query
    query = FinancialInsight.query

    if severity:
        query = query.filter(FinancialInsight.severity == severity)
    if insight_type:
        query = query.filter(FinancialInsight.insight_type == insight_type)
    if not show_dismissed:
        query = query.filter(FinancialInsight.is_dismissed == False)

    insights = query.order_by(FinancialInsight.created_at.desc()).all()

    # Get unique types for filter dropdown
    insight_types = db.session.query(FinancialInsight.insight_type).distinct().all()
    insight_types = [t[0] for t in insight_types]

    # Statistics
    total_insights = len(insights)
    avg_impact = sum(i.amount_impact for i in insights if i.amount_impact) / max(len([i for i in insights if i.amount_impact]), 1)

    return render_template('financial_advisor/history.html',
                         insights=insights,
                         insight_types=insight_types,
                         total_insights=total_insights,
                         avg_impact=avg_impact,
                         show_dismissed=show_dismissed)

@bp.route('/spending-analysis')
def spending_analysis():
    """Detailed spending analysis"""
    # Get date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)

    if request.args.get('start_date'):
        start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d')
    if request.args.get('end_date'):
        end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d')

    # Run analyses
    spikes = detect_spending_spikes(start_date, end_date)
    subscriptions = identify_subscription_creep(start_date, end_date)
    savings_rate = calculate_savings_rate(start_date, end_date)
    emergency_fund = emergency_fund_check()
    duplicates = find_duplicate_transactions(start_date, end_date)

    return render_template('financial_advisor/spending_analysis.html',
                         spikes=spikes,
                         subscriptions=subscriptions,
                         savings_rate=savings_rate,
                         emergency_fund=emergency_fund,
                         duplicates=duplicates,
                         start_date=start_date,
                         end_date=end_date)

@bp.route('/api/insights/summary')
def api_insights_summary():
    """API endpoint for insights summary"""
    thirty_days_ago = datetime.now() - timedelta(days=30)
    insights = FinancialInsight.query.filter(
        FinancialInsight.created_at >= thirty_days_ago,
        FinancialInsight.is_dismissed == False
    ).all()

    return jsonify({
        'total': len(insights),
        'critical': len([i for i in insights if i.severity == 'critical']),
        'warning': len([i for i in insights if i.severity == 'warning']),
        'info': len([i for i in insights if i.severity == 'info']),
        'total_impact': sum(i.amount_impact for i in insights if i.amount_impact)
    })
