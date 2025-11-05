"""
User Management Service

Provides CRUD operations and business logic for user accounts.
"""

from flask_login import current_user
from app import db
from app.models import User, DashboardPreferences


class UserService:
    """Service for managing user accounts and user data."""

    @staticmethod
    def get_user(user_id):
        """Get a user by ID."""
        return User.query.get(user_id)

    @staticmethod
    def get_user_by_username(username):
        """Get a user by username."""
        return User.query.filter_by(username=username).first()

    @staticmethod
    def get_user_by_email(email):
        """Get a user by email."""
        return User.query.filter_by(email=email).first()

    @staticmethod
    def create_user(username, email, password):
        """Create a new user."""
        if UserService.get_user_by_username(username):
            raise ValueError(f"Username '{username}' already exists")

        if UserService.get_user_by_email(email):
            raise ValueError(f"Email '{email}' already exists")

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # Create default dashboard preferences for new user
        preferences = DashboardPreferences(
            user_id=user.id,
            show_account_summary=True,
            show_recent_transactions=True,
            show_investment_summary=True,
            show_asset_summary=True
        )
        db.session.add(preferences)
        db.session.commit()

        return user

    @staticmethod
    def update_user(user_id, **kwargs):
        """Update user profile information."""
        user = UserService.get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Allowed fields to update
        allowed_fields = {'email', 'currency'}

        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(user, field, value)

        db.session.commit()
        return user

    @staticmethod
    def change_password(user_id, old_password, new_password):
        """Change user password with verification."""
        user = UserService.get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        if not user.check_password(old_password):
            raise ValueError("Current password is incorrect")

        user.set_password(new_password)
        db.session.commit()
        return user

    @staticmethod
    def delete_user(user_id):
        """Delete a user account."""
        user = UserService.get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        db.session.delete(user)
        db.session.commit()
