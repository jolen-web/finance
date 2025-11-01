from flask import Flask, g, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)
db_manager = None

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    login_manager.login_view = 'auth.login'

    # Security headers with Talisman (only in production)
    if app.config['FLASK_ENV'] == 'production':
        csp = {
            'default-src': "'self'",
            'img-src': ['*', 'data:', 'blob:'],
            'script-src': ["'self'", "'unsafe-inline'", 'cdn.jsdelivr.net', 'unpkg.com'],
            'style-src': ["'self'", "'unsafe-inline'", 'cdn.jsdelivr.net', 'fonts.googleapis.com'],
            'font-src': ["'self'", 'fonts.gstatic.com'],
            'connect-src': "'self'"
        }
        Talisman(app,
                 content_security_policy=csp,
                 force_https=True,
                 strict_transport_security=True,
                 session_cookie_secure=True,
                 session_cookie_samesite='Lax')

    from app.db_manager import DBManager
    app.db_manager = DBManager(db)

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # Register blueprints
    from app.routes import main, accounts, transactions, categories, backup, backup_view, settings, receipts, ai_categorizer, financial_advisor, tax_assistant, scenario_planner, investments, auth, assets, diag
    from app.routes import migrate as migrate_routes
    app.register_blueprint(main.bp)
    app.register_blueprint(accounts.bp)
    app.register_blueprint(transactions.bp)
    app.register_blueprint(categories.bp)
    app.register_blueprint(backup.bp)
    app.register_blueprint(backup_view.bp_view)
    app.register_blueprint(settings.bp)
    app.register_blueprint(receipts.bp)
    app.register_blueprint(ai_categorizer.bp)
    app.register_blueprint(financial_advisor.bp)
    app.register_blueprint(tax_assistant.bp)
    app.register_blueprint(scenario_planner.bp)
    app.register_blueprint(investments.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(assets.bp)
    app.register_blueprint(diag.bp)
    app.register_blueprint(migrate_routes.bp)

    # Ensure data directory exists
    import os
    data_dir = os.path.join(app.root_path, '..', 'data')
    os.makedirs(data_dir, exist_ok=True)

    # Configure structured logging for Cloud Run
    if app.config['FLASK_ENV'] == 'production':
        import logging
        import sys
        from pythonjsonlogger import jsonlogger

        logHandler = logging.StreamHandler(sys.stdout)
        formatter = jsonlogger.JsonFormatter()
        logHandler.setFormatter(formatter)
        app.logger.addHandler(logHandler)
        app.logger.setLevel(logging.INFO)

    # Register template filters
    from app.routes.settings import get_currency_info

    @app.template_filter('currency')
    def currency_filter(amount, show_sign=False):
        """Format amount with current currency symbol and thousands separators"""
        if amount is None:
            amount = 0

        currency_info = get_currency_info()
        symbol = currency_info['symbol']
        position = currency_info.get('position', 'before')

        # Format with thousands separators and 2 decimal places
        abs_amount = abs(float(amount))
        formatted_amount = f"{abs_amount:,.2f}"

        if position == 'before':
            result = f"{symbol}{formatted_amount}"
        else:
            result = f"{formatted_amount}{symbol}"

        if show_sign and amount != 0:
            result = f"+{result}" if amount > 0 else f"-{result}"
        elif amount < 0:
            result = f"-{result}"

        return result

    @app.template_filter('currency_symbol')
    def currency_symbol_filter(value):
        """Get current currency symbol (value argument ignored, required by Jinja2)"""
        currency_info = get_currency_info()
        return currency_info['symbol']

    # Context processor to inject dashboard preferences into all templates
    @app.context_processor
    def inject_dashboard_prefs():
        """Inject dashboard preferences into template context for all pages"""
        try:
            if current_user.is_authenticated and current_user.id:
                from app.models import DashboardPreferences
                prefs = DashboardPreferences.query.filter_by(user_id=current_user.id).first()
                if not prefs:
                    # Create default preferences if they don't exist
                    prefs = DashboardPreferences(user_id=current_user.id)
                    db.session.add(prefs)
                    db.session.commit()
                return {'prefs': prefs}
        except Exception as e:
            import logging
            logging.error(f"Error in inject_dashboard_prefs: {e}")
        return {'prefs': None}

    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 Not Found errors"""
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors"""
        db.session.rollback()
        app.logger.error(f'Server Error: {error}', exc_info=True)
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 Forbidden errors"""
        return render_template('errors/403.html'), 403

    return app
