"""Auto-categorize existing uncategorized transactions using smart categorization"""
from app import create_app, db
from app.models import Transaction, User
from app.services.categorizer import TransactionCategorizer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def auto_categorize_transactions():
    """Auto-categorize all uncategorized transactions for all users"""
    app = create_app()

    with app.app_context():
        # Get all users
        users = User.query.all()

        if not users:
            print("No users found!")
            return

        for user in users:
            print(f"\n{'='*60}")
            print(f"Processing user: {user.username}")
            print(f"{'='*60}")

            # Get uncategorized transactions for this user
            uncategorized = Transaction.query.filter_by(
                user_id=user.id,
                category_id=None
            ).all()

            if not uncategorized:
                print(f"✅ No uncategorized transactions for {user.username}")
                continue

            print(f"Found {len(uncategorized)} uncategorized transactions")

            # Initialize categorizer for this user
            categorizer = TransactionCategorizer(user.id)

            categorized_count = 0
            failed_count = 0

            for i, trans in enumerate(uncategorized, 1):
                try:
                    payee = trans.payee or "Unknown"
                    description = trans.memo or ""

                    # Get categorization
                    category_id, is_from_cache, reason = categorizer.categorize_transaction(
                        payee=payee,
                        description=description,
                        amount=trans.amount
                    )

                    if category_id:
                        # Update transaction
                        trans.category_id = category_id
                        db.session.add(trans)

                        cache_status = "📦 (cached)" if is_from_cache else "🤖 (LLM)"
                        print(f"  {i}. {payee[:40]:40} → Category {cache_status} [{reason}]")
                        categorized_count += 1
                    else:
                        print(f"  {i}. {payee[:40]:40} → ❌ Failed to categorize")
                        failed_count += 1

                except Exception as e:
                    logger.error(f"Error categorizing transaction {trans.id}: {str(e)}")
                    print(f"  {i}. {payee[:40]:40} → ❌ Error: {str(e)}")
                    failed_count += 1

            # Commit all changes
            db.session.commit()

            print(f"\n✅ User {user.username} results:")
            print(f"   Categorized: {categorized_count}/{len(uncategorized)}")
            print(f"   Failed: {failed_count}/{len(uncategorized)}")

            # Show cache stats
            stats = categorizer.get_cache_stats()
            print(f"\n📊 Cache Statistics:")
            print(f"   Total mappings: {stats['total_mappings']}")
            if stats['most_used']:
                print(f"   Most used payees:")
                for payee, category, freq in stats['most_used'][:5]:
                    print(f"     - {payee}: {category} (used {freq}x)")

        print(f"\n{'='*60}")
        print("✅ Auto-categorization complete!")
        print(f"{'='*60}")


if __name__ == '__main__':
    auto_categorize_transactions()
