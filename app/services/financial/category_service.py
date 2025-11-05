"""
Category Management Service

Provides CRUD operations for transaction categories with hierarchical support.
"""

from app import db
from app.models import Category


class CategoryService:
    """Service for managing transaction categories."""

    @staticmethod
    def create_category(user_id, name, category_type='expense', parent_id=None):
        """Create a new category."""
        category = Category(
            user_id=user_id,
            name=name,
            type=category_type,
            parent_id=parent_id
        )
        db.session.add(category)
        db.session.commit()
        return category

    @staticmethod
    def get_category(category_id):
        """Get a category by ID."""
        return Category.query.get(category_id)

    @staticmethod
    def get_user_categories(user_id, category_type=None):
        """Get all categories for a user."""
        query = Category.query.filter_by(user_id=user_id)
        if category_type:
            query = query.filter_by(type=category_type)
        return query.all()

    @staticmethod
    def get_root_categories(user_id, category_type=None):
        """Get top-level categories (no parent)."""
        query = Category.query.filter_by(user_id=user_id, parent_id=None)
        if category_type:
            query = query.filter_by(type=category_type)
        return query.all()

    @staticmethod
    def get_subcategories(parent_id):
        """Get all subcategories of a parent category."""
        return Category.query.filter_by(parent_id=parent_id).all()

    @staticmethod
    def update_category(category_id, **kwargs):
        """Update category information."""
        category = CategoryService.get_category(category_id)
        if not category:
            raise ValueError(f"Category {category_id} not found")

        allowed_fields = {'name', 'type', 'parent_id'}
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(category, field, value)

        db.session.commit()
        return category

    @staticmethod
    def delete_category(category_id):
        """Delete a category and reassign its subcategories."""
        category = CategoryService.get_category(category_id)
        if not category:
            raise ValueError(f"Category {category_id} not found")

        # Reassign subcategories to parent
        subcategories = CategoryService.get_subcategories(category_id)
        for subcat in subcategories:
            subcat.parent_id = category.parent_id

        db.session.delete(category)
        db.session.commit()

    @staticmethod
    def get_category_hierarchy(user_id, category_type=None):
        """Get category hierarchy as a tree structure."""
        root_categories = CategoryService.get_root_categories(user_id, category_type)

        def build_tree(category):
            return {
                'id': category.id,
                'name': category.name,
                'type': category.type,
                'children': [build_tree(child) for child in CategoryService.get_subcategories(category.id)]
            }

        return [build_tree(cat) for cat in root_categories]
