"""Asset model for tracking user assets"""
from datetime import datetime
from app import db


class Asset(db.Model):
    """User asset (house, vehicle, electronics, jewelry, art, collectible)"""
    __tablename__ = 'assets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)  # e.g., "My House", "Toyota Camry", "Laptop"
    asset_type = db.Column(db.String(50), nullable=False)  # house, lot, vehicle, electronics, jewelry, art, collectible, other
    purchase_price = db.Column(db.Numeric(14, 2), nullable=True)  # Original cost
    current_value = db.Column(db.Numeric(14, 2), nullable=False, default=0)  # Current estimated value
    purchase_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = db.relationship('User', backref='assets')

    def __repr__(self):
        return f'<Asset {self.name}>'

    def get_gain_loss(self):
        """Calculate gain/loss on asset"""
        if self.purchase_price:
            return self.current_value - self.purchase_price
        return 0

    def get_gain_loss_percentage(self):
        """Calculate gain/loss percentage"""
        if self.purchase_price and self.purchase_price > 0:
            return ((self.current_value - self.purchase_price) / self.purchase_price) * 100
        return 0
