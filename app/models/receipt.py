"""Receipt model for storing receipt uploads and OCR data"""
from datetime import datetime
from app import db


class Receipt(db.Model):
    """Uploaded receipt with OCR extraction data"""
    __tablename__ = 'receipts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id', ondelete='CASCADE'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(20), nullable=False)  # image/jpeg, image/png, application/pdf
    extracted_merchant = db.Column(db.String(200), nullable=True)
    extracted_date = db.Column(db.Date, nullable=True)
    extracted_amount = db.Column(db.Numeric(10, 2), nullable=True)
    extracted_items = db.Column(db.Text, nullable=True)  # JSON string of line items
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    user = db.relationship('User', backref='receipts')
    transaction = db.relationship('Transaction', backref=db.backref('receipts', cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<Receipt {self.filename}>'
