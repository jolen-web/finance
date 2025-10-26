"""Scenario Planning & Forecasting Service

Create financial scenarios, run what-if analyses, and forecast future cash flow.
"""
from datetime import datetime, timedelta
from collections import defaultdict
import json
from app import db
from app.models import Scenario, Transaction, Account, Category

def create_scenario(name, scenario_type, duration_months, parameters, description=None):
    """
    Create a new financial scenario.

    Args:
        name: Scenario name
        scenario_type: Type of scenario (forecast, what_if, goal, retirement, etc.)
        duration_months: How many months to project
        parameters: Dict of scenario parameters
        description: Optional description

    Returns:
        Scenario: Created scenario
    """
    scenario = Scenario(
        name=name,
        scenario_type=scenario_type,
        duration_months=duration_months,
        parameters=json.dumps(parameters),
        description=description
    )

    # Run the scenario calculation
    results = calculate_scenario(scenario_type, duration_months, parameters)
    scenario.results = json.dumps(results)

    db.session.add(scenario)
    db.session.commit()

    return scenario

def calculate_scenario(scenario_type, duration_months, parameters):
    """
    Calculate scenario results based on type and parameters.

    Returns:
        dict: Scenario results
    """
    if scenario_type == 'cash_flow_forecast':
        return forecast_cash_flow(duration_months, parameters)
    elif scenario_type == 'savings_goal':
        return calculate_savings_goal(duration_months, parameters)
    elif scenario_type == 'debt_payoff':
        return calculate_debt_payoff(duration_months, parameters)
    elif scenario_type == 'retirement':
        return calculate_retirement_scenario(duration_months, parameters)
    elif scenario_type == 'what_if':
        return calculate_what_if(duration_months, parameters)
    else:
        return {}

def forecast_cash_flow(months, parameters):
    """
    Forecast future cash flow based on historical data and assumptions.

    Parameters:
        - monthly_income: Expected monthly income
        - income_growth_rate: Annual income growth %
        - monthly_expenses: Expected monthly expenses
        - expense_growth_rate: Annual expense growth %
        - one_time_expenses: List of {month, amount, description}
        - one_time_income: List of {month, amount, description}

    Returns:
        dict: Month-by-month forecast
    """
    monthly_income = parameters.get('monthly_income', 0)
    income_growth = parameters.get('income_growth_rate', 0) / 100 / 12  # Monthly
    monthly_expenses = parameters.get('monthly_expenses', 0)
    expense_growth = parameters.get('expense_growth_rate', 0) / 100 / 12  # Monthly
    one_time_expenses = parameters.get('one_time_expenses', [])
    one_time_income = parameters.get('one_time_income', [])

    # Get current total balance
    accounts = Account.query.all()
    starting_balance = sum(acc.current_balance for acc in accounts)

    forecast = []
    current_balance = starting_balance
    cumulative_income = 0
    cumulative_expenses = 0

    for month in range(1, months + 1):
        # Calculate income for this month
        month_income = monthly_income * (1 + income_growth) ** month

        # Add one-time income
        for item in one_time_income:
            if item.get('month') == month:
                month_income += item.get('amount', 0)

        # Calculate expenses for this month
        month_expenses = monthly_expenses * (1 + expense_growth) ** month

        # Add one-time expenses
        for item in one_time_expenses:
            if item.get('month') == month:
                month_expenses += item.get('amount', 0)

        # Calculate balance
        net_cash_flow = month_income - month_expenses
        current_balance += net_cash_flow

        cumulative_income += month_income
        cumulative_expenses += month_expenses

        forecast.append({
            'month': month,
            'income': round(month_income, 2),
            'expenses': round(month_expenses, 2),
            'net_cash_flow': round(net_cash_flow, 2),
            'balance': round(current_balance, 2)
        })

    return {
        'forecast': forecast,
        'starting_balance': round(starting_balance, 2),
        'ending_balance': round(current_balance, 2),
        'total_income': round(cumulative_income, 2),
        'total_expenses': round(cumulative_expenses, 2),
        'net_change': round(current_balance - starting_balance, 2)
    }

def calculate_savings_goal(months, parameters):
    """
    Calculate how to reach a savings goal.

    Parameters:
        - goal_amount: Target savings amount
        - current_savings: Current savings balance
        - monthly_contribution: How much can be saved per month
        - interest_rate: Annual interest rate %

    Returns:
        dict: Progress towards goal
    """
    goal_amount = parameters.get('goal_amount', 0)
    current_savings = parameters.get('current_savings', 0)
    monthly_contribution = parameters.get('monthly_contribution', 0)
    annual_interest = parameters.get('interest_rate', 0) / 100
    monthly_interest = annual_interest / 12

    progress = []
    balance = current_savings
    months_to_goal = None

    for month in range(1, months + 1):
        # Add interest
        interest_earned = balance * monthly_interest

        # Add contribution
        balance += monthly_contribution + interest_earned

        progress_pct = (balance / goal_amount * 100) if goal_amount > 0 else 0

        progress.append({
            'month': month,
            'balance': round(balance, 2),
            'contribution': round(monthly_contribution, 2),
            'interest_earned': round(interest_earned, 2),
            'progress_percentage': round(progress_pct, 1)
        })

        if months_to_goal is None and balance >= goal_amount:
            months_to_goal = month

    return {
        'goal_amount': goal_amount,
        'starting_balance': current_savings,
        'ending_balance': round(balance, 2),
        'months_to_goal': months_to_goal,
        'goal_achievable': balance >= goal_amount,
        'shortfall': round(max(0, goal_amount - balance), 2),
        'progress': progress
    }

def calculate_debt_payoff(months, parameters):
    """
    Calculate debt payoff schedule.

    Parameters:
        - principal: Debt amount
        - annual_interest_rate: Interest rate %
        - monthly_payment: Payment amount
        - extra_payments: List of {month, amount}

    Returns:
        dict: Payoff schedule
    """
    principal = parameters.get('principal', 0)
    annual_rate = parameters.get('annual_interest_rate', 0) / 100
    monthly_rate = annual_rate / 12
    monthly_payment = parameters.get('monthly_payment', 0)
    extra_payments = parameters.get('extra_payments', [])

    schedule = []
    remaining_balance = principal
    total_interest = 0
    total_paid = 0
    payoff_month = None

    for month in range(1, months + 1):
        if remaining_balance <= 0:
            break

        # Calculate interest for this month
        interest_charge = remaining_balance * monthly_rate

        # Calculate principal payment
        principal_payment = monthly_payment - interest_charge

        # Add extra payments
        extra = 0
        for payment in extra_payments:
            if payment.get('month') == month:
                extra += payment.get('amount', 0)

        principal_payment += extra

        # Don't overpay
        if principal_payment > remaining_balance:
            principal_payment = remaining_balance

        remaining_balance -= principal_payment
        total_interest += interest_charge
        total_paid += monthly_payment + extra

        schedule.append({
            'month': month,
            'payment': round(monthly_payment + extra, 2),
            'principal': round(principal_payment, 2),
            'interest': round(interest_charge, 2),
            'remaining_balance': round(max(0, remaining_balance), 2)
        })

        if payoff_month is None and remaining_balance <= 0:
            payoff_month = month

    return {
        'original_principal': principal,
        'total_paid': round(total_paid, 2),
        'total_interest': round(total_interest, 2),
        'payoff_month': payoff_month,
        'paid_off': remaining_balance <= 0,
        'remaining_balance': round(max(0, remaining_balance), 2),
        'schedule': schedule
    }

def calculate_retirement_scenario(months, parameters):
    """
    Simple retirement savings projection.

    Parameters:
        - current_age: Current age
        - retirement_age: Target retirement age
        - current_retirement_savings: Current 401k/IRA balance
        - monthly_contribution: Monthly retirement contribution
        - employer_match_pct: Employer match %
        - annual_return: Expected annual return %

    Returns:
        dict: Retirement projection
    """
    current_age = parameters.get('current_age', 30)
    retirement_age = parameters.get('retirement_age', 65)
    current_savings = parameters.get('current_retirement_savings', 0)
    monthly_contribution = parameters.get('monthly_contribution', 0)
    employer_match = parameters.get('employer_match_pct', 0) / 100
    annual_return = parameters.get('annual_return', 7) / 100
    monthly_return = annual_return / 12

    years_to_retirement = retirement_age - current_age
    months_to_retirement = years_to_retirement * 12

    # Limit projection to requested months or retirement, whichever is sooner
    projection_months = min(months, months_to_retirement)

    projection = []
    balance = current_savings
    total_contributions = 0
    total_employer_match = 0
    total_growth = 0

    for month in range(1, projection_months + 1):
        # Add contributions
        employee_contrib = monthly_contribution
        employer_contrib = monthly_contribution * employer_match

        # Calculate growth
        growth = balance * monthly_return

        balance += employee_contrib + employer_contrib + growth

        total_contributions += employee_contrib
        total_employer_match += employer_contrib
        total_growth += growth

        age = current_age + (month / 12)

        projection.append({
            'month': month,
            'age': round(age, 1),
            'balance': round(balance, 2),
            'employee_contribution': round(employee_contrib, 2),
            'employer_contribution': round(employer_contrib, 2),
            'growth': round(growth, 2)
        })

    return {
        'current_age': current_age,
        'retirement_age': retirement_age,
        'starting_balance': current_savings,
        'projected_balance_at_retirement': round(balance, 2),
        'total_employee_contributions': round(total_contributions, 2),
        'total_employer_match': round(total_employer_match, 2),
        'total_investment_growth': round(total_growth, 2),
        'projection': projection
    }

def calculate_what_if(months, parameters):
    """
    Generic what-if scenario with customizable changes.

    Parameters:
        - baseline_income: Current monthly income
        - baseline_expenses: Current monthly expenses
        - income_change_pct: % change in income
        - expense_change_pct: % change in expenses
        - new_expense_name: Name of new expense
        - new_expense_amount: Amount of new expense

    Returns:
        dict: What-if results
    """
    baseline_income = parameters.get('baseline_income', 0)
    baseline_expenses = parameters.get('baseline_expenses', 0)
    income_change = parameters.get('income_change_pct', 0) / 100
    expense_change = parameters.get('expense_change_pct', 0) / 100
    new_expense_amount = parameters.get('new_expense_amount', 0)

    new_income = baseline_income * (1 + income_change)
    new_expenses = baseline_expenses * (1 + expense_change) + new_expense_amount

    # Get current balance
    accounts = Account.query.all()
    current_balance = sum(acc.current_balance for acc in accounts)

    projection = []
    balance = current_balance

    for month in range(1, months + 1):
        net_change = new_income - new_expenses
        balance += net_change

        projection.append({
            'month': month,
            'income': round(new_income, 2),
            'expenses': round(new_expenses, 2),
            'net_change': round(net_change, 2),
            'balance': round(balance, 2)
        })

    return {
        'baseline': {
            'income': baseline_income,
            'expenses': baseline_expenses,
            'net': baseline_income - baseline_expenses
        },
        'scenario': {
            'income': round(new_income, 2),
            'expenses': round(new_expenses, 2),
            'net': round(new_income - new_expenses, 2)
        },
        'changes': {
            'income_change': round(new_income - baseline_income, 2),
            'expense_change': round(new_expenses - baseline_expenses, 2),
            'net_change': round((new_income - new_expenses) - (baseline_income - baseline_expenses), 2)
        },
        'starting_balance': current_balance,
        'ending_balance': round(balance, 2),
        'projection': projection
    }

def get_historical_averages():
    """Get historical income and expense averages for baseline scenarios."""
    # Get last 3 months of transactions
    three_months_ago = datetime.now() - timedelta(days=90)
    transactions = Transaction.query.filter(Transaction.date >= three_months_ago).all()

    total_income = sum(t.amount for t in transactions if t.amount > 0)
    total_expenses = abs(sum(t.amount for t in transactions if t.amount < 0))

    avg_monthly_income = total_income / 3
    avg_monthly_expenses = total_expenses / 3

    # Category breakdown
    category_expenses = defaultdict(float)
    for t in transactions:
        if t.amount < 0 and t.category:
            category_expenses[t.category.name] += abs(t.amount)

    return {
        'avg_monthly_income': round(avg_monthly_income, 2),
        'avg_monthly_expenses': round(avg_monthly_expenses, 2),
        'category_breakdown': {k: round(v / 3, 2) for k, v in category_expenses.items()}
    }

def delete_scenario(scenario_id):
    """Delete a scenario."""
    scenario = Scenario.query.get(scenario_id)
    if scenario:
        db.session.delete(scenario)
        db.session.commit()
        return True
    return False
