#!/usr/bin/env python
"""
Rental Property Tracker
Comprehensive tool for tracking rental property financials including:
- Cost basis (land and building acquisition)
- Construction in Progress (CIP) tracking
- Financing and loan amortization
- Key dates for tax depreciation
- Operating income and expenses
- Depreciation calculations
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
import csv


@dataclass
class PropertyCost:
    """Individual cost item for property acquisition or construction"""
    description: str
    amount: float
    date: str  # YYYY-MM-DD format
    category: str  # 'land', 'building', 'materials', 'labor', 'permits', 'other'
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LoanRecord:
    """Loan/financing details"""
    lender_name: str
    loan_amount: float
    interest_rate: float  # annual percentage
    loan_term_years: int
    start_date: str  # YYYY-MM-DD
    loan_type: str  # 'mortgage', 'construction', 'personal', 'other'
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LoanPayment:
    """Individual loan payment record"""
    loan_id: int
    payment_date: str  # YYYY-MM-DD
    principal: float
    interest: float
    balance: float
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OperatingExpense:
    """Operating expense item"""
    description: str
    amount: float
    date: str  # YYYY-MM-DD
    category: str  # 'maintenance', 'repairs', 'utilities', 'insurance', 'property_tax', 'hoa', 'management', 'other'
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RentalIncome:
    """Rental income record"""
    amount: float
    date: str  # YYYY-MM-DD
    tenant_name: str = ""
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PropertyKeyDates:
    """Key dates for tax and depreciation purposes"""
    purchase_date: str  # YYYY-MM-DD
    placed_in_service_date: str  # YYYY-MM-DD - when ready for rental
    construction_start: Optional[str] = None  # YYYY-MM-DD
    construction_end: Optional[str] = None  # YYYY-MM-DD
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RentalPropertyTracker:
    """Main class for tracking rental property finances"""

    def __init__(self, property_name: str, data_dir: str = "data/rental_properties"):
        """
        Initialize tracker for a rental property

        Args:
            property_name: Name/identifier for the property
            data_dir: Directory to store property data
        """
        self.property_name = property_name
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.property_file = self.data_dir / f"{property_name}.json"
        self.property_data = self._load_property_data()

    def _load_property_data(self) -> Dict[str, Any]:
        """Load existing property data or create new structure"""
        if self.property_file.exists():
            with open(self.property_file, 'r') as f:
                return json.load(f)

        return {
            'property_name': self.property_name,
            'created_date': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'land_costs': [],
            'building_costs': [],
            'construction_in_progress': [],
            'loans': [],
            'loan_payments': [],
            'key_dates': {},
            'operating_expenses': [],
            'rental_income': [],
            'depreciation_start_date': None,
            'building_basis': 0.0,
            'land_basis': 0.0
        }

    def _save_property_data(self) -> None:
        """Save property data to JSON file"""
        self.property_data['last_updated'] = datetime.now().isoformat()
        with open(self.property_file, 'w') as f:
            json.dump(self.property_data, f, indent=2, default=str)

    def add_land_cost(self, description: str, amount: float, date: str, notes: str = "") -> Dict[str, Any]:
        """
        Add land acquisition cost

        Args:
            description: Description of the land cost
            amount: Cost amount in dollars
            date: Date in YYYY-MM-DD format
            notes: Additional notes

        Returns:
            The added cost item
        """
        cost = PropertyCost(
            description=description,
            amount=amount,
            date=date,
            category='land',
            notes=notes
        )
        self.property_data['land_costs'].append(cost.to_dict())
        self._save_property_data()
        return cost.to_dict()

    def add_building_cost(self, description: str, amount: float, date: str, notes: str = "") -> Dict[str, Any]:
        """
        Add building acquisition or improvement cost

        Args:
            description: Description of the building cost
            amount: Cost amount in dollars
            date: Date in YYYY-MM-DD format
            notes: Additional notes

        Returns:
            The added cost item
        """
        cost = PropertyCost(
            description=description,
            amount=amount,
            date=date,
            category='building',
            notes=notes
        )
        self.property_data['building_costs'].append(cost.to_dict())
        self._save_property_data()
        return cost.to_dict()

    def add_construction_in_progress(self, description: str, amount: float, date: str,
                                    cost_type: str = 'labor', notes: str = "") -> Dict[str, Any]:
        """
        Add Construction in Progress (CIP) cost during construction phase

        Args:
            description: Description of the CIP cost
            amount: Cost amount in dollars
            date: Date in YYYY-MM-DD format
            cost_type: Type of CIP cost ('materials', 'labor', 'permits', 'other')
            notes: Additional notes

        Returns:
            The added CIP item
        """
        cost = PropertyCost(
            description=description,
            amount=amount,
            date=date,
            category=cost_type,
            notes=notes
        )
        self.property_data['construction_in_progress'].append(cost.to_dict())
        self._save_property_data()
        return cost.to_dict()

    def add_loan_record(self, lender_name: str, loan_amount: float, interest_rate: float,
                       loan_term_years: int, start_date: str, loan_type: str = 'mortgage',
                       notes: str = "") -> Dict[str, Any]:
        """
        Add loan/financing record

        Args:
            lender_name: Name of lender
            loan_amount: Total loan amount
            interest_rate: Annual interest rate (as percentage, e.g., 5.5)
            loan_term_years: Loan term in years
            start_date: Loan start date in YYYY-MM-DD format
            loan_type: Type of loan ('mortgage', 'construction', 'personal', 'other')
            notes: Additional notes

        Returns:
            The added loan record
        """
        loan = LoanRecord(
            lender_name=lender_name,
            loan_amount=loan_amount,
            interest_rate=interest_rate,
            loan_term_years=loan_term_years,
            start_date=start_date,
            loan_type=loan_type,
            notes=notes
        )
        self.property_data['loans'].append(loan.to_dict())
        self._save_property_data()
        return loan.to_dict()

    def add_loan_payment(self, loan_id: int, payment_date: str, principal: float,
                        interest: float, balance: float, notes: str = "") -> Dict[str, Any]:
        """
        Record a loan payment

        Args:
            loan_id: ID of the loan (index in loans list)
            payment_date: Payment date in YYYY-MM-DD format
            principal: Principal portion of payment
            interest: Interest portion of payment
            balance: Remaining balance after payment
            notes: Additional notes

        Returns:
            The added payment record
        """
        payment = LoanPayment(
            loan_id=loan_id,
            payment_date=payment_date,
            principal=principal,
            interest=interest,
            balance=balance,
            notes=notes
        )
        self.property_data['loan_payments'].append(payment.to_dict())
        self._save_property_data()
        return payment.to_dict()

    def set_key_dates(self, purchase_date: str, placed_in_service_date: str,
                     construction_start: Optional[str] = None,
                     construction_end: Optional[str] = None,
                     notes: str = "") -> Dict[str, Any]:
        """
        Set key dates for tax and depreciation purposes

        Args:
            purchase_date: Property purchase date in YYYY-MM-DD format
            placed_in_service_date: When property was ready for rental in YYYY-MM-DD format
            construction_start: Construction start date if applicable
            construction_end: Construction end date if applicable
            notes: Additional notes

        Returns:
            The key dates record
        """
        key_dates = PropertyKeyDates(
            purchase_date=purchase_date,
            placed_in_service_date=placed_in_service_date,
            construction_start=construction_start,
            construction_end=construction_end,
            notes=notes
        )
        self.property_data['key_dates'] = key_dates.to_dict()
        self.property_data['depreciation_start_date'] = placed_in_service_date
        self._save_property_data()
        return key_dates.to_dict()

    def add_operating_expense(self, description: str, amount: float, date: str,
                             category: str = 'other', notes: str = "") -> Dict[str, Any]:
        """
        Add operating expense

        Args:
            description: Description of expense
            amount: Expense amount in dollars
            date: Date in YYYY-MM-DD format
            category: Expense category ('maintenance', 'repairs', 'utilities', 'insurance',
                     'property_tax', 'hoa', 'management', 'other')
            notes: Additional notes

        Returns:
            The added expense
        """
        expense = OperatingExpense(
            description=description,
            amount=amount,
            date=date,
            category=category,
            notes=notes
        )
        self.property_data['operating_expenses'].append(expense.to_dict())
        self._save_property_data()
        return expense.to_dict()

    def add_rental_income(self, amount: float, date: str, tenant_name: str = "",
                         notes: str = "") -> Dict[str, Any]:
        """
        Record rental income

        Args:
            amount: Rental income amount in dollars
            date: Date in YYYY-MM-DD format
            tenant_name: Name of tenant if applicable
            notes: Additional notes

        Returns:
            The added income record
        """
        income = RentalIncome(
            amount=amount,
            date=date,
            tenant_name=tenant_name,
            notes=notes
        )
        self.property_data['rental_income'].append(income.to_dict())
        self._save_property_data()
        return income.to_dict()

    def calculate_total_cost_basis(self) -> Dict[str, float]:
        """
        Calculate total cost basis broken down by category

        Returns:
            Dictionary with land_basis, building_basis, cip_basis, and total
        """
        land_total = sum(c['amount'] for c in self.property_data['land_costs'])
        building_total = sum(c['amount'] for c in self.property_data['building_costs'])
        cip_total = sum(c['amount'] for c in self.property_data['construction_in_progress'])

        total = land_total + building_total + cip_total

        # Update in property data for depreciation calculations
        self.property_data['land_basis'] = land_total
        self.property_data['building_basis'] = building_total + cip_total
        self._save_property_data()

        return {
            'land_basis': land_total,
            'building_basis': building_total,
            'cip_basis': cip_total,
            'total_cost_basis': total
        }

    def calculate_depreciation(self, year: Optional[int] = None, method: str = 'straight_line') -> Dict[str, Any]:
        """
        Calculate depreciation for the property

        Args:
            year: Specific year to calculate depreciation for (if None, uses current year)
            method: Depreciation method ('straight_line' is standard for residential)

        Returns:
            Dictionary with depreciation calculations and details
        """
        if not self.property_data['depreciation_start_date']:
            return {'error': 'Depreciation start date not set. Use set_key_dates() first.'}

        start_date = datetime.strptime(self.property_data['depreciation_start_date'], '%Y-%m-%d')
        current_year = year or datetime.now().year

        # Residential property depreciation: 27.5 years
        # Non-residential: 39 years (using residential as default)
        depreciation_life = 27.5

        building_basis = self.property_data['building_basis']

        if method == 'straight_line':
            annual_depreciation = building_basis / depreciation_life

            # Calculate years in service from start_date to current year (only completed years)
            years_completed = current_year - start_date.year - 1 if start_date.month <= datetime.now().month else current_year - start_date.year - 1
            if start_date.year < current_year or (start_date.year == current_year):
                years_completed = max(0, current_year - start_date.year)

            # For accumulated: count from placed in service to end of previous year
            if start_date.year == current_year:
                # Placed in service in current year
                months_in_service_this_year = 12 - start_date.month + 1
                total_accumulated = (annual_depreciation / 12) * months_in_service_this_year
                current_year_depreciation = total_accumulated
            else:
                # Calculate full years of depreciation
                full_years = current_year - start_date.year
                total_accumulated = annual_depreciation * (full_years - 1)
                # Add partial year for placement month
                months_first_year = 12 - start_date.month + 1
                total_accumulated += (annual_depreciation / 12) * months_first_year
                # Add current year
                current_year_depreciation = annual_depreciation

            return {
                'depreciation_method': 'straight_line',
                'depreciation_life_years': depreciation_life,
                'building_basis': building_basis,
                'land_basis': self.property_data['land_basis'],
                'depreciation_start_date': self.property_data['depreciation_start_date'],
                'annual_depreciation': annual_depreciation,
                'current_year_depreciation': current_year_depreciation,
                'total_accumulated_depreciation': total_accumulated,
                'remaining_depreciable_basis': building_basis - total_accumulated,
                'years_in_service': round(current_year - start_date.year, 2)
            }

        return {'error': f'Depreciation method "{method}" not supported'}

    def calculate_operating_income(self, start_date: Optional[str] = None,
                                  end_date: Optional[str] = None) -> Dict[str, float]:
        """
        Calculate operating income and expenses for a date range

        Args:
            start_date: Start date in YYYY-MM-DD format (if None, uses earliest)
            end_date: End date in YYYY-MM-DD format (if None, uses latest)

        Returns:
            Dictionary with gross rental income, total expenses, and net operating income
        """
        income_items = self.property_data['rental_income']
        expense_items = self.property_data['operating_expenses']

        # Filter by date range if provided
        if start_date:
            income_items = [i for i in income_items if i['date'] >= start_date]
            expense_items = [e for e in expense_items if e['date'] >= start_date]

        if end_date:
            income_items = [i for i in income_items if i['date'] <= end_date]
            expense_items = [e for e in expense_items if e['date'] <= end_date]

        gross_income = sum(i['amount'] for i in income_items)
        total_expenses = sum(e['amount'] for e in expense_items)

        # Calculate by category
        expenses_by_category = {}
        for expense in expense_items:
            category = expense['category']
            expenses_by_category[category] = expenses_by_category.get(category, 0) + expense['amount']

        return {
            'gross_rental_income': gross_income,
            'total_operating_expenses': total_expenses,
            'net_operating_income': gross_income - total_expenses,
            'expenses_by_category': expenses_by_category,
            'income_count': len(income_items),
            'expense_count': len(expense_items)
        }

    def get_loan_summary(self) -> Dict[str, Any]:
        """
        Get summary of all loans

        Returns:
            Dictionary with loan details and balances
        """
        loans = self.property_data['loans']
        payments = self.property_data['loan_payments']

        summary = {
            'total_loans': len(loans),
            'loans': []
        }

        for idx, loan in enumerate(loans):
            loan_payments = [p for p in payments if p['loan_id'] == idx]
            total_paid = sum(p['principal'] + p['interest'] for p in loan_payments)

            latest_payment = loan_payments[-1] if loan_payments else None
            current_balance = latest_payment['balance'] if latest_payment else loan['loan_amount']

            summary['loans'].append({
                'loan_id': idx,
                'lender_name': loan['lender_name'],
                'loan_type': loan['loan_type'],
                'original_amount': loan['loan_amount'],
                'interest_rate': loan['interest_rate'],
                'loan_term_years': loan['loan_term_years'],
                'start_date': loan['start_date'],
                'total_payments_made': len(loan_payments),
                'total_paid': total_paid,
                'current_balance': current_balance,
                'notes': loan.get('notes', '')
            })

        summary['total_original_loans'] = sum(l['loan_amount'] for l in loans)
        summary['total_current_balance'] = sum(l['current_balance'] for l in summary['loans'])

        return summary

    def generate_tax_report(self, year: int) -> Dict[str, Any]:
        """
        Generate a tax report for the property

        Args:
            year: Tax year to report on

        Returns:
            Dictionary with tax-relevant information
        """
        # Date range for the tax year
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"

        operating_income = self.calculate_operating_income(start_date, end_date)
        depreciation = self.calculate_depreciation(year)
        loans = self.get_loan_summary()

        # Find interest paid in this year
        interest_paid = 0
        for payment in self.property_data['loan_payments']:
            if start_date <= payment['payment_date'] <= end_date:
                interest_paid += payment['interest']

        # Find property taxes paid in this year
        property_taxes = 0
        for expense in self.property_data['operating_expenses']:
            if expense['category'] == 'property_tax' and start_date <= expense['date'] <= end_date:
                property_taxes += expense['amount']

        return {
            'tax_year': year,
            'property_name': self.property_name,
            'rental_income': operating_income['gross_rental_income'],
            'operating_expenses': operating_income['total_operating_expenses'],
            'expenses_by_category': operating_income['expenses_by_category'],
            'net_operating_income': operating_income['net_operating_income'],
            'depreciation_expense': depreciation.get('current_year_depreciation', 0) if 'current_year_depreciation' in depreciation else 0,
            'interest_paid': interest_paid,
            'property_taxes_paid': property_taxes,
            'taxable_income': (
                operating_income['net_operating_income'] -
                depreciation.get('current_year_depreciation', 0) if 'current_year_depreciation' in depreciation else operating_income['net_operating_income']
            ),
            'cost_basis': self.calculate_total_cost_basis(),
            'depreciation_summary': depreciation,
            'loan_summary': loans
        }

    def list_properties(self) -> List[str]:
        """
        List all tracked properties

        Returns:
            List of property files
        """
        properties = []
        for file in self.data_dir.glob("*.json"):
            properties.append(file.stem)
        return properties

    def print_summary(self) -> None:
        """Print a text summary of the property"""
        print(f"\n{'='*60}")
        print(f"RENTAL PROPERTY SUMMARY: {self.property_name}")
        print(f"{'='*60}")

        # Cost basis
        basis = self.calculate_total_cost_basis()
        print(f"\nCOST BASIS:")
        print(f"  Land: ${basis['land_basis']:,.2f}")
        print(f"  Building: ${basis['building_basis']:,.2f}")
        print(f"  CIP: ${basis['cip_basis']:,.2f}")
        print(f"  Total: ${basis['total_cost_basis']:,.2f}")

        # Depreciation
        depreciation = self.calculate_depreciation()
        if 'error' not in depreciation:
            print(f"\nDEPRECIATION (27.5-year):")
            print(f"  Annual: ${depreciation['annual_depreciation']:,.2f}")
            print(f"  Accumulated: ${depreciation['total_accumulated_depreciation']:,.2f}")
            print(f"  Remaining basis: ${depreciation['remaining_depreciable_basis']:,.2f}")

        # Operating income
        operating = self.calculate_operating_income()
        print(f"\nOPERATING INCOME:")
        print(f"  Gross rental income: ${operating['gross_rental_income']:,.2f}")
        print(f"  Total expenses: ${operating['total_operating_expenses']:,.2f}")
        print(f"  Net operating income: ${operating['net_operating_income']:,.2f}")

        # Loans
        loans = self.get_loan_summary()
        if loans['loans']:
            print(f"\nFINANCING:")
            print(f"  Total loans: {loans['total_loans']}")
            print(f"  Original loan amount: ${loans['total_original_loans']:,.2f}")
            print(f"  Current balance: ${loans['total_current_balance']:,.2f}")

        print(f"\n{'='*60}\n")

    def export_to_csv(self, filename: str = None) -> str:
        """
        Export property data to CSV file

        Args:
            filename: Output filename (if None, generates default)

        Returns:
            Path to exported file
        """
        if filename is None:
            filename = f"{self.property_name}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        filepath = self.data_dir / filename

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)

            # Summary section
            writer.writerow(['RENTAL PROPERTY TRACKER EXPORT'])
            writer.writerow(['Property Name', self.property_name])
            writer.writerow(['Export Date', datetime.now().isoformat()])
            writer.writerow([])

            # Cost basis
            basis = self.calculate_total_cost_basis()
            writer.writerow(['COST BASIS'])
            writer.writerow(['Category', 'Amount'])
            writer.writerow(['Land', basis['land_basis']])
            writer.writerow(['Building', basis['building_basis']])
            writer.writerow(['CIP', basis['cip_basis']])
            writer.writerow(['Total', basis['total_cost_basis']])
            writer.writerow([])

            # Operating income
            operating = self.calculate_operating_income()
            writer.writerow(['OPERATING INCOME'])
            writer.writerow(['Description', 'Amount'])
            writer.writerow(['Gross Rental Income', operating['gross_rental_income']])
            writer.writerow(['Total Expenses', operating['total_operating_expenses']])
            writer.writerow(['Net Operating Income', operating['net_operating_income']])
            writer.writerow([])

            # Expenses by category
            if operating['expenses_by_category']:
                writer.writerow(['EXPENSES BY CATEGORY'])
                writer.writerow(['Category', 'Amount'])
                for category, amount in operating['expenses_by_category'].items():
                    writer.writerow([category, amount])
                writer.writerow([])

            # Depreciation
            depreciation = self.calculate_depreciation()
            if 'error' not in depreciation:
                writer.writerow(['DEPRECIATION'])
                writer.writerow(['Description', 'Amount'])
                writer.writerow(['Annual Depreciation', depreciation['annual_depreciation']])
                writer.writerow(['Accumulated Depreciation', depreciation['total_accumulated_depreciation']])
                writer.writerow(['Remaining Basis', depreciation['remaining_depreciable_basis']])
                writer.writerow([])

        return str(filepath)


def main():
    """CLI interface for the rental property tracker"""
    parser = argparse.ArgumentParser(
        description="Rental Property Tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python rental_property_tracker.py --create "Beach House"
  python rental_property_tracker.py --property "Beach House" --add-land "Land acquisition" 250000 "2020-01-15"
  python rental_property_tracker.py --property "Beach House" --add-building "Building cost" 400000 "2020-02-01"
  python rental_property_tracker.py --property "Beach House" --set-dates "2020-01-15" "2020-06-01"
  python rental_property_tracker.py --property "Beach House" --add-expense "Insurance" 1200 "2024-01-01" --category "insurance"
  python rental_property_tracker.py --property "Beach House" --depreciation
  python rental_property_tracker.py --property "Beach House" --tax-report 2024
  python rental_property_tracker.py --property "Beach House" --summary
  python rental_property_tracker.py --list
        """
    )

    parser.add_argument('--property', type=str, help='Property name to work with')
    parser.add_argument('--create', type=str, help='Create new property')
    parser.add_argument('--list', action='store_true', help='List all properties')
    parser.add_argument('--summary', action='store_true', help='Show property summary')

    # Cost basis
    parser.add_argument('--add-land', type=str, help='Add land cost (description)')
    parser.add_argument('--add-building', type=str, help='Add building cost (description)')
    parser.add_argument('--add-cip', type=str, help='Add construction in progress cost (description)')
    parser.add_argument('--amount', type=float, help='Cost amount for --add-* commands')
    parser.add_argument('--date', type=str, help='Cost date (YYYY-MM-DD)')
    parser.add_argument('--cip-type', type=str, default='labor',
                       help='CIP cost type: labor, materials, permits, other')

    # Loans
    parser.add_argument('--add-loan', type=str, help='Add loan (lender name)')
    parser.add_argument('--loan-amount', type=float, help='Loan amount')
    parser.add_argument('--loan-rate', type=float, help='Annual interest rate')
    parser.add_argument('--loan-term', type=int, help='Loan term in years')
    parser.add_argument('--loan-type', type=str, default='mortgage',
                       help='Loan type: mortgage, construction, personal, other')

    # Key dates
    parser.add_argument('--set-dates', action='store_true', help='Set key dates')
    parser.add_argument('--purchase-date', type=str, help='Purchase date (YYYY-MM-DD)')
    parser.add_argument('--service-date', type=str, help='Placed in service date (YYYY-MM-DD)')
    parser.add_argument('--construction-start', type=str, help='Construction start date')
    parser.add_argument('--construction-end', type=str, help='Construction end date')

    # Operating expenses and income
    parser.add_argument('--add-expense', type=str, help='Add operating expense (description)')
    parser.add_argument('--category', type=str, default='other',
                       help='Expense category: maintenance, repairs, utilities, insurance, property_tax, hoa, management, other')
    parser.add_argument('--add-income', type=float, help='Add rental income amount')
    parser.add_argument('--tenant', type=str, help='Tenant name for income')

    # Reports
    parser.add_argument('--depreciation', action='store_true', help='Calculate depreciation')
    parser.add_argument('--tax-report', type=int, help='Generate tax report for year (e.g., 2024)')
    parser.add_argument('--operating-income', action='store_true', help='Show operating income summary')
    parser.add_argument('--loans', action='store_true', help='Show loan summary')

    # Export
    parser.add_argument('--export', action='store_true', help='Export to CSV')
    parser.add_argument('--notes', type=str, help='Additional notes for entries')

    args = parser.parse_args()

    # List properties
    if args.list:
        tracker = RentalPropertyTracker("temp")
        properties = tracker.list_properties()
        if properties:
            print(f"\nTracked Properties ({len(properties)}):")
            for prop in properties:
                print(f"  - {prop}")
        else:
            print("\nNo properties tracked yet.")
        print()
        return

    # Create new property
    if args.create:
        tracker = RentalPropertyTracker(args.create)
        print(f"\nCreated new property: {args.create}")
        print(f"Data file: {tracker.property_file}")
        print()
        return

    # All other operations require a property
    if not args.property:
        print("Error: --property is required for most operations. Use --list to see existing properties.")
        return

    tracker = RentalPropertyTracker(args.property)

    # Add land cost
    if args.add_land:
        if not args.amount or not args.date:
            print("Error: --amount and --date required for --add-land")
            return
        result = tracker.add_land_cost(args.add_land, args.amount, args.date, args.notes or "")
        print(f"Added land cost: ${result['amount']:,.2f} on {result['date']}")

    # Add building cost
    if args.add_building:
        if not args.amount or not args.date:
            print("Error: --amount and --date required for --add-building")
            return
        result = tracker.add_building_cost(args.add_building, args.amount, args.date, args.notes or "")
        print(f"Added building cost: ${result['amount']:,.2f} on {result['date']}")

    # Add CIP cost
    if args.add_cip:
        if not args.amount or not args.date:
            print("Error: --amount and --date required for --add-cip")
            return
        result = tracker.add_construction_in_progress(args.add_cip, args.amount, args.date,
                                                     args.cip_type, args.notes or "")
        print(f"Added CIP cost: ${result['amount']:,.2f} on {result['date']}")

    # Add loan
    if args.add_loan:
        if not (args.loan_amount and args.loan_rate and args.loan_term and args.date):
            print("Error: --loan-amount, --loan-rate, --loan-term, and --date required for --add-loan")
            return
        result = tracker.add_loan_record(args.add_loan, args.loan_amount, args.loan_rate,
                                        args.loan_term, args.date, args.loan_type, args.notes or "")
        print(f"Added loan from {result['lender_name']}: ${result['loan_amount']:,.2f}")

    # Set key dates
    if args.set_dates:
        if not (args.purchase_date and args.service_date):
            print("Error: --purchase-date and --service-date required for --set-dates")
            return
        result = tracker.set_key_dates(args.purchase_date, args.service_date,
                                      args.construction_start, args.construction_end,
                                      args.notes or "")
        print(f"Set key dates - Purchased: {result['purchase_date']}, In service: {result['placed_in_service_date']}")

    # Add operating expense
    if args.add_expense:
        if not args.amount or not args.date:
            print("Error: --amount and --date required for --add-expense")
            return
        result = tracker.add_operating_expense(args.add_expense, args.amount, args.date,
                                             args.category, args.notes or "")
        print(f"Added expense: ${result['amount']:,.2f} - {result['description']}")

    # Add rental income
    if args.add_income:
        if not args.date:
            print("Error: --date required for --add-income")
            return
        result = tracker.add_rental_income(args.add_income, args.date, args.tenant or "", args.notes or "")
        print(f"Added rental income: ${result['amount']:,.2f} on {result['date']}")

    # Reports
    if args.depreciation:
        depreciation = tracker.calculate_depreciation()
        if 'error' in depreciation:
            print(f"Error: {depreciation['error']}")
        else:
            print(f"\nDEPRECIATION CALCULATION")
            print(f"{'='*50}")
            print(f"Method: {depreciation['depreciation_method']}")
            print(f"Life: {depreciation['depreciation_life_years']} years")
            print(f"Building basis: ${depreciation['building_basis']:,.2f}")
            print(f"Annual depreciation: ${depreciation['annual_depreciation']:,.2f}")
            print(f"Accumulated: ${depreciation['total_accumulated_depreciation']:,.2f}")
            print(f"Remaining basis: ${depreciation['remaining_depreciable_basis']:,.2f}")
            print()

    if args.tax_report:
        report = tracker.generate_tax_report(args.tax_report)
        print(f"\nTAX REPORT - {args.tax_report}")
        print(f"{'='*50}")
        print(f"Gross rental income: ${report['rental_income']:,.2f}")
        print(f"Operating expenses: ${report['operating_expenses']:,.2f}")
        print(f"Net operating income: ${report['net_operating_income']:,.2f}")
        print(f"Depreciation expense: ${report['depreciation_expense']:,.2f}")
        print(f"Interest paid: ${report['interest_paid']:,.2f}")
        print(f"Property taxes: ${report['property_taxes_paid']:,.2f}")
        print(f"Taxable income: ${report['taxable_income']:,.2f}")
        print()

    if args.operating_income:
        operating = tracker.calculate_operating_income()
        print(f"\nOPERATING INCOME")
        print(f"{'='*50}")
        print(f"Gross rental income: ${operating['gross_rental_income']:,.2f}")
        print(f"Total expenses: ${operating['total_operating_expenses']:,.2f}")
        print(f"Net operating income: ${operating['net_operating_income']:,.2f}")
        if operating['expenses_by_category']:
            print(f"\nExpenses by category:")
            for category, amount in operating['expenses_by_category'].items():
                print(f"  {category}: ${amount:,.2f}")
        print()

    if args.loans:
        loans = tracker.get_loan_summary()
        print(f"\nLOAN SUMMARY")
        print(f"{'='*50}")
        print(f"Total loans: {loans['total_loans']}")
        print(f"Original loan amount: ${loans['total_original_loans']:,.2f}")
        print(f"Current balance: ${loans['total_current_balance']:,.2f}")
        for loan in loans['loans']:
            print(f"\n  {loan['lender_name']} ({loan['loan_type']})")
            print(f"    Original: ${loan['original_amount']:,.2f}")
            print(f"    Rate: {loan['interest_rate']}%")
            print(f"    Balance: ${loan['current_balance']:,.2f}")
        print()

    if args.summary:
        tracker.print_summary()

    if args.export:
        filepath = tracker.export_to_csv()
        print(f"Exported to: {filepath}")


if __name__ == '__main__':
    main()
