import os
from pathlib import Path

basedir = Path(__file__).parent.absolute()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Database configuration
    if os.environ.get('FLASK_ENV') == 'production':
        # Cloud Run with Cloud SQL PostgreSQL
        # Connection via Unix socket: /cloudsql/PROJECT:REGION:INSTANCE
        db_user = os.environ.get('DB_USER', 'postgres')
        db_pass = os.environ.get('DB_PASSWORD', '')
        db_name = os.environ.get('DB_NAME', 'finance')
        cloud_sql_connection_name = os.environ.get('CLOUD_SQL_CONNECTION_NAME', 'jinolen:us-central1:finance-db')

        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
            f'postgresql+psycopg2://{db_user}:{db_pass}@/{db_name}?host=/cloudsql/{cloud_sql_connection_name}'
    else:
        # Local development: use SQLite in data directory
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
            f'sqlite:///{basedir / "data" / "finance.db"}'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Gemini API configuration
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

    # Application settings
    ITEMS_PER_PAGE = 50
    DATE_FORMAT = '%Y-%m-%d'

    # Currency settings
    CURRENCIES = {
        'USD': {'symbol': '$', 'name': 'US Dollar', 'position': 'before'},
        'PHP': {'symbol': '₱', 'name': 'Philippine Peso', 'position': 'before'},
        'EUR': {'symbol': '€', 'name': 'Euro', 'position': 'before'},
        'GBP': {'symbol': '£', 'name': 'British Pound', 'position': 'before'},
        'JPY': {'symbol': '¥', 'name': 'Japanese Yen', 'position': 'before'},
        'CNY': {'symbol': '¥', 'name': 'Chinese Yuan', 'position': 'before'},
        'INR': {'symbol': '₹', 'name': 'Indian Rupee', 'position': 'before'},
        'KRW': {'symbol': '₩', 'name': 'Korean Won', 'position': 'before'},
        'AUD': {'symbol': '$', 'name': 'Australian Dollar', 'position': 'before'},
        'CAD': {'symbol': '$', 'name': 'Canadian Dollar', 'position': 'before'},
        'CHF': {'symbol': 'Fr', 'name': 'Swiss Franc', 'position': 'before'},
        'SGD': {'symbol': '$', 'name': 'Singapore Dollar', 'position': 'before'},
        'MXN': {'symbol': '$', 'name': 'Mexican Peso', 'position': 'before'},
        'BRL': {'symbol': 'R$', 'name': 'Brazilian Real', 'position': 'before'},
    }
    DEFAULT_CURRENCY = os.environ.get('DEFAULT_CURRENCY') or 'PHP'
