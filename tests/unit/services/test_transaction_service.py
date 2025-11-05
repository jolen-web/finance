"""Unit tests for TransactionService."""

import pytest
from decimal import Decimal
from app.services.financial.transaction_service import TransactionService
from app.models import Transaction


class TestTransactionService:
    """Test suite for TransactionService."""

    def test_create_transaction(self, db_session, test_account, test_category):
        """Test creating a transaction."""
        transaction = TransactionService.create_transaction(
            test_account.id,
            Decimal('50.00'),
            'Gas station',
            test_category.id,
            'expense'
        )
        
        assert transaction.account_id == test_account.id
        assert transaction.amount == Decimal('50.00')
        assert transaction.description == 'Gas station'
        assert transaction.transaction_type == 'expense'

    def test_get_transaction(self, db_session, test_transaction):
        """Test retrieving a transaction."""
        transaction = TransactionService.get_transaction(test_transaction.id)
        
        assert transaction.id == test_transaction.id
        assert transaction.description == test_transaction.description

    def test_get_account_transactions(self, db_session, test_account, test_transaction):
        """Test retrieving account transactions."""
        transactions = TransactionService.get_account_transactions(test_account.id)
        
        assert len(transactions) >= 1
        assert test_transaction in transactions

    def test_toggle_cleared(self, db_session, test_transaction):
        """Test toggling transaction cleared status."""
        initial_status = test_transaction.is_cleared
        TransactionService.toggle_cleared(test_transaction.id)
        
        updated = TransactionService.get_transaction(test_transaction.id)
        assert updated.is_cleared != initial_status

    def test_delete_transaction(self, db_session, test_transaction):
        """Test deleting a transaction."""
        transaction_id = test_transaction.id
        TransactionService.delete_transaction(transaction_id)
        
        deleted = TransactionService.get_transaction(transaction_id)
        assert deleted is None

    def test_categorize_transaction(self, db_session, test_transaction, test_category):
        """Test categorizing a transaction."""
        # Create another category
        new_category = CategoryService.create_category(
            test_transaction.account.user_id,
            'Utilities',
            'expense'
        )
        
        TransactionService.categorize_transaction(
            test_transaction.id,
            new_category.id
        )
        
        updated = TransactionService.get_transaction(test_transaction.id)
        assert updated.category_id == new_category.id
