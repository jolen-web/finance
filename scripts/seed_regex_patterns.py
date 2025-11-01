import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import RegexPattern, User

def seed_regex_patterns():
    app = create_app()
    with app.app_context():
        # Get the first user to associate the patterns with
        user = User.query.first()
        if not user:
            print("No users found in the database. Please create a user first.")
            return

        patterns = [
            # Pattern 1: Two dates followed by description and amount
            {'pattern': r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s+(.+?)\s+([\d,]+\.\d{2})\s*$', 'account_type': 'credit_card', 'score': 0.8},
            # Pattern 2: MM/DD/YY Description Amount
            {'pattern': r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+(.+?)\s+([\d,]+\.\d{2})$', 'account_type': 'credit_card', 'score': 0.9},
            # Pattern 3: Date in YYYY-MM-DD format
            {'pattern': r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})\s+(.+?)\s+([\d,]+\.\d{2})$', 'account_type': 'credit_card', 'score': 0.9},
            # Pattern 4: Month name format
            {'pattern': r'([A-Za-z]+\s+\d{1,2},?\s+\d{4})\s+(.+?)\s+([\d,]+\.\d{2})\s*$', 'account_type': 'credit_card', 'score': 0.8},
        ]

        for p in patterns:
            existing_pattern = RegexPattern.query.filter_by(user_id=user.id, pattern=p['pattern']).first()
            if not existing_pattern:
                new_pattern = RegexPattern(
                    user_id=user.id,
                    pattern=p['pattern'],
                    account_type=p['account_type'],
                    confidence_score=p['score']
                )
                db.session.add(new_pattern)

        db.session.commit()
        print(f"Seeded {len(patterns)} regex patterns for user {user.username}.")

if __name__ == '__main__':
    seed_regex_patterns()
