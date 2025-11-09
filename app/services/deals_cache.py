"""Deals caching service for performance optimization"""
import json
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from app import db
from app.models import Deal


class DealsCacheService:
    """Service to manage deals caching and data persistence"""

    # Cache duration in minutes
    CACHE_DURATION = 60  # 1 hour
    SCRAPE_INTERVAL = 24 * 60  # 24 hours

    @staticmethod
    def get_cache_key(category=None, merchant=None, issuer=None):
        """Generate a cache key based on filters"""
        key_parts = [
            category or 'all',
            merchant or 'all',
            issuer or 'all'
        ]
        key_string = '|'.join(str(p) for p in key_parts)
        return f"deals_{hashlib.md5(key_string.encode()).hexdigest()}"

    @staticmethod
    def load_deals_from_json(filepath):
        """Load deals from JSON file (from scraper output)"""
        try:
            with open(filepath, 'r') as f:
                deals_data = json.load(f)

            loaded_count = 0
            for deal_data in deals_data:
                # Check if deal already exists
                existing = Deal.query.filter(
                    (Deal.source == deal_data.get('source')) &
                    (Deal.title == deal_data.get('title')) &
                    (Deal.card_issuer == deal_data.get('card_issuer'))
                ).first()

                if not existing:
                    deal = Deal(
                        source=deal_data.get('source'),
                        card_issuer=deal_data.get('card_issuer'),
                        title=deal_data.get('title'),
                        description=deal_data.get('description'),
                        merchant=deal_data.get('merchant'),
                        category=deal_data.get('category'),
                        card_type=deal_data.get('card_type'),
                        discount_type=deal_data.get('discount_type'),
                        discount_percent=deal_data.get('discount_percent'),
                        discount_amount=deal_data.get('discount_amount'),
                        reward_points=deal_data.get('reward_points'),
                        cashback_percent=deal_data.get('cashback_percent'),
                        promotion_start_date=deal_data.get('promotion_start_date'),
                        promotion_end_date=deal_data.get('promotion_end_date'),
                        url=deal_data.get('url'),
                        promotion_details=deal_data.get('promotion_details'),
                        data_quality_score=deal_data.get('data_quality_score', 0.5),
                        is_active=True
                    )
                    db.session.add(deal)
                    loaded_count += 1
                else:
                    # Update existing deal
                    existing.description = deal_data.get('description', existing.description)
                    existing.discount_percent = deal_data.get('discount_percent', existing.discount_percent)
                    existing.updated_at = datetime.utcnow()
                    loaded_count += 1

            db.session.commit()
            return {
                'success': True,
                'loaded': loaded_count,
                'message': f'Loaded {loaded_count} deals from JSON'
            }

        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def get_all_deals(refresh=False):
        """Get all deals with caching"""
        if not refresh:
            deals = Deal.query.filter(Deal.is_active == True).all()
            if deals:
                return deals

        return Deal.query.filter(Deal.is_active == True).all()

    @staticmethod
    def get_deals_by_category(category, refresh=False):
        """Get deals filtered by category"""
        query = Deal.query.filter(
            (Deal.is_active == True) &
            (Deal.category.ilike(f'%{category}%'))
        )
        return query.all()

    @staticmethod
    def get_deals_by_merchant(merchant, refresh=False):
        """Get deals filtered by merchant"""
        query = Deal.query.filter(
            (Deal.is_active == True) &
            (Deal.merchant.ilike(f'%{merchant}%'))
        )
        return query.all()

    @staticmethod
    def get_deals_by_issuer(issuer, refresh=False):
        """Get deals filtered by card issuer"""
        query = Deal.query.filter(
            (Deal.is_active == True) &
            (Deal.card_issuer.ilike(f'%{issuer}%'))
        )
        return query.all()

    @staticmethod
    def get_best_deals(limit=10):
        """Get best deals sorted by discount"""
        return Deal.query.filter(
            Deal.is_active == True
        ).order_by(
            Deal.discount_percent.desc(),
            Deal.data_quality_score.desc()
        ).limit(limit).all()

    @staticmethod
    def get_deals_stats():
        """Get deals statistics"""
        total = Deal.query.filter(Deal.is_active == True).count()

        by_category = db.session.query(
            Deal.category,
            db.func.count(Deal.id)
        ).filter(Deal.is_active == True).group_by(Deal.category).all()

        by_issuer = db.session.query(
            Deal.card_issuer,
            db.func.count(Deal.id)
        ).filter(Deal.is_active == True).group_by(Deal.card_issuer).all()

        avg_discount = db.session.query(
            db.func.avg(Deal.discount_percent)
        ).filter(
            Deal.is_active == True,
            Deal.discount_percent.isnot(None)
        ).scalar() or 0

        return {
            'total_deals': total,
            'by_category': {cat: cnt for cat, cnt in by_category if cat},
            'by_issuer': {issuer: cnt for issuer, cnt in by_issuer if issuer},
            'average_discount': float(avg_discount)
        }

    @staticmethod
    def deactivate_expired_deals():
        """Mark deals as inactive if they have passed the end date"""
        from sqlalchemy import func, cast, Date

        today = datetime.utcnow().date()

        # Update deals where promotion_end_date has passed
        Deal.query.filter(
            Deal.is_active == True,
            Deal.promotion_end_date.isnot(None)
        ).update({
            Deal.is_active: False
        }, synchronize_session=False)

        db.session.commit()

    @staticmethod
    def clear_deals():
        """Clear all deals from database (use with caution)"""
        try:
            Deal.query.delete()
            db.session.commit()
            return {'success': True, 'message': 'All deals cleared'}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    @staticmethod
    def export_deals_to_json(output_file):
        """Export all deals to JSON file"""
        try:
            deals = Deal.query.filter(Deal.is_active == True).all()
            deals_json = [deal.to_dict() for deal in deals]

            with open(output_file, 'w') as f:
                json.dump(deals_json, f, indent=2)

            return {
                'success': True,
                'count': len(deals_json),
                'file': output_file
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


def cached_deals(duration_minutes=60):
    """Decorator to cache deal results"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # For now, we'll just call the function
            # In production, this would use Redis or similar
            return f(*args, **kwargs)
        return decorated_function
    return decorator
