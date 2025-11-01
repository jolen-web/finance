import pytest
from bs4 import BeautifulSoup
from app.models import User, Account
from app import db as _db

def test_user_registration(client, new_user_payload, db_session):
    """
    GIVEN a Flask application
    WHEN a new user is registered
    THEN check that the user is created in the database
    """
    response = client.post('/auth/register', data=new_user_payload, follow_redirects=True)
    assert response.status_code == 200
    user = db_session.query(User).filter_by(username=new_user_payload['username']).first()
    assert user is not None
    assert user.email == new_user_payload['email']

def test_user_login(client, new_user_payload, db_session):
    """
    GIVEN a registered user
    WHEN the user logs in
    THEN check that the login is successful
    """
    user = User(username=new_user_payload['username'], email=new_user_payload['email'])
    user.set_password(new_user_payload['password'])
    db_session.add(user)
    db_session.commit()

    login_payload = {
        'username': new_user_payload['username'],
        'password': new_user_payload['password']
    }
    response = client.post('/auth/login', data=login_payload, follow_redirects=True)
    assert response.status_code == 200
    assert b'Logout' in response.data

def test_account_creation(client, new_user_payload, db_session):
    """
    GIVEN a logged-in user
    WHEN the user creates a new account
    THEN check that the account is created and associated with the user
    """
    user = User(username=new_user_payload['username'], email=new_user_payload['email'])
    user.set_password(new_user_payload['password'])
    db_session.add(user)
    db_session.commit()

    login_payload = {
        'username': new_user_payload['username'],
        'password': new_user_payload['password']
    }
    client.post('/auth/login', data=login_payload, follow_redirects=True)

    account_payload = {
        'name': 'Test Account',
        'account_type': 'checking',
        'starting_balance': 1000
    }
    response = client.post('/accounts/new', data=account_payload, follow_redirects=True)
    assert response.status_code == 200
    
    account = db_session.query(Account).filter_by(name='Test Account').first()
    assert account is not None
    assert account.user_id == user.id

def test_data_isolation(app, db_session):
    """
    GIVEN a clean database
    WHEN two different users are created and each creates an account
    THEN each user should only see their own account data
    """
    # --- Setup ---
    user_a = User(username='usera', email='usera@example.com')
    user_a.set_password('password_a')
    db_session.add(user_a)

    user_b = User(username='userb', email='userb@example.com')
    user_b.set_password('password_b')
    db_session.add(user_b)
    db_session.commit()

    app.db_manager.initialize_user_data(user_a.id)
    app.db_manager.initialize_user_data(user_b.id)
    db_session.commit()

    # --- User A's Workflow ---
    with app.test_client() as client_a:
        with app.app_context():
            _db.session = db_session
            # Login as User A
            client_a.post('/auth/login', data={'username': 'usera', 'password': 'password_a'}, follow_redirects=True)
            
            # Create an account for User A
            client_a.post('/accounts/new', data={'name': "User A's Account", 'account_type': 'checking', 'starting_balance': 1000}, follow_redirects=True)
            
            # Verify User A's view
            response_a = client_a.get('/accounts/')
            assert response_a.status_code == 200
            soup_a = BeautifulSoup(response_a.data, 'html.parser')
            page_text_a = soup_a.get_text()
            assert "User A's Account" in page_text_a
            assert "User B's Account" not in page_text_a

    # --- User B's Workflow ---
    with app.test_client() as client_b:
        with app.app_context():
            _db.session = db_session
            # Login as User B
            client_b.post('/auth/login', data={'username': 'userb', 'password': 'password_b'}, follow_redirects=True)
            
            # Verify User B's view (before creating their own account)
            response_b_initial = client_b.get('/accounts/')
            assert response_b_initial.status_code == 200
            soup_b_initial = BeautifulSoup(response_b_initial.data, 'html.parser')
            page_text_b_initial = soup_b_initial.get_text()
            assert "User A's Account" not in page_text_b_initial

            # Create an account for User B
            client_b.post('/accounts/new', data={'name': "User B's Account", 'account_type': 'savings', 'starting_balance': 2000}, follow_redirects=True)
            
            # Verify User B's view (after creating their own account)
            response_b_final = client_b.get('/accounts/')
            assert response_b_final.status_code == 200
            soup_b_final = BeautifulSoup(response_b_final.data, 'html.parser')
            page_text_b_final = soup_b_final.get_text()
            assert "User B's Account" in page_text_b_final
            assert "User A's Account" not in page_text_b_final
