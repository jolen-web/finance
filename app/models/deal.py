"""Deal model for credit card offers and promotions"""
from datetime import datetime
from app import db


class Deal(db.Model):
    """Credit card deal/promotion with filtering and search capabilities"""
    __tablename__ = 'deals'

    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(100), nullable=False)  # e.g., 'bdo_website', 'chase_website'
    card_issuer = db.Column(db.String(100), nullable=False)  # e.g., 'BDO', 'Chase', 'Amex'
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    merchant = db.Column(db.String(255))  # e.g., 'Pizza Hut', 'The Podium'
    category = db.Column(db.String(100))  # e.g., 'Dining', 'Travel', 'Shopping'
    card_type = db.Column(db.String(100))  # e.g., 'Credit Card', 'Debit Card'

    # Discount information
    discount_type = db.Column(db.String(50))  # 'Percentage', 'Fixed', 'BOGO', 'Points'
    discount_percent = db.Column(db.Float)  # e.g., 30.0 for 30% off
    discount_amount = db.Column(db.Float)  # e.g., 500.0 for ₱500 off
    reward_points = db.Column(db.Integer)  # e.g., 1000 for 1000 bonus points
    cashback_percent = db.Column(db.Float)  # e.g., 5.0 for 5% cashback

    # Promotion dates
    promotion_start_date = db.Column(db.String(50))  # e.g., '11/09/2025'
    promotion_end_date = db.Column(db.String(50))  # e.g., '12/31/2025'

    # Additional details
    url = db.Column(db.String(500))  # Link to deal details
    promotion_details = db.Column(db.Text)  # Extra promotion details
    data_quality_score = db.Column(db.Float, default=0.5)  # 0-1 quality score

    # Metadata
    scraped_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Deal {self.title} - {self.card_issuer}>'

    def to_dict(self):
        """Convert deal to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'source': self.source,
            'card_issuer': self.card_issuer,
            'title': self.title,
            'description': self.description,
            'merchant': self.merchant,
            'category': self.category,
            'card_type': self.card_type,
            'discount': {
                'type': self.discount_type,
                'percent': self.discount_percent,
                'amount': self.discount_amount,
                'points': self.reward_points,
                'cashback': self.cashback_percent,
            },
            'promotion': {
                'start_date': self.promotion_start_date,
                'end_date': self.promotion_end_date,
                'details': self.promotion_details,
            },
            'url': self.url,
            'quality_score': self.data_quality_score,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
            'is_active': self.is_active,
        }
