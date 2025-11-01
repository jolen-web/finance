from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from app.models import RegexPattern

bp = Blueprint('diag', __name__, url_prefix='/diag')

@bp.route('/show-regex-patterns')
@login_required
def show_regex_patterns():
    patterns = RegexPattern.query.filter_by(user_id=current_user.id).all()
    patterns_data = []
    for p in patterns:
        patterns_data.append({
            'id': p.id,
            'pattern': p.pattern,
            'account_type': p.account_type,
            'confidence_score': p.confidence_score,
            'created_at': p.created_at.isoformat()
        })
    return jsonify(patterns_data)
