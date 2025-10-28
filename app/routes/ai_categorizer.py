from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.services.ai_categorizer import AICategorizerAgent
from app.models import Transaction, Category, CategorizationRule
from app import db

bp = Blueprint('ai_categorizer', __name__, url_prefix='/ai-categorizer')

@bp.route('/')
def index():
    """AI Categorizer dashboard"""
    agent = AICategorizerAgent()

    # Get statistics
    total_transactions = Transaction.query.count()
    categorized = Transaction.query.filter(Transaction.category_id.isnot(None)).count()
    uncategorized = total_transactions - categorized

    rules = CategorizationRule.query.order_by(CategorizationRule.usage_count.desc()).limit(10).all()

    # Check if model exists
    model_exists = agent.load_model()

    stats = {
        'total_transactions': total_transactions,
        'categorized_transactions': categorized,
        'uncategorized_transactions': uncategorized,
        'categorized_percentage': round(categorized / total_transactions * 100, 1) if total_transactions > 0 else 0,
        'active_rules': CategorizationRule.query.count()
    }

    model_status = {
        'is_trained': model_exists,
        'training_samples': categorized,
        'num_categories': Category.query.count(),
        'last_trained': None
    }

    return render_template('ai_categorizer/index.html',
                         stats=stats,
                         model_status=model_status,
                         top_rules=rules)

@bp.route('/train', methods=['POST'])
def train():
    """Train the ML model"""
    agent = AICategorizerAgent()
    success, message = agent.learn_from_existing_transactions()

    if success:
        flash(message, 'success')
    else:
        flash(message, 'warning')

    return redirect(url_for('ai_categorizer.index'))

@bp.route('/auto-categorize', methods=['POST'])
def auto_categorize():
    """Auto-categorize all uncategorized transactions"""
    min_confidence = float(request.form.get('min_confidence', 0.6))

    agent = AICategorizerAgent()
    results = agent.auto_categorize_transactions(min_confidence=min_confidence)

    flash(f"Categorized {results['categorized']} transactions. "
          f"{results['low_confidence']} had low confidence and were skipped.", 'success')

    return redirect(url_for('ai_categorizer.index'))

@bp.route('/suggest/<int:transaction_id>')
def suggest(transaction_id):
    """Get category suggestions for a transaction"""
    transaction = Transaction.query.get_or_404(transaction_id)

    agent = AICategorizerAgent()
    suggestions = agent.get_suggestions(transaction.payee)

    return jsonify({
        'transaction_id': transaction_id,
        'payee': transaction.payee,
        'suggestions': suggestions
    })

@bp.route('/apply-suggestion', methods=['POST'])
def apply_suggestion():
    """Apply a category suggestion to a transaction"""
    transaction_id = request.form.get('transaction_id')
    category_id = request.form.get('category_id')
    create_rule = request.form.get('create_rule') == 'on'

    transaction = Transaction.query.get_or_404(transaction_id)
    transaction.category_id = category_id

    if create_rule:
        agent = AICategorizerAgent()
        agent.create_rule(transaction.payee, int(category_id), confidence=1.0, auto_learned=False)

    db.session.commit()

    flash('Category applied successfully!', 'success')
    return redirect(request.referrer or url_for('transactions.list_transactions'))

@bp.route('/rules')
def rules():
    """List all categorization rules"""
    rules = CategorizationRule.query.filter_by(user_id=current_user.id).order_by(CategorizationRule.usage_count.desc()).all()
    return render_template('ai_categorizer/rules.html', rules=rules)

@bp.route('/rules/<int:id>/delete', methods=['POST'])
def delete_rule(id):
    """Delete a categorization rule"""
    rule = CategorizationRule.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(rule)
    db.session.commit()

    flash('Rule deleted successfully!', 'success')
    return redirect(url_for('ai_categorizer.list_rules'))
