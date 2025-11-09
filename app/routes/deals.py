"""API routes for credit card deals and promotions"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import and_
from app import db, csrf
from app.models import Deal

deals_bp = Blueprint('deals', __name__, url_prefix='/api/deals')


@deals_bp.route('', methods=['GET'])
@login_required
def list_deals():
    """
    Get all active deals with optional filtering

    Query parameters:
    - category: Filter by category (e.g., 'Dining', 'Travel')
    - merchant: Filter by merchant name
    - card_issuer: Filter by card issuer (e.g., 'BDO', 'Chase')
    - discount_type: Filter by discount type (e.g., 'Percentage', 'BOGO')
    - min_discount: Minimum discount percent (for percentage discounts)
    - card_type: Filter by card type (e.g., 'Credit Card')
    - search: Search in title and description
    - sort_by: Sort by field ('discount', 'date', 'quality')
    - limit: Number of results (default: 50, max: 100)
    - offset: Pagination offset (default: 0)
    """
    try:
        # Build base query for active deals
        query = Deal.query.filter(Deal.is_active == True)

        # Apply filters
        category = request.args.get('category')
        if category:
            query = query.filter(Deal.category.ilike(f'%{category}%'))

        merchant = request.args.get('merchant')
        if merchant:
            query = query.filter(Deal.merchant.ilike(f'%{merchant}%'))

        card_issuer = request.args.get('card_issuer')
        if card_issuer:
            query = query.filter(Deal.card_issuer.ilike(f'%{card_issuer}%'))

        discount_type = request.args.get('discount_type')
        if discount_type:
            query = query.filter(Deal.discount_type == discount_type)

        min_discount = request.args.get('min_discount', type=float)
        if min_discount:
            query = query.filter(Deal.discount_percent >= min_discount)

        card_type = request.args.get('card_type')
        if card_type:
            query = query.filter(Deal.card_type.ilike(f'%{card_type}%'))

        search = request.args.get('search')
        if search:
            search_term = f'%{search}%'
            query = query.filter(
                (Deal.title.ilike(search_term)) |
                (Deal.description.ilike(search_term)) |
                (Deal.merchant.ilike(search_term))
            )

        # Apply sorting
        sort_by = request.args.get('sort_by', 'date')
        if sort_by == 'discount':
            query = query.order_by(Deal.discount_percent.desc(), Deal.discount_amount.desc())
        elif sort_by == 'quality':
            query = query.order_by(Deal.data_quality_score.desc())
        else:  # default: date
            query = query.order_by(Deal.scraped_at.desc())

        # Apply pagination
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))

        total = query.count()
        deals = query.limit(limit).offset(offset).all()

        return jsonify({
            'success': True,
            'data': [deal.to_dict() for deal in deals],
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@deals_bp.route('/<int:deal_id>', methods=['GET'])
@login_required
def get_deal(deal_id):
    """Get a specific deal by ID"""
    try:
        deal = Deal.query.filter(and_(
            Deal.id == deal_id,
            Deal.is_active == True
        )).first()

        if not deal:
            return jsonify({
                'success': False,
                'error': 'Deal not found'
            }), 404

        return jsonify({
            'success': True,
            'data': deal.to_dict()
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@deals_bp.route('/categories', methods=['GET'])
@login_required
def get_categories():
    """Get list of unique categories"""
    try:
        categories = db.session.query(Deal.category).distinct().filter(
            Deal.is_active == True
        ).all()

        category_list = [cat[0] for cat in categories if cat[0]]

        return jsonify({
            'success': True,
            'data': sorted(category_list)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@deals_bp.route('/merchants', methods=['GET'])
@login_required
def get_merchants():
    """Get list of unique merchants"""
    try:
        merchants = db.session.query(Deal.merchant).distinct().filter(
            Deal.is_active == True
        ).all()

        merchant_list = [m[0] for m in merchants if m[0]]

        return jsonify({
            'success': True,
            'data': sorted(merchant_list)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@deals_bp.route('/card-issuers', methods=['GET'])
@login_required
def get_card_issuers():
    """Get list of unique card issuers"""
    try:
        issuers = db.session.query(Deal.card_issuer).distinct().filter(
            Deal.is_active == True
        ).all()

        issuer_list = [issuer[0] for issuer in issuers if issuer[0]]

        return jsonify({
            'success': True,
            'data': sorted(issuer_list)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@deals_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    """Get deals statistics"""
    try:
        total_deals = Deal.query.filter(Deal.is_active == True).count()
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
        ).scalar()

        return jsonify({
            'success': True,
            'data': {
                'total_deals': total_deals,
                'by_category': {cat: count for cat, count in by_category if cat},
                'by_issuer': {issuer: count for issuer, count in by_issuer if issuer},
                'average_discount_percent': float(avg_discount) if avg_discount else 0
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@deals_bp.route('/refresh', methods=['POST'])
@login_required
@csrf.exempt
def refresh_deals():
    """
    Admin endpoint to refresh deals from BDO API

    This fetches the latest promotional campaigns from BDO's backend
    and updates the database with fresh data.
    """
    try:
        from services.deals.scrapers.bdo_perx_api_scraper import BDOPerxScraper
        import logging

        logger = logging.getLogger(__name__)

        # Fetch fresh data from BDO
        scraper = BDOPerxScraper()
        fresh_deals = scraper.scrape()

        if fresh_deals:
            # Successfully fetched new deals - replace old ones
            Deal.query.delete()
            db.session.commit()

            for deal_data in fresh_deals:
                deal = Deal(**deal_data)
                db.session.add(deal)

            db.session.commit()

            return jsonify({
                'success': True,
                'message': f'Successfully refreshed {len(fresh_deals)} deals from BDO',
                'data': {
                    'deals_updated': len(fresh_deals),
                    'timestamp': __import__('datetime').datetime.utcnow().isoformat()
                }
            }), 200
        else:
            # API failed - keep existing deals and return graceful message
            current_count = Deal.query.filter(Deal.is_active == True).count()
            logger.warning(f"BDO API fetch failed, but maintaining {current_count} existing deals")

            return jsonify({
                'success': True,
                'message': f'BDO API temporarily unavailable. Showing {current_count} existing deals.',
                'data': {
                    'deals_updated': 0,
                    'deals_maintained': current_count,
                    'timestamp': __import__('datetime').datetime.utcnow().isoformat(),
                    'note': 'Displaying existing cached deals while API is unavailable'
                }
            }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
