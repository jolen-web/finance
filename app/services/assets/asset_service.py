"""
Asset Management Service

Provides CRUD operations for tracking valuable assets.
"""

from app import db
from app.models import Asset


class AssetService:
    """Service for managing assets."""

    @staticmethod
    def create_asset(user_id, name, asset_type, current_value, description=None):
        """Create a new asset."""
        asset = Asset(
            user_id=user_id,
            name=name,
            type=asset_type,
            current_value=current_value,
            description=description
        )
        db.session.add(asset)
        db.session.commit()
        return asset

    @staticmethod
    def get_asset(asset_id):
        """Get an asset by ID."""
        return Asset.query.get(asset_id)

    @staticmethod
    def get_user_assets(user_id):
        """Get all assets for a user."""
        return Asset.query.filter_by(user_id=user_id).all()

    @staticmethod
    def update_asset(asset_id, **kwargs):
        """Update asset information."""
        asset = AssetService.get_asset(asset_id)
        if not asset:
            raise ValueError(f"Asset {asset_id} not found")

        allowed_fields = {'name', 'type', 'current_value', 'description'}
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(asset, field, value)

        db.session.commit()
        return asset

    @staticmethod
    def delete_asset(asset_id):
        """Delete an asset."""
        asset = AssetService.get_asset(asset_id)
        if not asset:
            raise ValueError(f"Asset {asset_id} not found")

        db.session.delete(asset)
        db.session.commit()

    @staticmethod
    def get_total_assets_value(user_id):
        """Get total value of all assets."""
        assets = AssetService.get_user_assets(user_id)
        return sum(asset.current_value for asset in assets)
