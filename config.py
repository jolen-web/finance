import os
from pathlib import Path
from app.db_manager import db_manager

basedir = Path(__file__).parent.absolute()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Database configuration
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')

    if FLASK_ENV == 'development':
        # For development, use a default SQLite database for operations
        # outside of a request context (e.g., flask db migrate).
        # The per-user database will be switched in app/__init__.py for requests.
        db_path = basedir / 'data' / 'finance.db'
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    else:
        # In production, the URI is set dynamically per-request.
        # We set a dummy value here to avoid import-time errors.
        # CLI commands that need the DB in production will require a different setup.
        SQLALCHEMY_DATABASE_URI = 'postgresql://dummy:dummy@dummy/dummy'

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
