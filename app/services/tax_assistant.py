"""Tax Preparation Assistant Service

Helps track deductible expenses, generate tax reports, and prepare for tax filing.
"""
from datetime import datetime
from collections import defaultdict
from app import db
from app.models import Transaction, Category, TaxTag, Account

# Common tax deduction categories
TAX_DEDUCTION_CATEGORIES = {
    'business_expense': {
        'name': 'Business Expenses',
        'keywords': ['office', 'supplies', 'software', 'equipment', 'advertising', 'marketing'],
        'default_percentage': 100
    },
    'home_office': {
        'name': 'Home Office',
        'keywords': ['internet', 'phone', 'utilities', 'rent', 'mortgage'],
        'default_percentage': 20  # Partial deduction based on home office percentage
    },
    'vehicle': {
        'name': 'Vehicle Expenses',
        'keywords': ['gas', 'fuel', 'parking', 'tolls', 'maintenance', 'insurance', 'car'],
        'default_percentage': 50  # Business use percentage
    },
    'meals': {
        'name': 'Meals & Entertainment',
        'keywords': ['restaurant', 'meal', 'lunch', 'dinner', 'coffee'],
        'default_percentage': 50  # IRS allows 50% for business meals
    },
    'travel': {
        'name': 'Business Travel',
        'keywords': ['hotel', 'flight', 'airbnb', 'lodging', 'airline'],
        'default_percentage': 100
    },
    'education': {
        'name': 'Professional Development',
        'keywords': ['course', 'training', 'conference', 'seminar', 'book', 'education'],
        'default_percentage': 100
    },
    'medical': {
        'name': 'Medical Expenses',
        'keywords': ['doctor', 'hospital', 'pharmacy', 'medical', 'dental', 'prescription'],
        'default_percentage': 100
    },
    'charity': {
        'name': 'Charitable Donations',
        'keywords': ['donation', 'charity', 'nonprofit', 'church'],
        'default_percentage': 100
    }
}

def suggest_tax_deductions(tax_year=None):
    """
    Analyze transactions and suggest potential tax deductions.

    Returns:
        list: Suggested transactions with deduction types
    """
    if tax_year is None:
        tax_year = datetime.now().year

    # Get all transactions for the tax year not already tagged
    start_date = datetime(tax_year, 1, 1)
    end_date = datetime(tax_year, 12, 31)

    # Get already tagged transaction IDs
    tagged_ids = set(tag.transaction_id for tag in TaxTag.query.filter_by(tax_year=tax_year).all())

    transactions = Transaction.query.filter(
        Transaction.date >= start_date,
        Transaction.date <= end_date,
        Transaction.id.not_in(tagged_ids) if tagged_ids else True
    ).all()

    suggestions = []

    for transaction in transactions:
        # Check payee and category against keywords
        payee_lower = (transaction.payee or '').lower()
        category_name = transaction.category.name.lower() if transaction.category else ''
        combined_text = f"{payee_lower} {category_name}"

        for deduction_type, info in TAX_DEDUCTION_CATEGORIES.items():
            for keyword in info['keywords']:
                if keyword in combined_text:
                    suggestions.append({
                        'transaction': transaction,
                        'deduction_type': deduction_type,
                        'deduction_name': info['name'],
                        'suggested_percentage': info['default_percentage'],
                        'deductible_amount': abs(transaction.amount) * (info['default_percentage'] / 100),
                        'match_reason': f"Matched keyword: '{keyword}'"
                    })
                    break  # Only one match per transaction

    return suggestions

def add_tax_tag(transaction_id, tax_year, deduction_type, deduction_percentage=100, notes=None):
    """
    Tag a transaction as tax deductible.

    Args:
        transaction_id: Transaction ID
        tax_year: Tax year (e.g., 2024)
        deduction_type: Type of deduction
        deduction_percentage: Percentage deductible (0-100)
        notes: Optional notes

    Returns:
        TaxTag: Created tag
    """
    # Check if already tagged
    existing = TaxTag.query.filter_by(
        transaction_id=transaction_id,
        tax_year=tax_year
    ).first()

    if existing:
        # Update existing tag
        existing.deduction_type = deduction_type
        existing.deduction_percentage = deduction_percentage
        existing.notes = notes
        db.session.commit()
        return existing

    # Create new tag
    tag = TaxTag(
        transaction_id=transaction_id,
        tax_year=tax_year,
        deduction_type=deduction_type,
        deduction_percentage=deduction_percentage,
        notes=notes
    )
    db.session.add(tag)
    db.session.commit()

    return tag

def remove_tax_tag(tag_id):
    """Remove a tax tag."""
    tag = TaxTag.query.get(tag_id)
    if tag:
        db.session.delete(tag)
        db.session.commit()
        return True
    return False

def get_tax_summary(tax_year):
    """
    Generate comprehensive tax summary for a year.

    Returns:
        dict: Summary with totals by deduction type
    """
    tags = TaxTag.query.filter_by(tax_year=tax_year).all()

    summary = {
        'tax_year': tax_year,
        'total_deductions': 0,
        'by_type': defaultdict(lambda: {'count': 0, 'total': 0, 'transactions': []}),
        'total_transactions': len(tags)
    }

    for tag in tags:
        transaction = tag.transaction
        if not transaction:
            continue

        deductible_amount = abs(transaction.amount) * (tag.deduction_percentage / 100)

        summary['total_deductions'] += deductible_amount
        summary['by_type'][tag.deduction_type]['count'] += 1
        summary['by_type'][tag.deduction_type]['total'] += deductible_amount
        summary['by_type'][tag.deduction_type]['transactions'].append({
            'transaction': transaction,
            'tag': tag,
            'deductible_amount': deductible_amount
        })

    # Convert defaultdict to regular dict
    summary['by_type'] = dict(summary['by_type'])

    return summary

def generate_tax_report(tax_year, format='summary'):
    """
    Generate tax report for export.

    Args:
        tax_year: Tax year
        format: 'summary' or 'detailed'

    Returns:
        dict: Report data
    """
    summary = get_tax_summary(tax_year)

    if format == 'summary':
        # Simple summary by category
        report = {
            'tax_year': tax_year,
            'report_date': datetime.now().strftime('%Y-%m-%d'),
            'categories': []
        }

        for deduction_type, data in summary['by_type'].items():
            category_info = TAX_DEDUCTION_CATEGORIES.get(deduction_type, {})
            report['categories'].append({
                'type': deduction_type,
                'name': category_info.get('name', deduction_type.replace('_', ' ').title()),
                'count': data['count'],
                'total': data['total']
            })

        report['total_deductions'] = summary['total_deductions']
        report['total_transactions'] = summary['total_transactions']

        return report

    elif format == 'detailed':
        # Detailed list of all transactions
        report = {
            'tax_year': tax_year,
            'report_date': datetime.now().strftime('%Y-%m-%d'),
            'transactions': []
        }

        tags = TaxTag.query.filter_by(tax_year=tax_year).order_by(TaxTag.created_at).all()

        for tag in tags:
            transaction = tag.transaction
            if not transaction:
                continue

            deductible_amount = abs(transaction.amount) * (tag.deduction_percentage / 100)

            report['transactions'].append({
                'date': transaction.date.strftime('%Y-%m-%d'),
                'payee': transaction.payee,
                'category': transaction.category.name if transaction.category else 'Uncategorized',
                'amount': abs(transaction.amount),
                'deduction_type': tag.deduction_type,
                'deduction_percentage': tag.deduction_percentage,
                'deductible_amount': deductible_amount,
                'notes': tag.notes or ''
            })

        report['total_deductions'] = sum(t['deductible_amount'] for t in report['transactions'])
        report['total_transactions'] = len(report['transactions'])

        return report

    return {}

def get_year_end_summary(tax_year):
    """
    Generate comprehensive year-end summary for tax prep.

    Returns:
        dict: Year-end financial summary
    """
    start_date = datetime(tax_year, 1, 1)
    end_date = datetime(tax_year, 12, 31)

    # Get all transactions for the year
    transactions = Transaction.query.filter(
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).all()

    # Calculate totals
    total_income = sum(t.amount for t in transactions if t.amount > 0)
    total_expenses = abs(sum(t.amount for t in transactions if t.amount < 0))

    # Get category breakdown
    category_totals = defaultdict(float)
    for t in transactions:
        if t.amount < 0 and t.category:  # Expenses only
            category_totals[t.category.name] += abs(t.amount)

    # Get tax deductions
    tax_summary = get_tax_summary(tax_year)

    return {
        'tax_year': tax_year,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_income': total_income - total_expenses,
        'category_breakdown': dict(sorted(category_totals.items(), key=lambda x: x[1], reverse=True)),
        'tax_deductions': tax_summary['total_deductions'],
        'deductions_by_type': tax_summary['by_type'],
        'accounts_summary': get_accounts_summary()
    }

def get_accounts_summary():
    """Get current balance summary for all accounts."""
    accounts = Account.query.all()
    return {
        'total_balance': sum(acc.current_balance for acc in accounts),
        'by_account': {acc.name: acc.current_balance for acc in accounts}
    }

def export_tax_data_csv(tax_year):
    """
    Export tax deductions to CSV format.

    Returns:
        str: CSV content
    """
    report = generate_tax_report(tax_year, format='detailed')

    csv_lines = [
        'Date,Payee,Category,Amount,Deduction Type,Deduction %,Deductible Amount,Notes'
    ]

    for t in report.get('transactions', []):
        csv_lines.append(
            f"{t['date']},{t['payee']},{t['category']},{t['amount']},"
            f"{t['deduction_type']},{t['deduction_percentage']},{t['deductible_amount']},{t['notes']}"
        )

    csv_lines.append(f"\nTotal Deductions:,,,,,{report['total_deductions']}")

    return '\n'.join(csv_lines)
