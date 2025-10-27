from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # Dynamic database routing middleware
    @app.before_request
    def set_user_database():
        """Set the database URI based on current user for per-user isolation"""
        if current_user.is_authenticated:
            from app.db_manager import db_manager
            from sqlalchemy import create_engine
            from sqlalchemy.pool import StaticPool

            # Get user-specific database URI
            db_uri = db_manager.get_database_uri(current_user.id)

            # Update the app config (this is what gets read by db.get_engine())
            app.config['SQLALCHEMY_DATABASE_URI'] = db_uri

            # Get or create engine for this user's database
            if not hasattr(app, '_user_engines'):
                app._user_engines = {}

            if current_user.id not in app._user_engines:
                # Create a new engine for this user's database
                engine_options = app.config['SQLALCHEMY_ENGINE_OPTIONS'].copy()
                if db_uri.startswith('sqlite://'):
                    # SQLite doesn't support pool_size and max_overflow with StaticPool
                    engine_options.pop('pool_size', None)
                    engine_options.pop('max_overflow', None)
                    engine_options['poolclass'] = StaticPool

                app._user_engines[current_user.id] = create_engine(db_uri, **engine_options)

            # Bind the session to this user's engine
            db.session.bind = app._user_engines[current_user.id]

    # Register blueprints
    from app.routes import main, accounts, transactions, categories, backup, backup_view, settings, receipts, ai_categorizer, financial_advisor, tax_assistant, scenario_planner, investments, auth, assets
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

    # Ensure data directory exists
    import os
    data_dir = os.path.join(app.root_path, '..', 'data')
    os.makedirs(data_dir, exist_ok=True)

    # Register template filters
    from app.routes.settings import get_currency_info

    @app.template_filter('currency')
    def currency_filter(amount, show_sign=False):
        """Format amount with current currency symbol and thousands separators"""
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
        if current_user.is_authenticated:
            from app.models import DashboardPreferences
            prefs = DashboardPreferences.query.first()
            if not prefs:
                # Create default preferences if they don't exist
                prefs = DashboardPreferences()
                db.session.add(prefs)
                db.session.commit()
            return {'prefs': prefs}
        return {'prefs': None}

    return app
