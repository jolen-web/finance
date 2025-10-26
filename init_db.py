"""Initialize the database with default categories"""
from app import create_app, db
from app.models import Category

def init_database():
    app = create_app()

    with app.app_context():
        # Create all tables
        db.create_all()

        # Check if categories already exist
        if Category.query.first() is not None:
            print("Database already initialized with categories.")
            return

        # Default income categories
        income_categories = [
            'Salary',
            'Freelance Income',
            'Investment Income',
            'Other Income'
        ]

        # Default expense categories with subcategories
        expense_categories = {
            'Housing': ['Rent/Mortgage', 'Property Tax', 'Home Insurance', 'Utilities', 'Maintenance'],
            'Transportation': ['Car Payment', 'Gas', 'Insurance', 'Maintenance', 'Public Transit'],
            'Food': ['Groceries', 'Restaurants', 'Coffee Shops'],
            'Healthcare': ['Insurance', 'Doctor Visits', 'Prescriptions', 'Dental'],
            'Personal': ['Clothing', 'Haircare', 'Personal Care'],
            'Entertainment': ['Movies', 'Streaming Services', 'Hobbies', 'Events'],
            'Bills & Utilities': ['Phone', 'Internet', 'Electricity', 'Water', 'Gas'],
            'Shopping': ['General Shopping', 'Electronics', 'Home Goods'],
            'Education': ['Tuition', 'Books', 'Courses'],
            'Savings & Investments': ['Emergency Fund', 'Retirement', 'Investments'],
            'Debt Payments': ['Credit Card', 'Student Loans', 'Personal Loans'],
            'Other Expenses': []
        }

        # Add income categories
        for cat_name in income_categories:
            category = Category(name=cat_name, is_income=True)
            db.session.add(category)

        # Add expense categories and subcategories
        for parent_name, subcats in expense_categories.items():
            parent = Category(name=parent_name, is_income=False)
            db.session.add(parent)
            db.session.flush()  # Get the parent ID

            for subcat_name in subcats:
                subcat = Category(name=f"{parent_name} - {subcat_name}",
                                parent_id=parent.id,
                                is_income=False)
                db.session.add(subcat)

        db.session.commit()
        print("Database initialized successfully with default categories!")

if __name__ == '__main__':
    init_database()
