from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse, urljoin
from app.models import User
from app import db, db_manager, limiter

bp = Blueprint('auth', __name__, url_prefix='/auth')

def is_safe_url(target):
    """Check if a redirect URL is safe (same domain)"""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

def validate_password_strength(password):
    """Validate password meets security requirements"""
    import re
    errors = []

    if len(password) < 12:
        errors.append('Password must be at least 12 characters long')
    if not re.search(r'[A-Z]', password):
        errors.append('Password must contain at least one uppercase letter')
    if not re.search(r'[a-z]', password):
        errors.append('Password must contain at least one lowercase letter')
    if not re.search(r'\d', password):
        errors.append('Password must contain at least one number')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append('Password must contain at least one special character')

    return errors

def validate_email(email):
    """Validate email format"""
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

def validate_registration(username, email, password, password_confirm):
    """Validates user registration form data."""
    errors = []
    if not username:
        errors.append('Username is required')
    elif len(username) < 3:
        errors.append('Username must be at least 3 characters long')
    elif User.query.filter_by(username=username).first():
        errors.append('Username already exists')

    if not email:
        errors.append('Email is required')
    elif not validate_email(email):
        errors.append('Invalid email address format')
    elif User.query.filter_by(email=email).first():
        errors.append('Email already registered')

    if not password:
        errors.append('Password is required')
    else:
        # Validate password strength
        password_errors = validate_password_strength(password)
        errors.extend(password_errors)

    if password != password_confirm:
        errors.append('Passwords do not match')

    return errors

@bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("20 per hour")
def register():
    """User registration page."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')

        errors = validate_registration(username, email, password, password_confirm)

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/register.html')

        try:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            if not current_app.db_manager.initialize_user_data(user.id):
                db.session.delete(user)
                db.session.commit()
                flash('Error creating user database. Please try again.', 'danger')
                return render_template('auth/register.html')

            flash(f'Account created successfully! Welcome {username}. Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Registration error for {username}: {str(e)}', exc_info=True)
            flash('An error occurred during registration. Please try again later.', 'danger')
            return render_template('auth/register.html')

    return render_template('auth/register.html')

@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("100 per hour")
def login():
    """User login page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember_me = request.form.get('remember_me') == 'on'

        errors = []

        if not username:
            errors.append('Username is required')
        if not password:
            errors.append('Password is required')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/login.html')

        # Check credentials
        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash('Invalid username or password', 'danger')
            return render_template('auth/login.html')

        if not user.is_active:
            flash('This account has been deactivated', 'danger')
            return render_template('auth/login.html')

        # Log in user
        login_user(user, remember=remember_me)
        flash(f'Welcome back, {user.username}!', 'success')

        # Redirect to next page or dashboard (with open redirect protection)
        next_page = request.args.get('next')
        if not next_page or not is_safe_url(next_page):
            next_page = url_for('main.index')

        return redirect(next_page)

    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    """Log out user"""
    username = current_user.username
    logout_user()
    flash(f'You have been logged out. Goodbye, {username}!', 'info')
    return redirect(url_for('auth.login'))