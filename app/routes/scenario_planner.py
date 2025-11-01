"""Routes for Scenario Planning & Forecasting"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import json
from datetime import datetime
from app import db
from app.models import Scenario
from app.services.scenario_planner import (
    create_scenario,
    delete_scenario,
    get_historical_averages
)

bp = Blueprint('scenario_planner', __name__, url_prefix='/scenario-planner')

@bp.route('/')
def index():
    """Scenario planner dashboard"""
    scenarios = Scenario.query.order_by(Scenario.created_at.desc()).all()

    # Get historical averages for suggestions
    historical = get_historical_averages()

    return render_template('scenario_planner/index.html',
                         scenarios=scenarios,
                         historical=historical)

@bp.route('/new', methods=['GET', 'POST'])
def new_scenario():
    """Create new scenario"""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            scenario_type = request.form.get('scenario_type')
            duration_months = int(request.form.get('duration_months', 12))
            description = request.form.get('description')

            # Build parameters based on scenario type
            parameters = {}

            if scenario_type == 'cash_flow_forecast':
                parameters = {
                    'monthly_income': float(request.form.get('monthly_income', 0)),
                    'income_growth_rate': float(request.form.get('income_growth_rate', 0)),
                    'monthly_expenses': float(request.form.get('monthly_expenses', 0)),
                    'expense_growth_rate': float(request.form.get('expense_growth_rate', 0)),
                    'one_time_expenses': [],
                    'one_time_income': []
                }

            elif scenario_type == 'savings_goal':
                parameters = {
                    'goal_amount': float(request.form.get('goal_amount', 0)),
                    'current_savings': float(request.form.get('current_savings', 0)),
                    'monthly_contribution': float(request.form.get('monthly_contribution', 0)),
                    'interest_rate': float(request.form.get('interest_rate', 0))
                }

            elif scenario_type == 'debt_payoff':
                parameters = {
                    'principal': float(request.form.get('principal', 0)),
                    'annual_interest_rate': float(request.form.get('annual_interest_rate', 0)),
                    'monthly_payment': float(request.form.get('monthly_payment', 0)),
                    'extra_payments': []
                }

            elif scenario_type == 'retirement':
                parameters = {
                    'current_age': int(request.form.get('current_age', 30)),
                    'retirement_age': int(request.form.get('retirement_age', 65)),
                    'current_retirement_savings': float(request.form.get('current_retirement_savings', 0)),
                'monthly_contribution': float(request.form.get('monthly_contribution', 0)),
                'employer_match_pct': float(request.form.get('employer_match_pct', 0)),
                'annual_return': float(request.form.get('annual_return', 7))
            }

            elif scenario_type == 'what_if':
                parameters = {
                    'baseline_income': float(request.form.get('baseline_income', 0)),
                    'baseline_expenses': float(request.form.get('baseline_expenses', 0)),
                    'income_change_pct': float(request.form.get('income_change_pct', 0)),
                    'expense_change_pct': float(request.form.get('expense_change_pct', 0)),
                    'new_expense_amount': float(request.form.get('new_expense_amount', 0)),
                    'new_expense_name': request.form.get('new_expense_name', '')
                }

            scenario = create_scenario(name, scenario_type, duration_months, parameters, description)
            flash(f'Scenario "{name}" created successfully!', 'success')
            return redirect(url_for('scenario_planner.view_scenario', scenario_id=scenario.id))
        except (ValueError, TypeError):
            flash('Invalid numeric values provided. Please check your input.', 'danger')
        except Exception as e:
            flash(f'Error creating scenario: {str(e)}', 'danger')

    # GET request - show form
    historical = get_historical_averages()

    return render_template('scenario_planner/new.html',
                         historical=historical)

@bp.route('/view/<int:scenario_id>')
def view_scenario(scenario_id):
    """View scenario details and results"""
    scenario = Scenario.query.get_or_404(scenario_id)

    # Parse JSON fields
    parameters = json.loads(scenario.parameters)
    results = json.loads(scenario.results)

    return render_template('scenario_planner/view.html',
                         scenario=scenario,
                         parameters=parameters,
                         results=results)

@bp.route('/delete/<int:scenario_id>', methods=['POST'])
def delete(scenario_id):
    """Delete a scenario"""
    if delete_scenario(scenario_id):
        flash('Scenario deleted.', 'success')
    else:
        flash('Error deleting scenario.', 'danger')

    return redirect(url_for('scenario_planner.index'))

@bp.route('/api/historical-averages')
def api_historical_averages():
    """API endpoint for historical averages"""
    return jsonify(get_historical_averages())

@bp.route('/compare')
def compare_scenarios():
    """Compare multiple scenarios side by side"""
    scenario_ids = request.args.getlist('ids', type=int)

    scenarios = []
    for scenario_id in scenario_ids:
        scenario = Scenario.query.get(scenario_id)
        if scenario:
            scenarios.append({
                'scenario': scenario,
                'parameters': json.loads(scenario.parameters),
                'results': json.loads(scenario.results)
            })

    return render_template('scenario_planner/compare.html',
                         scenarios=scenarios)
