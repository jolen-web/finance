from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Feedback

feedback_bp = Blueprint('feedback', __name__, url_prefix='/feedback')


@feedback_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_feedback():
    """Create new feedback"""
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            feedback = Feedback(
                user_id=current_user.id,
                feedback_type=data.get('feedback_type', 'other'),
                title=data.get('title'),
                description=data.get('description'),
                priority=data.get('priority', 'medium')
            )
        else:
            feedback = Feedback(
                user_id=current_user.id,
                feedback_type=request.form.get('feedback_type', 'other'),
                title=request.form.get('title'),
                description=request.form.get('description'),
                priority=request.form.get('priority', 'medium')
            )

        if not feedback.title or not feedback.description:
            if request.is_json:
                return jsonify({'message': 'Title and description are required', 'errors': {}}), 400
            flash('Title and description are required', 'error')
            return redirect(url_for('feedback.new_feedback'))

        db.session.add(feedback)
        db.session.commit()

        if request.is_json:
            return jsonify({
                'message': 'Thank you for your feedback!',
                'redirect': url_for('feedback.list_feedback')
            }), 200

        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('feedback.list_feedback'))

    return render_template('feedback/new.html')


@feedback_bp.route('/', methods=['GET'])
@login_required
def list_feedback():
    """View all user feedback"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')

    query = Feedback.query.filter_by(user_id=current_user.id)

    if status_filter:
        query = query.filter_by(status=status_filter)

    feedback_items = query.order_by(Feedback.created_at.desc()).paginate(page=page, per_page=10)

    return render_template('feedback/list.html', feedback_items=feedback_items, status_filter=status_filter)


@feedback_bp.route('/<int:feedback_id>', methods=['GET'])
@login_required
def view_feedback(feedback_id):
    """View feedback details"""
    feedback = Feedback.query.get_or_404(feedback_id)

    # Ensure user can only view their own feedback
    if feedback.user_id != current_user.id:
        flash('You do not have permission to view this feedback', 'error')
        return redirect(url_for('feedback.list_feedback'))

    return render_template('feedback/view.html', feedback=feedback)


@feedback_bp.route('/<int:feedback_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_feedback(feedback_id):
    """Edit feedback"""
    feedback = Feedback.query.get_or_404(feedback_id)

    # Ensure user can only edit their own feedback
    if feedback.user_id != current_user.id:
        flash('You do not have permission to edit this feedback', 'error')
        return redirect(url_for('feedback.list_feedback'))

    if request.method == 'POST':
        feedback.feedback_type = request.form.get('feedback_type', feedback.feedback_type)
        feedback.title = request.form.get('title', feedback.title)
        feedback.description = request.form.get('description', feedback.description)
        feedback.priority = request.form.get('priority', feedback.priority)

        if not feedback.title or not feedback.description:
            flash('Title and description are required', 'error')
            return redirect(url_for('feedback.edit_feedback', feedback_id=feedback_id))

        db.session.commit()
        flash('Feedback updated successfully', 'success')
        return redirect(url_for('feedback.view_feedback', feedback_id=feedback_id))

    return render_template('feedback/edit.html', feedback=feedback)


@feedback_bp.route('/<int:feedback_id>/delete', methods=['POST'])
@login_required
def delete_feedback(feedback_id):
    """Delete feedback"""
    feedback = Feedback.query.get_or_404(feedback_id)

    # Ensure user can only delete their own feedback
    if feedback.user_id != current_user.id:
        flash('You do not have permission to delete this feedback', 'error')
        return redirect(url_for('feedback.list_feedback'))

    db.session.delete(feedback)
    db.session.commit()
    flash('Feedback deleted successfully', 'success')
    return redirect(url_for('feedback.list_feedback'))
