import os
from pathlib import Path

basedir = Path(__file__).parent.absolute()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("No SECRET_KEY set for Flask application")

    # Database configuration
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')

    # Cloud SQL configuration - construct URI from environment variables
    CLOUD_SQL_CONNECTION_NAME = os.environ.get('CLOUD_SQL_CONNECTION_NAME')
    if CLOUD_SQL_CONNECTION_NAME:
        # Running on Cloud Run with Cloud SQL PostgreSQL
        DB_USER = os.environ.get('DB_USER', 'postgres')
        DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
        DB_NAME = os.environ.get('DB_NAME', 'finance')
        SQLALCHEMY_DATABASE_URI = (
            f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@/{DB_NAME}'
            f'?host=/cloudsql/{CLOUD_SQL_CONNECTION_NAME}'
        )
    else:
        # Local development or explicit DATABASE_URL
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
            'sqlite:///' + os.path.join(str(basedir), '..', 'data', 'finance.db')

    # Enable dynamic query tracking
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'pool_size': 10,
        'max_overflow': 20,
    }

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Gemini API configuration (matches receipt_ocr.py which uses GOOGLE_API_KEY)
    GEMINI_API_KEY = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')

    # Session security settings
    SESSION_COOKIE_SECURE = FLASK_ENV == 'production'  # HTTPS only in production
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours in seconds

    # Request size limits (prevent DoS via large uploads)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max request size

    # Application settings
    ITEMS_PER_PAGE = 50
    DATE_FORMAT = '%Y-%m-%d'

    # Version information
    APP_VERSION = '2.0.0'
    APP_VERSION_STAGE = 'beta'  # beta, alpha, rc, stable
    APP_NAME = 'Finance Tracker'
    APP_DESCRIPTION = 'Smart Personal Finance Management'

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
