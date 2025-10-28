"""Database manager for single PostgreSQL database with user_id filtering"""
import os
from pathlib import Path


class DatabaseManager:
    """Manages single PostgreSQL database with user_id-based data isolation"""

    def __init__(self):
        """Initialize database manager with PostgreSQL connection details"""
        self.flask_env = os.environ.get('FLASK_ENV', 'development')

    def get_database_uri(self):
        """
        Get the shared database URI (no user_id in URI).

        Returns:
            Database connection URI
        """
        if self.flask_env == 'production':
            # Cloud SQL production settings
            db_user = os.environ.get('DB_USER', 'postgres')
            db_pass = os.environ.get('DB_PASSWORD', '')
            cloud_sql_connection_name = os.environ.get(
                'CLOUD_SQL_CONNECTION_NAME',
                'jinolen:us-central1:finance-db'
            )
            db_name = os.environ.get('DB_NAME', 'finance')

            return (
                f'postgresql+psycopg2://{db_user}:{db_pass}@/'
                f'{db_name}?host=/cloudsql/{cloud_sql_connection_name}'
            )
        else:
            # Local development - use PostgreSQL
            db_user = os.environ.get('DB_USER', 'postgres')
            db_pass = os.environ.get('DB_PASSWORD', 'postgres')
            db_host = os.environ.get('DB_HOST', 'localhost')
            db_port = os.environ.get('DB_PORT', '5432')
            db_name = os.environ.get('DB_NAME', 'finance_app')

            return (
                f'postgresql+psycopg2://{db_user}:{db_pass}@'
                f'{db_host}:{db_port}/{db_name}'
            )

    def create_user_database(self, user_id):
        """
        Initialize default categories for a user in the shared database.

        Args:
            user_id: The user ID

        Returns:
            True if successful, False otherwise
        """
        try:
            # Initialize default categories for the user
            self._initialize_default_categories(user_id)
            return True
        except Exception as e:
            print(f'Error initializing user data: {e}')
            import traceback
            traceback.print_exc()
            return False

    def delete_user_database(self, user_id):
        """
        Delete all user data from the shared database (for account deletion).

        Args:
            user_id: The user ID

        Returns:
            True if successful, False otherwise
        """
        try:
            from app import db
            from app.models import User

            # Delete the user and all associated data (cascading deletes)
            user = User.query.get(user_id)
            if user:
                db.session.delete(user)
                db.session.commit()

            return True
        except Exception as e:
            print(f'Error deleting user data: {e}')
            return False

    def database_exists(self, user_id):
        """
        Check if a user has been initialized in the shared database.

        Args:
            user_id: The user ID

        Returns:
            True if user exists, False otherwise
        """
        try:
            from app.models import User
            user = User.query.get(user_id)
            return user is not None
        except Exception as e:
            print(f'Error checking user: {e}')
            return False

    def _initialize_default_categories(self, user_id):
        """
        Initialize default categories for a new user in the shared database.

        Args:
            user_id: The user ID

        Returns:
            True if successful, False otherwise
        """
        try:
            from app.models import Category
            from app import db

            # Default categories: expense categories and income categories
            default_categories = [
                # Expense categories
                ('Groceries', False),
                ('Utilities', False),
                ('Transport', False),
                ('Entertainment', False),
                ('Healthcare', False),
                ('Dining Out', False),
                ('Shopping', False),
                ('Subscriptions', False),
                ('Insurance', False),
                ('Other Expenses', False),
                # Income categories
                ('Salary', True),
                ('Bonus', True),
                ('Interest', True),
                ('Dividends', True),
                ('Other Income', True),
            ]

            for category_name, is_income in default_categories:
                # Check if category already exists for this user
                existing = Category.query.filter_by(
                    user_id=user_id,
                    name=category_name,
                    is_income=is_income
                ).first()

                if not existing:
                    category = Category(
                        user_id=user_id,
                        name=category_name,
                        is_income=is_income
                    )
                    db.session.add(category)

            db.session.commit()
            return True
        except Exception as e:
            print(f'Error initializing default categories: {e}')
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False


# Global database manager instance
db_manager = DatabaseManager()
