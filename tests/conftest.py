import pytest
from app import create_app, db as _db
from app.models import User
from config import Config
from sqlalchemy.orm import sessionmaker, scoped_session

@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for the entire test session."""
    app = create_app(TestConfig)
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()

class TestConfig(Config):
    """Test configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_ENGINE_OPTIONS = {}

@pytest.fixture(scope='function')
def db_session(app):
    """
    Creates a new database session for a test, wrapped in a transaction that is
    rolled back at the end.
    """
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()
        
        session_factory = sessionmaker(bind=connection)
        session = scoped_session(session_factory)
        
        _db.session = session

        yield session

        session.remove()
        transaction.rollback()
        connection.close()

@pytest.fixture()
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def new_user_payload():
    """Fixture for creating a new user payload."""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password',
        'password_confirm': 'password'
    }
