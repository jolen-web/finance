"""Database manager for per-user database isolation"""
import os
from pathlib import Path

try:
    import psycopg2
    from psycopg2 import sql
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False


class DatabaseManager:
    """Manages per-user database creation and management"""

    def __init__(self):
        """Initialize database manager with PostgreSQL connection details"""
        self.flask_env = os.environ.get('FLASK_ENV', 'development')

        if self.flask_env == 'production':
            # Cloud SQL production settings
            self.db_user = os.environ.get('DB_USER', 'postgres')
            self.db_pass = os.environ.get('DB_PASSWORD', '')
            self.db_host = None  # Using Unix socket
            self.db_port = None
            self.cloud_sql_connection_name = os.environ.get(
                'CLOUD_SQL_CONNECTION_NAME',
                'jinolen:us-central1:finance-db'
            )
            self.use_unix_socket = True
        else:
            # Local development - use SQLite per user
            self.use_sqlite = True
            self.db_dir = Path(__file__).parent.parent / 'data'
            self.db_dir.mkdir(exist_ok=True)

    def get_database_uri(self, user_id):
        """
        Get the database URI for a specific user.

        Args:
            user_id: The user ID

        Returns:
            Database connection URI
        """
        if self.flask_env == 'production':
            # PostgreSQL per-user database on Cloud SQL
            db_name = f'finance_user_{user_id}'
            return (
                f'postgresql+psycopg2://{self.db_user}:{self.db_pass}@/'
                f'{db_name}?host=/cloudsql/{self.cloud_sql_connection_name}'
            )
        else:
            # SQLite per-user database
            db_path = self.db_dir / f'finance_user_{user_id}.db'
            return f'sqlite:///{db_path}'

    def create_user_database(self, user_id):
        """
        Create a new database for a user and initialize schema.

        Args:
            user_id: The user ID

        Returns:
            True if successful, False otherwise
        """
        if self.flask_env == 'development':
            # SQLite: Create database file and initialize schema
            from app import db
            from sqlalchemy import create_engine
            from sqlalchemy.pool import StaticPool

            try:
                db_uri = self.get_database_uri(user_id)

                # Create engine for user's database
                engine_options = {
                    'poolclass': StaticPool,
                    'echo': False
                }
                engine = create_engine(db_uri, **engine_options)

                # Create all tables in the user's database
                with engine.begin() as connection:
                    db.metadata.create_all(bind=connection)

                engine.dispose()

                # Initialize default categories for the user
                self._initialize_default_categories(user_id)

                return True
            except Exception as e:
                print(f'Error creating user database schema: {e}')
                import traceback
                traceback.print_exc()
                return False

        # PostgreSQL: create database
        if not HAS_PSYCOPG2:
            print('psycopg2 not installed. Skipping database creation.')
            return True

        try:
            # Connect to default postgres database
            conn = psycopg2.connect(
                user=self.db_user,
                password=self.db_pass,
                host=f'/cloudsql/{self.cloud_sql_connection_name}',
                database='postgres'
            )
            conn.autocommit = True
            cursor = conn.cursor()

            db_name = f'finance_user_{user_id}'

            # Create database
            cursor.execute(
                sql.SQL('CREATE DATABASE {} OWNER {}'.format(
                    sql.Identifier(db_name),
                    sql.Identifier(self.db_user)
                ))
            )

            cursor.close()
            conn.close()

            return True
        except psycopg2.Error as e:
            if 'already exists' in str(e):
                return True  # Database already exists
            print(f'Error creating database: {e}')
            return False

    def delete_user_database(self, user_id):
        """
        Delete a user's database (for account deletion).

        Args:
            user_id: The user ID

        Returns:
            True if successful, False otherwise
        """
        if self.flask_env == 'development':
            # SQLite: delete the file
            db_path = self.db_dir / f'finance_user_{user_id}.db'
            if db_path.exists():
                db_path.unlink()
            return True

        # PostgreSQL: drop database
        if not HAS_PSYCOPG2:
            print('psycopg2 not installed. Skipping database deletion.')
            return True

        try:
            conn = psycopg2.connect(
                user=self.db_user,
                password=self.db_pass,
                host=f'/cloudsql/{self.cloud_sql_connection_name}',
                database='postgres'
            )
            conn.autocommit = True
            cursor = conn.cursor()

            db_name = f'finance_user_{user_id}'

            # Terminate connections to the database
            cursor.execute(
                sql.SQL(
                    'SELECT pg_terminate_backend(pg_stat_activity.pid) '
                    'FROM pg_stat_activity '
                    'WHERE pg_stat_activity.datname = %s'
                ),
                (db_name,)
            )

            # Drop database
            cursor.execute(
                sql.SQL('DROP DATABASE IF EXISTS {}').format(
                    sql.Identifier(db_name)
                )
            )

            cursor.close()
            conn.close()

            return True
        except psycopg2.Error as e:
            print(f'Error deleting database: {e}')
            return False

    def database_exists(self, user_id):
        """
        Check if a user's database exists.

        Args:
            user_id: The user ID

        Returns:
            True if database exists, False otherwise
        """
        if self.flask_env == 'development':
            db_path = self.db_dir / f'finance_user_{user_id}.db'
            return db_path.exists()

        # PostgreSQL
        if not HAS_PSYCOPG2:
            return True  # Assume database exists if we can't check

        try:
            conn = psycopg2.connect(
                user=self.db_user,
                password=self.db_pass,
                host=f'/cloudsql/{self.cloud_sql_connection_name}',
                database='postgres'
            )
            cursor = conn.cursor()

            db_name = f'finance_user_{user_id}'

            cursor.execute(
                'SELECT 1 FROM pg_database WHERE datname = %s',
                (db_name,)
            )

            exists = cursor.fetchone() is not None

            cursor.close()
            conn.close()

            return exists
        except psycopg2.Error as e:
            print(f'Error checking database: {e}')
            return False

    def _initialize_default_categories(self, user_id):
        """
        Initialize default categories for a new user.

        Args:
            user_id: The user ID

        Returns:
            True if successful, False otherwise
        """
        try:
            from app.models import Category
            from app import db
            from sqlalchemy import create_engine
            from sqlalchemy.pool import StaticPool

            db_uri = self.get_database_uri(user_id)

            # Create a temporary engine for this user's database
            engine_options = {
                'poolclass': StaticPool,
                'echo': False
            }
            engine = create_engine(db_uri, **engine_options)

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

            with engine.begin() as connection:
                # Create a temporary session bound to this connection
                from sqlalchemy.orm import sessionmaker, Session
                temp_session = Session(bind=connection)

                for category_name, is_income in default_categories:
                    # Check if category already exists
                    existing = temp_session.query(Category).filter_by(
                        name=category_name, is_income=is_income
                    ).first()

                    if not existing:
                        category = Category(name=category_name, is_income=is_income)
                        temp_session.add(category)

                temp_session.commit()
                temp_session.close()

            engine.dispose()
            return True
        except Exception as e:
            print(f'Error initializing default categories: {e}')
            import traceback
            traceback.print_exc()
            return False


# Global database manager instance
db_manager = DatabaseManager()
