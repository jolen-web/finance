"""Regex pattern model for receipt OCR extraction"""
from datetime import datetime
from app import db


class RegexPattern(db.Model):
    """Regex pattern for extracting data from receipts"""
    __tablename__ = 'regex_patterns'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    pattern = db.Column(db.String(500), nullable=False)
    description = db.Column(db.String(500), nullable=True)  # Human-readable description of what this pattern does
    pattern_type = db.Column(db.String(50), nullable=True)  # date, amount, merchant, item, tax, total, phone, email, address, etc.
    test_string = db.Column(db.Text, nullable=True)  # Example string to test pattern against
    expected_result = db.Column(db.Text, nullable=True)  # Expected output when pattern is applied to test_string
    account_type = db.Column(db.String(50), nullable=True)  # checking, savings, credit_card, etc.
    confidence_score = db.Column(db.Numeric(3, 2), default=0.5)  # Original confidence (0-1)
    effectiveness_score = db.Column(db.Numeric(3, 2), default=0.5)  # Calculated from success rate (0-1)
    success_count = db.Column(db.Integer, default=0)  # Number of successful matches
    fail_count = db.Column(db.Integer, default=0)  # Number of failed matches
    is_active = db.Column(db.Boolean, default=True)  # Whether pattern should be used in extraction
    is_example = db.Column(db.Boolean, default=False)  # Pre-populated example patterns
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime, nullable=True)  # When pattern was last used successfully
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref='regex_patterns')

    def __repr__(self):
        return f'<RegexPattern {self.pattern_type or "custom"}: {self.pattern[:30]}...>'

    def calculate_effectiveness(self):
        """Calculate effectiveness score based on success/fail ratio"""
        total = self.success_count + self.fail_count
        if total == 0:
            return self.effectiveness_score  # Return default if no usage yet
        success_rate = self.success_count / total
        self.effectiveness_score = success_rate
        return success_rate

    def record_success(self):
        """Record a successful pattern match"""
        self.success_count += 1
        self.last_used = datetime.utcnow()
        self.calculate_effectiveness()

    def record_failure(self):
        """Record a failed pattern match"""
        self.fail_count += 1
        self.calculate_effectiveness()
