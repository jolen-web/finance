#!/usr/bin/env python3
"""
Seed example regex patterns for all users.
Run this from the web container: docker-compose exec web python seed_patterns.py
"""
import sys
sys.path.insert(0, '/app')

from app import create_app, db
from app.models import User, RegexPattern
from app.seeds.regex_patterns import EXAMPLE_PATTERNS

def seed_patterns():
    """Seed example patterns for all users"""
    app = create_app()

    with app.app_context():
        users = User.query.all()
        print(f"Found {len(users)} users")

        for user in users:
            # Check if user already has example patterns
            existing_examples = RegexPattern.query.filter_by(
                user_id=user.id,
                is_example=True
            ).count()

            if existing_examples == 0:
                print(f"\n  Seeding patterns for user: {user.username}")
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
                print(f"    ✓ Seeded {len(EXAMPLE_PATTERNS)} example patterns")
            else:
                print(f"\n  User {user.username} already has {existing_examples} example patterns - skipping")

        print("\n✅ Pattern seeding complete!")

if __name__ == '__main__':
    seed_patterns()
