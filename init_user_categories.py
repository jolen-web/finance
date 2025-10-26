"""Initialize default categories for all existing users"""
from app import create_app, db
from app.models import Category, User

def init_user_categories():
    """Create default categories for all users who don't have any"""
    app = create_app()

    with app.app_context():
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

        # Get all users
        users = User.query.all()

        if not users:
            print("No users found in database!")
            return

        for user in users:
            # Check if user already has categories
            existing_categories = Category.query.filter_by(user_id=user.id).first()

            if existing_categories:
                print(f"User '{user.username}' already has categories. Skipping.")
                continue

            print(f"Creating default categories for user '{user.username}'...")

            # Add income categories
            for cat_name in income_categories:
                category = Category(
                    name=cat_name,
                    is_income=True,
                    user_id=user.id
                )
                db.session.add(category)

            # Add expense categories and subcategories
            for parent_name, subcats in expense_categories.items():
                parent = Category(
                    name=parent_name,
                    is_income=False,
                    user_id=user.id
                )
                db.session.add(parent)
                db.session.flush()  # Get the parent ID

                for subcat_name in subcats:
                    subcat = Category(
                        name=f"{parent_name} - {subcat_name}",
                        parent_id=parent.id,
                        is_income=False,
                        user_id=user.id
                    )
                    db.session.add(subcat)

            db.session.commit()
            print(f"✅ Categories created for user '{user.username}'")

        print("\n✅ All users have been initialized with default categories!")

if __name__ == '__main__':
    init_user_categories()
