# Rental Property Tracker

A comprehensive command-line tool for tracking rental property finances including cost basis, depreciation, financing, and tax reporting.

## Features

- **Cost Basis Tracking**: Track land, building, and construction-in-progress (CIP) costs
- **Depreciation Calculation**: Automatic straight-line depreciation calculation (27.5-year residential)
- **Financing Management**: Track loans, payments, and interest paid
- **Key Dates**: Set critical dates for tax and depreciation purposes
- **Operating Income/Expenses**: Track rental income and categorized operating expenses
- **Tax Reports**: Generate comprehensive tax reports by year
- **Data Export**: Export property data to CSV for analysis

## Installation

```bash
cd scripts
python3 rental_property_tracker.py --help
```

No external dependencies required beyond Python standard library.

## Quick Start

### Create a new property
```bash
python3 rental_property_tracker.py --create "Beach House"
```

### Add cost basis items
```bash
# Add land cost
python3 rental_property_tracker.py --property "Beach House" \
  --add-land "Land acquisition" \
  --amount 250000 \
  --date "2020-01-15"

# Add building cost
python3 rental_property_tracker.py --property "Beach House" \
  --add-building "Building cost" \
  --amount 400000 \
  --date "2020-02-01"
```

### Set key dates
```bash
python3 rental_property_tracker.py --property "Beach House" \
  --set-dates \
  --purchase-date "2020-01-15" \
  --service-date "2020-06-01"
```

### Track operating expenses
```bash
python3 rental_property_tracker.py --property "Beach House" \
  --add-expense "Insurance" \
  --amount 1200 \
  --date "2024-01-01" \
  --category "insurance"
```

### Record rental income
```bash
python3 rental_property_tracker.py --property "Beach House" \
  --add-income 5000 \
  --date "2024-01-01" \
  --tenant "John Smith"
```

### View depreciation
```bash
python3 rental_property_tracker.py --property "Beach House" --depreciation
```

### Generate tax report
```bash
python3 rental_property_tracker.py --property "Beach House" --tax-report 2024
```

### View summary
```bash
python3 rental_property_tracker.py --property "Beach House" --summary
```

### Export to CSV
```bash
python3 rental_property_tracker.py --property "Beach House" --export
```

### List all properties
```bash
python3 rental_property_tracker.py --list
```

## Data Structure

### Cost Basis Categories
- **Land**: Land acquisition costs
- **Building**: Building acquisition and improvement costs
- **CIP (Construction in Progress)**: Construction-related costs during active construction
  - labor: Labor costs
  - materials: Construction materials
  - permits: Permits and fees
  - other: Other construction expenses

### Operating Expense Categories
- **maintenance**: General maintenance
- **repairs**: Repairs and fixes
- **utilities**: Utilities (water, electric, gas)
- **insurance**: Property insurance
- **property_tax**: Property tax payments
- **hoa**: HOA fees
- **management**: Property management fees
- **other**: Miscellaneous

### Financing
- **mortgage**: Primary mortgage
- **construction**: Construction loan
- **personal**: Personal/line of credit loan
- **other**: Other loan types

## Tax Features

### Depreciation
The tracker uses standard residential property depreciation:
- **Life**: 27.5 years (residential properties)
- **Method**: Straight-line depreciation
- **Basis**: Building cost basis (land is not depreciated)
- **Date**: Depreciation starts from "placed in service" date

### Tax Report (Annual)
Generates comprehensive tax report including:
- Gross rental income
- Operating expenses (by category)
- Net operating income
- Depreciation expense
- Interest paid (from loan payments)
- Property taxes paid
- Taxable income

## Data Files

Properties are stored as JSON in the `data/rental_properties/` directory:
- File naming: `{property_name}.json`
- Format: Complete property data with all costs, expenses, loans, and dates
- CSV exports: `{property_name}_export_{timestamp}.csv`

## Example Workflow

```bash
# Create property
python3 rental_property_tracker.py --create "Investment Property A"

# Add acquisition costs
python3 rental_property_tracker.py --property "Investment Property A" \
  --add-land "Land" --amount 150000 --date "2023-01-01"

python3 rental_property_tracker.py --property "Investment Property A" \
  --add-building "Building" --amount 350000 --date "2023-01-15"

# Set key dates
python3 rental_property_tracker.py --property "Investment Property A" \
  --set-dates --purchase-date "2023-01-01" --service-date "2023-06-01"

# Add financing
python3 rental_property_tracker.py --property "Investment Property A" \
  --add-loan "First Bank" \
  --loan-amount 400000 \
  --loan-rate 6.5 \
  --loan-term 30 \
  --date "2023-01-15"

# Track annual expenses (repeat for each month/expense)
python3 rental_property_tracker.py --property "Investment Property A" \
  --add-expense "Property Tax" --amount 3600 --date "2024-01-01" --category "property_tax"

python3 rental_property_tracker.py --property "Investment Property A" \
  --add-expense "Insurance" --amount 1200 --date "2024-01-01" --category "insurance"

# Record income (repeat for each month)
python3 rental_property_tracker.py --property "Investment Property A" \
  --add-income 6000 --date "2024-01-01" --tenant "Tenant Name"

# Review depreciation
python3 rental_property_tracker.py --property "Investment Property A" --depreciation

# Generate tax report
python3 rental_property_tracker.py --property "Investment Property A" --tax-report 2024

# Export for analysis
python3 rental_property_tracker.py --property "Investment Property A" --export
```

## Output Examples

### Summary Report
```
============================================================
RENTAL PROPERTY SUMMARY: Beach House
============================================================

COST BASIS:
  Land: $250,000.00
  Building: $400,000.00
  CIP: $0.00
  Total: $650,000.00

DEPRECIATION (27.5-year):
  Annual: $14,545.45
  Accumulated: $66,666.67
  Remaining basis: $333,333.33

OPERATING INCOME:
  Gross rental income: $5,000.00
  Total expenses: $4,800.00
  Net operating income: $200.00

FINANCING:
  Total loans: 1
  Original loan amount: $400,000.00
  Current balance: $395,000.00
```

### Tax Report
```
TAX REPORT - 2024
==================================================
Gross rental income: $60,000.00
Operating expenses: $4,800.00
Net operating income: $55,200.00
Depreciation expense: $14,545.45
Interest paid: $25,000.00
Property taxes: $3,600.00
Taxable income: $14,654.55
```

## Notes

- All amounts are in USD
- Dates must be in YYYY-MM-DD format
- The tracker stores data locally in JSON files
- For multi-property tracking, run separate commands for each property
- Depreciation calculations use standard residential property rules
- Tax reports are informational; consult a tax professional for actual tax filing

## Limitations

- Single-property tracking per instance
- No built-in amortization schedule (partial integration for loan tracking)
- No bonus depreciation or cost recovery methods (standard MACRS only)
- No like-kind exchange tracking
- No 1031 exchange tracking

## Future Enhancements

- Multiple properties in single database
- Loan amortization schedule generation
- Monthly/quarterly reports
- Web interface
- Multiple depreciation methods (MACRS, declining balance, etc.)
- Integration with main Finance Tracker application
