"""Pytest configuration and shared fixtures."""

import os
import pytest
from decimal import Decimal
from app import create_app, db
from app.models import User, Account, Transaction, Category


@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client for making requests."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """CLI runner for testing CLI commands."""
    return app.test_cli_runner()


@pytest.fixture
def app_context(app):
    """Application context for database operations."""
    with app.app_context():
        yield app


@pytest.fixture
def db_session(app_context):
    """Database session for tests."""
    yield db.session
    db.session.rollback()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        username='testuser',
        email='test@example.com',
        password_hash='hashed_password'
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_account(db_session, test_user):
    """Create a test account."""
    account = Account(
        user_id=test_user.id,
        name='Test Checking',
        account_type='checking',
        current_balance=Decimal('1000.00')
    )
    db_session.add(account)
    db_session.commit()
    return account


@pytest.fixture
def test_category(db_session, test_user):
    """Create a test category."""
    category = Category(
        user_id=test_user.id,
        name='Groceries',
        category_type='expense'
    )
    db_session.add(category)
    db_session.commit()
    return category


@pytest.fixture
def test_transaction(db_session, test_account, test_category):
    """Create a test transaction."""
    transaction = Transaction(
        account_id=test_account.id,
        amount=Decimal('25.50'),
        description='Grocery store',
        category_id=test_category.id,
        transaction_type='expense'
    )
    db_session.add(transaction)
    db_session.commit()
    return transaction
