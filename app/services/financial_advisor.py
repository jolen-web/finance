"""
Financial Health Advisor Agent
Analyzes spending patterns and provides personalized financial insights
"""
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from app.models import Transaction, Account, Category, FinancialInsight
from app import db
from collections import defaultdict
import statistics
from flask_login import current_user

class FinancialAdvisorAgent:
    def __init__(self, user_id=None):
        self.insights = []
        self.user_id = user_id

    def analyze_spending_patterns(self, months_back=3):
        """Analyze spending patterns over recent months"""
        cutoff_date = datetime.now() - timedelta(days=months_back * 30)

        # Get transactions by category
        transactions = Transaction.query.filter(
            Transaction.date >= cutoff_date,
            Transaction.transaction_type == 'withdrawal'
        ).all()

        # Group by category and month
        category_spending = defaultdict(lambda: defaultdict(float))

        for trans in transactions:
            if trans.category:
                month_key = trans.date.strftime('%Y-%m')
                category_spending[trans.category.name][month_key] += trans.amount

        return category_spending

    def detect_spending_spikes(self):
        """Detect unusual spending increases"""
        spending = self.analyze_spending_patterns(months_back=3)

        for category, months in spending.items():
            if len(months) < 2:
                continue

            amounts = list(months.values())
            avg = statistics.mean(amounts)
            latest = amounts[-1]

            # Spike if latest month is 40% or more above average
            if latest > avg * 1.4:
                insight = FinancialInsight(
                    insight_type='spending_spike',
                    title=f"Spending spike in {category}",
                    description=f"You spent {latest:.2f} on {category} this month, which is {(latest / avg - 1) * 100:.1f}% above your average of {avg:.2f}.",
                    severity='warning',
                    amount_impact=latest - avg,
                    user_id=self.user_id
                )
                self.insights.append(insight)

    def identify_subscription_creep(self):
        """Find recurring charges that might be forgotten subscriptions"""
        # Get transactions from last 3 months
        cutoff_date = datetime.now() - timedelta(days=90)

        transactions = Transaction.query.filter(
            Transaction.date >= cutoff_date,
            Transaction.transaction_type == 'withdrawal'
        ).all()

        # Group by payee and look for recurring patterns
        payee_charges = defaultdict(list)
        for trans in transactions:
            payee_charges[trans.payee].append((trans.date, trans.amount))

        subscriptions = []
        for payee, charges in payee_charges.items():
            if len(charges) >= 2:
                # Check if amounts are similar
                amounts = [amt for _, amt in charges]
                avg_amt = statistics.mean(amounts)
                std_dev = statistics.stdev(amounts) if len(amounts) > 1 else 0

                # Similar amounts (low variance) suggests subscription
                if std_dev < avg_amt * 0.1:
                    subscriptions.append((payee, avg_amt, len(charges)))

        if subscriptions:
            total_monthly = sum(amt for _, amt, _ in subscriptions)
            insight = FinancialInsight(
                insight_type='subscription_alert',
                title=f"Found {len(subscriptions)} potential subscriptions",
                description=f"You have approximately {total_monthly:.2f} in recurring charges. Review: {', '.join([p for p, _, _ in subscriptions[:5]])}...",
                severity='info',
                amount_impact=total_monthly,
                user_id=self.user_id
            )
            self.insights.append(insight)

    def calculate_savings_rate(self):
        """Calculate monthly savings rate"""
        # Get last month's data
        last_month = datetime.now().replace(day=1) - timedelta(days=1)
        month_start = last_month.replace(day=1)

        income = Transaction.query.filter(
            Transaction.date >= month_start,
            Transaction.date <= last_month,
            Transaction.transaction_type == 'deposit'
        ).with_entities(func.sum(Transaction.amount)).scalar() or 0

        expenses = Transaction.query.filter(
            Transaction.date >= month_start,
            Transaction.date <= last_month,
            Transaction.transaction_type == 'withdrawal'
        ).with_entities(func.sum(Transaction.amount)).scalar() or 0

        if income > 0:
            savings_rate = ((income - expenses) / income) * 100

            if savings_rate < 10:
                severity = 'critical'
                message = "Your savings rate is very low. Try to save at least 20% of your income."
            elif savings_rate < 20:
                severity = 'warning'
                message = "Your savings rate is below recommended 20%. Look for areas to cut back."
            else:
                severity = 'info'
                message = f"Great job! You're saving {savings_rate:.1f}% of your income."

            insight = FinancialInsight(
                insight_type='savings_rate',
                title=f"Savings Rate: {savings_rate:.1f}%",
                description=message,
                severity=severity,
                amount_impact=income - expenses,
                user_id=self.user_id
            )
            self.insights.append(insight)

    def analyze_category_overspending(self, budget_multiplier=1.5):
        """Identify categories where spending exceeds historical average"""
        current_month_start = datetime.now().replace(day=1)
        last_3_months_start = current_month_start - timedelta(days=90)

        # Get current month spending
        current_spending = db.session.query(
            Category.name,
            func.sum(Transaction.amount).label('total')
        ).join(Transaction).filter(
            Transaction.date >= current_month_start,
            Transaction.transaction_type == 'withdrawal'
        ).group_by(Category.name).all()

        # Get average from last 3 months (excluding current)
        historical_spending = db.session.query(
            Category.name,
            func.avg(Transaction.amount).label('avg')
        ).join(Transaction).filter(
            Transaction.date >= last_3_months_start,
            Transaction.date < current_month_start,
            Transaction.transaction_type == 'withdrawal'
        ).group_by(Category.name).all()

        hist_dict = {name: avg for name, avg in historical_spending}

        for category_name, current_total in current_spending:
            if category_name in hist_dict:
                avg = hist_dict[category_name]
                if current_total > avg * budget_multiplier:
                    insight = FinancialInsight(
                        insight_type='overspending',
                        title=f"Overspending in {category_name}",
                        description=f"You've spent {current_total:.2f} on {category_name} this month, "
                                  f"which is {(current_total / avg - 1) * 100:.1f}% above your typical {avg:.2f}.",
                        severity='warning',
                        amount_impact=current_total - avg,
                        user_id=self.user_id
                    )
                    self.insights.append(insight)

    def emergency_fund_check(self):
        """Check if emergency fund is adequate (3-6 months expenses)"""
        # Calculate average monthly expenses from last 6 months
        six_months_ago = datetime.now() - timedelta(days=180)

        # Get monthly totals first, then calculate average
        monthly_totals = db.session.query(
            func.sum(Transaction.amount).label('monthly_total')
        ).filter(
            Transaction.date >= six_months_ago,
            Transaction.amount < 0
        ).group_by(
            extract('year', Transaction.date),
            extract('month', Transaction.date)
        ).all()

        if monthly_totals:
            avg_monthly_expenses = abs(sum(total[0] for total in monthly_totals) / len(monthly_totals))
        else:
            avg_monthly_expenses = 0

        # Get total liquid assets from all accounts
        accounts = Account.query.all()
        total_liquid = sum(acc.current_balance for acc in accounts)

        months_covered = total_liquid / avg_monthly_expenses if avg_monthly_expenses > 0 else 0

        if months_covered < 3:
            severity = 'critical'
            message = f"You only have {months_covered:.1f} months of expenses saved. Build an emergency fund of at least 3-6 months."
        elif months_covered < 6:
            severity = 'warning'
            message = f"You have {months_covered:.1f} months of expenses saved. Try to reach 6 months for better security."
        else:
            severity = 'info'
            message = f"Excellent! You have {months_covered:.1f} months of expenses in your emergency fund."

        insight = FinancialInsight(
            insight_type='emergency_fund',
            title=f"Emergency Fund: {months_covered:.1f} months",
            description=message,
            severity=severity,
            amount_impact=total_liquid,
            user_id=self.user_id
        )
        self.insights.append(insight)

    def generate_all_insights(self):
        """Run all analyses and generate insights"""
        # Clear old insights
        FinancialInsight.query.filter_by(is_dismissed=False).delete()

        # Reset insights list
        self.insights = []

        # Run all analyses
        self.detect_spending_spikes()
        self.identify_subscription_creep()
        self.calculate_savings_rate()
        self.analyze_category_overspending()
        self.emergency_fund_check()

        # Save all insights to database
        for insight in self.insights:
            db.session.add(insight)

        db.session.commit()

        return len(self.insights)

    def get_active_insights(self):
        """Get all non-dismissed insights"""
        return FinancialInsight.query.filter_by(is_dismissed=False).order_by(
            FinancialInsight.created_at.desc()
        ).all()

    def dismiss_insight(self, insight_id):
        """Dismiss an insight"""
        insight = FinancialInsight.query.get(insight_id)
        if insight:
            insight.is_dismissed = True
            db.session.commit()
            return True
        return False


# Standalone wrapper functions for route imports
def generate_all_insights(start_date, end_date, user_id=None):
    """Generate all financial insights for a date range"""
    # Get user_id from current_user if not provided
    if user_id is None and current_user.is_authenticated:
        user_id = current_user.id

    agent = FinancialAdvisorAgent(user_id=user_id)
    agent.generate_all_insights()
    return agent.insights


def detect_spending_spikes(start_date, end_date):
    """Detect spending spikes in categories"""
    cutoff_date = datetime.now() - timedelta(days=90)
    transactions = Transaction.query.filter(Transaction.date >= cutoff_date).all()

    # Group by category and month
    category_spending = defaultdict(lambda: defaultdict(float))

    for trans in transactions:
        if trans.amount < 0 and trans.category:
            month_key = trans.date.strftime('%Y-%m')
            category_spending[trans.category.name][month_key] += abs(trans.amount)

    spikes = []
    for category, months in category_spending.items():
        if len(months) < 2:
            continue

        month_list = sorted(months.items())
        amounts = [amt for _, amt in month_list]

        if len(amounts) >= 2:
            avg_previous = statistics.mean(amounts[:-1])
            current = amounts[-1]

            if current > avg_previous * 1.4:  # 40% spike
                spikes.append({
                    'category_name': category,
                    'previous_amount': avg_previous,
                    'current_amount': current,
                    'increase_amount': current - avg_previous,
                    'percentage_increase': ((current / avg_previous) - 1) * 100
                })

    return spikes


def identify_subscription_creep(start_date, end_date):
    """Find potential recurring subscriptions"""
    cutoff_date = datetime.now() - timedelta(days=90)
    transactions = Transaction.query.filter(
        Transaction.date >= cutoff_date,
        Transaction.amount < 0
    ).all()

    # Group by payee
    payee_charges = defaultdict(list)
    for trans in transactions:
        if trans.payee:
            payee_charges[trans.payee].append(abs(trans.amount))

    subscriptions = []
    for payee, amounts in payee_charges.items():
        if len(amounts) >= 2:
            avg_amt = statistics.mean(amounts)
            std_dev = statistics.stdev(amounts) if len(amounts) > 1 else 0

            # Low variance suggests subscription
            if std_dev < avg_amt * 0.15:
                subscriptions.append({
                    'payee': payee,
                    'avg_amount': avg_amt,
                    'frequency': len(amounts),
                    'total_amount': sum(amounts),
                    'annual_cost': avg_amt * 12
                })

    return sorted(subscriptions, key=lambda x: x['annual_cost'], reverse=True)


def calculate_savings_rate(start_date, end_date):
    """Calculate savings rate for period"""
    income = Transaction.query.filter(
        Transaction.date >= start_date,
        Transaction.date <= end_date,
        Transaction.amount > 0
    ).with_entities(func.sum(Transaction.amount)).scalar() or 0

    expenses = abs(Transaction.query.filter(
        Transaction.date >= start_date,
        Transaction.date <= end_date,
        Transaction.amount < 0
    ).with_entities(func.sum(Transaction.amount)).scalar() or 0)

    if income > 0:
        savings_rate = ((income - expenses) / income) * 100
        net_savings = income - expenses

        if savings_rate < 10:
            recommendation = "Your savings rate is very low. Try to save at least 20% of your income."
        elif savings_rate < 20:
            recommendation = "Your savings rate is below recommended 20%. Look for areas to cut back."
        else:
            recommendation = f"Great job! You're saving {savings_rate:.1f}% of your income."

        return {
            'savings_rate': savings_rate,
            'total_income': income,
            'total_expenses': expenses,
            'net_savings': net_savings,
            'recommendation': recommendation
        }

    return None


def emergency_fund_check():
    """Check emergency fund adequacy"""
    # Calculate average monthly expenses from last 6 months
    six_months_ago = datetime.now() - timedelta(days=180)

    monthly_expenses = []
    current_date = datetime.now()

    for i in range(6):
        month_end = current_date.replace(day=1) - timedelta(days=1)
        month_start = month_end.replace(day=1)

        month_expense = abs(Transaction.query.filter(
            Transaction.date >= month_start,
            Transaction.date <= month_end,
            Transaction.amount < 0
        ).with_entities(func.sum(Transaction.amount)).scalar() or 0)

        monthly_expenses.append(month_expense)
        current_date = month_start

    avg_monthly_expenses = statistics.mean(monthly_expenses) if monthly_expenses else 0

    # Get total balance from all accounts
    accounts = Account.query.all()
    total_balance = sum(acc.current_balance for acc in accounts)

    months_covered = total_balance / avg_monthly_expenses if avg_monthly_expenses > 0 else 0

    if months_covered < 3:
        recommendation = f"You only have {months_covered:.1f} months of expenses saved. Build an emergency fund of at least 3-6 months."
    elif months_covered < 6:
        recommendation = f"You have {months_covered:.1f} months of expenses saved. Try to reach 6 months for better security."
    else:
        recommendation = f"Excellent! You have {months_covered:.1f} months of expenses in your emergency fund."

    return {
        'months_covered': months_covered,
        'total_balance': total_balance,
        'avg_monthly_expenses': avg_monthly_expenses,
        'recommended_amount': avg_monthly_expenses * 6,
        'recommendation': recommendation
    }


def find_duplicate_transactions(start_date, end_date):
    """Find potential duplicate transactions"""
    transactions = Transaction.query.filter(
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).order_by(Transaction.date).all()

    duplicates = []
    seen = defaultdict(list)

    for trans in transactions:
        key = (trans.date.strftime('%Y-%m-%d'), trans.payee, abs(trans.amount))
        seen[key].append(trans)

    for key, trans_list in seen.items():
        if len(trans_list) > 1:
            duplicates.extend(trans_list)

    return duplicates
