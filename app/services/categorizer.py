"""Smart transaction categorization service using cache and LLM fallback"""
import logging
from app.models import PayeeCategory, Category, Transaction
from app import db
import google.generativeai as genai

logger = logging.getLogger(__name__)


class TransactionCategorizer:
    """Smart categorization using cache and LLM suggestions"""

    def __init__(self, user_id):
        self.user_id = user_id

    def categorize_transaction(self, payee, description=None, amount=None):
        """
        Categorize a transaction using cache or LLM suggestion.

        Returns: (category_id, is_from_cache, suggestion_text)
        """
        if not payee:
            return None, False, "No payee provided"

        # Step 1: Check cache for existing payee mapping
        cached = PayeeCategory.query.filter_by(
            payee=payee
        ).first()

        if cached:
            return cached.category_id, True, f"Categorized as '{cached.category.name}' (cached)"

        # Step 2: Use LLM to suggest category if not in cache
        suggestion = self._suggest_category_with_llm(payee, description, amount)

        if suggestion and suggestion.get('category_id'):
            # Save to cache for future use
            self._save_to_cache(payee, suggestion['category_id'])
            return suggestion['category_id'], False, suggestion.get('reason', 'LLM suggested')

        return None, False, "Unable to categorize"

    def _suggest_category_with_llm(self, payee, description=None, amount=None):
        """Use Gemini to suggest the best category for a transaction"""
        try:
            # Get available categories for this user
            categories = Category.query.all()
            category_names = [cat.name for cat in categories]

            if not category_names:
                logger.warning(f"No categories found for user {self.user_id}")
                return None

            # Create the prompt
            prompt = f"""You are a financial categorization expert. Based on the merchant/payee name, suggest the most appropriate expense category.

Merchant/Payee: {payee}
{f'Description: {description}' if description else ''}
{f'Amount: {amount}' if amount else ''}

Available categories: {', '.join(category_names)}

Choose the MOST SPECIFIC and RELEVANT category from the list above. Respond in this exact format:
CATEGORY: [category name]
CONFIDENCE: [high/medium/low]
REASON: [brief explanation]

Be strict - only use categories from the provided list."""

            # Call Gemini API
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(prompt)

            if not response.text:
                logger.warning(f"Empty response from Gemini for payee: {payee}")
                return None

            # Parse the response
            result = self._parse_llm_response(response.text, categories)
            return result

        except Exception as e:
            logger.error(f"Error in LLM categorization: {str(e)}")
            return None

    def _parse_llm_response(self, response_text, categories):
        """Parse LLM response and extract category"""
        try:
            lines = response_text.strip().split('\n')
            category_name = None
            reason = ""

            for line in lines:
                if 'CATEGORY:' in line:
                    category_name = line.split('CATEGORY:')[1].strip()
                elif 'REASON:' in line:
                    reason = line.split('REASON:')[1].strip()

            if not category_name:
                logger.warning(f"Could not extract category from LLM response: {response_text}")
                return None

            # Find the category by name
            category = next((cat for cat in categories if cat.name.lower() == category_name.lower()), None)

            if category:
                return {
                    'category_id': category.id,
                    'category_name': category.name,
                    'reason': reason or f"LLM suggested '{category.name}'"
                }
            else:
                logger.warning(f"LLM suggested category '{category_name}' not found in user's categories")
                return None

        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            return None

    def _save_to_cache(self, payee, category_id):
        """Save payee → category mapping to cache"""
        try:
            # Check if already exists
            existing = PayeeCategory.query.filter_by(
                payee=payee,
                category_id=category_id
            ).first()

            if existing:
                # Increment frequency
                existing.frequency += 1
                db.session.commit()
            else:
                # Create new mapping
                mapping = PayeeCategory(
                    payee=payee,
                    category_id=category_id
                )
                db.session.add(mapping)
                db.session.commit()

            logger.info(f"Saved payee cache: {payee} → category_id {category_id}")
        except Exception as e:
            logger.error(f"Error saving to cache: {str(e)}")
            db.session.rollback()

    def update_mapping(self, payee, category_id):
        """Update or create a payee → category mapping"""
        try:
            # Find or create
            mapping = PayeeCategory.query.filter_by(
                payee=payee
            ).first()

            if mapping:
                mapping.category_id = category_id
                mapping.frequency += 1
            else:
                mapping = PayeeCategory(
                    payee=payee,
                    category_id=category_id
                )
                db.session.add(mapping)

            db.session.commit()
            logger.info(f"Updated mapping: {payee} → category_id {category_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating mapping: {str(e)}")
            db.session.rollback()
            return False

    def get_cache_stats(self):
        """Get statistics about cached payee mappings"""
        total = PayeeCategory.query.count()
        most_used = PayeeCategory.query.order_by(
            PayeeCategory.frequency.desc()
        ).limit(10).all()

        return {
            'total_mappings': total,
            'most_used': [(m.payee, m.category.name, m.frequency) for m in most_used]
        }
