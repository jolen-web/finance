"""
Pre-populated regex pattern examples for receipt extraction.

These patterns are commonly used for extracting key information from receipts.
Users can customize, disable, or delete patterns as needed.
"""

EXAMPLE_PATTERNS = [
    {
        "pattern": r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})",
        "description": "Extract date in MM/DD/YYYY or DD/MM/YYYY format",
        "pattern_type": "date",
        "test_string": "Purchase date: 11/02/2025",
        "expected_result": "11/02/2025",
        "confidence_score": 0.95,
        "is_example": True,
    },
    {
        "pattern": r"\$?\d+\.?\d{0,2}(?:\s*(?:usd|cad|eur|gbp))?",
        "description": "Extract monetary amounts with optional currency symbols",
        "pattern_type": "amount",
        "test_string": "Total: $45.99 USD",
        "expected_result": "$45.99",
        "confidence_score": 0.92,
        "is_example": True,
    },
    {
        "pattern": r"(?:total|subtotal|amount due|balance due|total amount)[\s:]*\$?([\d,]+\.?\d{0,2})",
        "description": "Extract total amount from receipt lines",
        "pattern_type": "total",
        "test_string": "Total Amount Due: $127.45",
        "expected_result": "$127.45",
        "confidence_score": 0.88,
        "is_example": True,
    },
    {
        "pattern": r"(?:tax|sales tax|tax amount|gst|vat)[\s:]*\$?([\d,]+\.?\d{0,2})",
        "description": "Extract tax amount from receipt",
        "pattern_type": "tax",
        "test_string": "Sales Tax: $8.50",
        "expected_result": "$8.50",
        "confidence_score": 0.85,
        "is_example": True,
    },
    {
        "pattern": r"(?:merchant|store|vendor|restaurant|location)[\s:]*([^\n]+)",
        "description": "Extract merchant/store name",
        "pattern_type": "merchant",
        "test_string": "Merchant: Whole Foods Market #1234",
        "expected_result": "Whole Foods Market #1234",
        "confidence_score": 0.80,
        "is_example": True,
    },
    {
        "pattern": r"(\d{1,3})\s*x\s*([\w\s]+?)\s*@?\s*\$?([\d.]+)(?:\s|$)",
        "description": "Extract item quantity x description @ price format",
        "pattern_type": "item",
        "test_string": "2 x Organic Apples @ $3.99 each",
        "expected_result": "2 x Organic Apples @ $3.99",
        "confidence_score": 0.75,
        "is_example": True,
    },
    {
        "pattern": r"(?:item|product|qty|quantity)\s*:?\s*([^\n$]+?)\s*(?:\$|$)",
        "description": "Extract product/item descriptions",
        "pattern_type": "item",
        "test_string": "Item: Organic Milk 1L",
        "expected_result": "Organic Milk 1L",
        "confidence_score": 0.78,
        "is_example": True,
    },
    {
        "pattern": r"(?:subtotal|sub-total|base amount)[\s:]*\$?([\d,]+\.?\d{0,2})",
        "description": "Extract subtotal before tax",
        "pattern_type": "total",
        "test_string": "Subtotal: $118.95",
        "expected_result": "$118.95",
        "confidence_score": 0.90,
        "is_example": True,
    },
    {
        "pattern": r"(?:phone|tel|contact)[\s:]*(\d{3}[-.]?\d{3}[-.]?\d{4})",
        "description": "Extract phone numbers in XXX-XXX-XXXX format",
        "pattern_type": "phone",
        "test_string": "Phone: 555-123-4567",
        "expected_result": "555-123-4567",
        "confidence_score": 0.88,
        "is_example": True,
    },
    {
        "pattern": r"(?:address|location|store #|store number)[\s:]*([^\n]+)",
        "description": "Extract store address or location",
        "pattern_type": "address",
        "test_string": "Store #: 1234 Main St, Springfield, IL 62701",
        "expected_result": "1234 Main St, Springfield, IL 62701",
        "confidence_score": 0.75,
        "is_example": True,
    },
    {
        "pattern": r"\b([A-Z][A-Z0-9]{2,9})\b",
        "description": "Extract product codes or SKUs",
        "pattern_type": "item",
        "test_string": "SKU: ABC123DEF",
        "expected_result": "ABC123DEF",
        "confidence_score": 0.65,
        "is_example": True,
    },
    {
        "pattern": r"(?:discount|savings|promo|coupon)[\s:]*-?\$?([\d.]+)(?:%)?",
        "description": "Extract discount or promotional amounts",
        "pattern_type": "amount",
        "test_string": "Discount: -$10.00",
        "expected_result": "-$10.00",
        "confidence_score": 0.82,
        "is_example": True,
    },
    {
        "pattern": r"(?:cashback|rebate)[\s:]*\$?([\d.]+)",
        "description": "Extract cashback or rebate amounts",
        "pattern_type": "amount",
        "test_string": "Cashback: $2.50",
        "expected_result": "$2.50",
        "confidence_score": 0.79,
        "is_example": True,
    },
]


def seed_regex_patterns(db, User):
    """
    Seed the database with example regex patterns for all users.
    This creates example patterns for the first admin/system user.

    Usage in migration or initialization:
        from app.seeds.regex_patterns import seed_regex_patterns
        seed_regex_patterns(db, User)
    """
    from app.models import RegexPattern

    # Only seed patterns for existing users who don't have them
    users = User.query.all()

    for user in users:
        # Check if user already has example patterns
        existing_examples = RegexPattern.query.filter_by(
            user_id=user.id,
            is_example=True
        ).count()

        if existing_examples == 0:
            # Add all example patterns for this user
            for pattern_data in EXAMPLE_PATTERNS:
                pattern = RegexPattern(
                    user_id=user.id,
                    pattern=pattern_data["pattern"],
                    description=pattern_data["description"],
                    pattern_type=pattern_data["pattern_type"],
                    test_string=pattern_data["test_string"],
                    expected_result=pattern_data["expected_result"],
                    confidence_score=pattern_data["confidence_score"],
                    is_example=True,
                    is_active=True,
                )
                db.session.add(pattern)

            db.session.commit()
            print(f"✓ Seeded {len(EXAMPLE_PATTERNS)} example regex patterns for user: {user.username}")
