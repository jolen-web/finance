"""
Authentication Service

Provides authentication-related business logic including login, logout, and permission checks.
"""

from flask_login import current_user, login_user, logout_user
from app.models import User
from app.services.auth.user_service import UserService


class AuthService:
    """Service for authentication operations."""

    @staticmethod
    def authenticate(username, password):
        """
        Authenticate a user with username and password.

        Args:
            username: User's username
            password: User's plain text password

        Returns:
            User object if authentication successful, None otherwise
        """
        user = UserService.get_user_by_username(username)

        if user and user.check_password(password):
            return user

        return None

    @staticmethod
    def login(user, remember_me=False):
        """
        Log in a user.

        Args:
            user: User object to log in
            remember_me: Boolean to remember login session

        Returns:
            True if login successful
        """
        login_user(user, remember=remember_me)
        return True

    @staticmethod
    def logout():
        """
        Log out the current user.

        Returns:
            True if logout successful
        """
        logout_user()
        return True

    @staticmethod
    def is_authenticated():
        """Check if current user is authenticated."""
        return current_user.is_authenticated

    @staticmethod
    def get_current_user():
        """Get the currently authenticated user."""
        if current_user.is_authenticated:
            return current_user
        return None
