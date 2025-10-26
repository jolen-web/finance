import os
from pathlib import Path

basedir = Path(__file__).parent.absolute()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{basedir / "data" / "finance.db"}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

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
