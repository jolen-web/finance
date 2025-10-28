from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models import DashboardPreferences
from app import db
from app.services.dashboard import DashboardService

bp = Blueprint('main', __name__)

@bp.route('/')
@login_required
def index():
    """Dashboard view showing account summary and recent transactions"""
    # Get dashboard data from the service layer
    service = DashboardService(user_id=current_user.id)
    dashboard_data = service.get_net_worth_data()

    # Get or create dashboard preferences for user
    prefs = DashboardPreferences.query.filter_by(user_id=current_user.id).first()
    if not prefs:
        prefs = DashboardPreferences(user_id=current_user.id)
        db.session.add(prefs)
        db.session.commit()

    return render_template('dashboard.html', **dashboard_data, prefs=prefs)
