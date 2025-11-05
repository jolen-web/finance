"""User model with authentication and API key encryption"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
from app import db
import os
import base64
import hashlib


class User(UserMixin, db.Model):
    """User account with password and encrypted API key management"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    gemini_api_key = db.Column(db.String(500), nullable=True)  # User's personal Gemini API key (encrypted)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def _get_encryption_key():
        """Get or derive encryption key from SECRET_KEY"""
        secret_key = os.environ.get('SECRET_KEY', '')
        if not secret_key:
            raise ValueError("SECRET_KEY not configured for API key encryption")
        # Derive a key from SECRET_KEY using SHA256
        key_material = hashlib.sha256(secret_key.encode()).digest()
        # Fernet requires base64-encoded 32-byte key
        return base64.urlsafe_b64encode(key_material)

    def set_gemini_api_key(self, api_key):
        """Encrypt and store Gemini API key"""
        if not api_key:
            self.gemini_api_key = None
            return
        try:
            key = self._get_encryption_key()
            cipher = Fernet(key)
            encrypted = cipher.encrypt(api_key.encode())
            # Store as string for database
            self.gemini_api_key = encrypted.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Failed to encrypt API key: {str(e)}")

    def get_gemini_api_key(self):
        """Decrypt and retrieve Gemini API key"""
        if not self.gemini_api_key:
            return None
        try:
            key = self._get_encryption_key()
            cipher = Fernet(key)
            decrypted = cipher.decrypt(self.gemini_api_key.encode())
            return decrypted.decode('utf-8')
        except Exception as e:
            # If decryption fails, return None (key may be corrupted)
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to decrypt API key for user {self.id}: {str(e)}")
            return None
