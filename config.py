import os
from pathlib import Path

basedir = Path(__file__).parent.absolute()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Per-user database configuration (dynamic routing)
    # Database URI will be set per-request based on current_user
    # Initialize with a default SQLite database for anonymous users
    _base_db_path = os.path.join(os.path.dirname(__file__), 'data', 'finance_default.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{_base_db_path}'

    # Database configuration for dynamic routing
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')

    if FLASK_ENV == 'production':
        # Cloud Run with Cloud SQL PostgreSQL
        # Connection via Unix socket: /cloudsql/PROJECT:REGION:INSTANCE
        DB_USER = os.environ.get('DB_USER', 'postgres')
        DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
        CLOUD_SQL_CONNECTION_NAME = os.environ.get('CLOUD_SQL_CONNECTION_NAME', 'jinolen:us-central1:finance-db')

    # Enable dynamic query tracking
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'pool_size': 10,
        'max_overflow': 20,
    }

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
