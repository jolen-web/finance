"""
Receipt Processing Service

Wrapper around existing receipt OCR functionality with enhanced service interface.
"""

from app.services.receipt_ocr import ReceiptOCR
from app.models import Receipt
from app import db


class ReceiptService:
    """Service for receipt processing and OCR."""

    @staticmethod
    def process_receipt(file_path, user_id):
        """Process a receipt image and extract data."""
        ocr = ReceiptOCR()
        extracted_data = ocr.extract_receipt_data(file_path)
        return extracted_data

    @staticmethod
    def save_receipt(user_id, file_path, transaction_id=None):
        """Save a receipt to the database."""
        receipt = Receipt(user_id=user_id, file_path=file_path, transaction_id=transaction_id)
        db.session.add(receipt)
        db.session.commit()
        return receipt

    @staticmethod
    def get_receipt(receipt_id):
        """Get a receipt by ID."""
        return Receipt.query.get(receipt_id)

    @staticmethod
    def get_user_receipts(user_id):
        """Get all receipts for a user."""
        return Receipt.query.filter_by(user_id=user_id).all()

    @staticmethod
    def delete_receipt(receipt_id):
        """Delete a receipt."""
        receipt = ReceiptService.get_receipt(receipt_id)
        if receipt:
            db.session.delete(receipt)
            db.session.commit()

    @staticmethod
    def link_receipt_to_transaction(receipt_id, transaction_id):
        """Link a receipt to a transaction."""
        receipt = ReceiptService.get_receipt(receipt_id)
        if receipt:
            receipt.transaction_id = transaction_id
            db.session.commit()
        return receipt
