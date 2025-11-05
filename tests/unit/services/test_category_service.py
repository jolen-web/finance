"""Unit tests for CategoryService."""

import pytest
from app.services.financial.category_service import CategoryService


class TestCategoryService:
    """Test suite for CategoryService."""

    def test_create_category(self, db_session, test_user):
        """Test creating a category."""
        category = CategoryService.create_category(
            test_user.id,
            'Entertainment',
            'expense'
        )
        
        assert category.user_id == test_user.id
        assert category.name == 'Entertainment'
        assert category.category_type == 'expense'

    def test_get_category(self, db_session, test_category):
        """Test retrieving a category."""
        category = CategoryService.get_category(test_category.id)
        
        assert category.id == test_category.id
        assert category.name == test_category.name

    def test_get_user_categories(self, db_session, test_user, test_category):
        """Test retrieving user categories."""
        categories = CategoryService.get_user_categories(test_user.id)
        
        assert len(categories) >= 1
        assert test_category in categories

    def test_update_category(self, db_session, test_category):
        """Test updating a category."""
        CategoryService.update_category(test_category.id, name='Updated Category')
        
        updated = CategoryService.get_category(test_category.id)
        assert updated.name == 'Updated Category'

    def test_delete_category(self, db_session, test_category):
        """Test deleting a category."""
        category_id = test_category.id
        CategoryService.delete_category(category_id)
        
        deleted = CategoryService.get_category(category_id)
        assert deleted is None

    def test_get_root_categories(self, db_session, test_user, test_category):
        """Test retrieving root categories (no parent)."""
        root_categories = CategoryService.get_root_categories(test_user.id)
        
        assert len(root_categories) >= 1
        assert test_category in root_categories
