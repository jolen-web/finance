"""Base classes and mixins for models"""
from datetime import datetime
from app import db


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps"""
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
