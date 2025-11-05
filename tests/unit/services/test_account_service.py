"""Unit tests for AccountService."""

import pytest
from decimal import Decimal
from app.services.financial.account_service import AccountService
from app.models import Account


class TestAccountService:
    """Test suite for AccountService."""

    def test_create_account(self, db_session, test_user):
        """Test creating a new account."""
        account = AccountService.create_account(
            test_user.id,
            'Savings Account',
            'savings',
            Decimal('5000.00')
        )
        
        assert account.user_id == test_user.id
        assert account.name == 'Savings Account'
        assert account.account_type == 'savings'
        assert account.current_balance == Decimal('5000.00')

    def test_get_user_accounts(self, db_session, test_user, test_account):
        """Test retrieving user accounts."""
        accounts = AccountService.get_user_accounts(test_user.id)
        
        assert len(accounts) >= 1
        assert test_account in accounts

    def test_get_account(self, db_session, test_account):
        """Test retrieving a specific account."""
        account = AccountService.get_account(test_account.id)
        
        assert account.id == test_account.id
        assert account.name == test_account.name

    def test_calculate_net_worth(self, db_session, test_user, test_account):
        """Test net worth calculation."""
        # Create additional account
        AccountService.create_account(
            test_user.id,
            'Savings',
            'savings',
            Decimal('3000.00')
        )
        
        net_worth = AccountService.calculate_net_worth(test_user.id)
        assert net_worth == Decimal('4000.00')  # 1000 + 3000

    def test_update_account(self, db_session, test_account):
        """Test updating account details."""
        AccountService.update_account(test_account.id, name='Updated Name')
        
        updated = AccountService.get_account(test_account.id)
        assert updated.name == 'Updated Name'

    def test_delete_account(self, db_session, test_account, test_user):
        """Test deleting an account."""
        account_id = test_account.id
        AccountService.delete_account(account_id)
        
        deleted = AccountService.get_account(account_id)
        assert deleted is None
