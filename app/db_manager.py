from pathlib import Path
from app.models import Category, Account

class DBManager:
    def __init__(self, db):
        self.db = db

    def get_database_uri(self):
        # This is now only used for the default production config
        db_path = Path(__file__).parent.parent / 'data' / 'finance.db'
        db_path.parent.mkdir(exist_ok=True)
        return f'sqlite:///{db_path.absolute()}'

    def initialize_user_data(self, user_id):
        """Initializes default categories and accounts for a new user."""
        import logging
        logger = logging.getLogger(__name__)
        try:
            self._initialize_default_categories(user_id)
            self._initialize_default_accounts(user_id)
            self.db.session.commit()
            return True
        except Exception as e:
            self.db.session.rollback()
            logger.error(f"Error initializing user data for user {user_id}: {e}", exc_info=True)
            return False

    def _initialize_default_categories(self, user_id):
        """Creates a set of default categories for a new user."""
        default_categories = {
            "Income": ["Salary", "Bonus", "Interest Income"],
            "Expense": {
                "Housing": ["Rent/Mortgage", "Property Tax", "Utilities"],
                "Transportation": ["Gas/Fuel", "Public Transit", "Car Maintenance"],
                "Food": ["Groceries", "Restaurants"],
                "Personal Care": ["Haircut", "Toiletries"],
                "Entertainment": ["Movies", "Concerts", "Games"],
                "Debt": ["Credit Card Payment", "Loan Payment"]
            }
        }

        # Income categories
        income_parent = self._get_or_create_category(user_id, "Income", is_income=True)
        for cat_name in default_categories["Income"]:
            self._get_or_create_category(user_id, cat_name, parent=income_parent, is_income=True)

        # Expense categories
        expense_parent = self._get_or_create_category(user_id, "Expense")
        for parent_name, sub_cats in default_categories["Expense"].items():
            parent_cat = self._get_or_create_category(user_id, parent_name, parent=expense_parent)
            for sub_cat_name in sub_cats:
                self._get_or_create_category(user_id, sub_cat_name, parent=parent_cat)

    def _initialize_default_accounts(self, user_id):
        """Creates default 'Cash' and 'Credit Card' accounts for a new user."""
        if not Account.query.filter_by(user_id=user_id, name="Cash").first():
            cash_account = Account(user_id=user_id, name="Cash", account_type="cash", starting_balance=0)
            self.db.session.add(cash_account)

        if not Account.query.filter_by(user_id=user_id, name="Credit Card").first():
            cc_account = Account(user_id=user_id, name="Credit Card", account_type="credit_card", starting_balance=0)
            self.db.session.add(cc_account)

    def _get_or_create_category(self, user_id, name, parent=None, is_income=False):
        """Finds an existing category or creates a new one."""
        category = Category.query.filter_by(
            user_id=user_id,
            name=name,
            parent_id=parent.id if parent else None
        ).first()
        if not category:
            category = Category(
                user_id=user_id,
                name=name,
                parent=parent,
                is_income=is_income
            )
            self.db.session.add(category)
            self.db.session.flush()  # Flush to get the ID for potential children
        return category
