from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app import db
from werkzeug.exceptions import BadRequest

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')

        # Validation
        errors = []

        if not username:
            errors.append('Username is required')
        elif len(username) < 3:
            errors.append('Username must be at least 3 characters long')
        elif User.query.filter_by(username=username).first():
            errors.append('Username already exists')

        if not email:
            errors.append('Email is required')
        elif '@' not in email:
            errors.append('Invalid email address')
        elif User.query.filter_by(email=email).first():
            errors.append('Email already registered')

        if not password:
            errors.append('Password is required')
        elif len(password) < 6:
            errors.append('Password must be at least 6 characters long')

        if password != password_confirm:
            errors.append('Passwords do not match')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/register.html')

        # Create new user
        try:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            flash(f'Account created successfully! Welcome {username}. Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating account: {str(e)}', 'danger')
            return render_template('auth/register.html')

    return render_template('auth/register.html')


@bp.route('/login', methods=['GET', 'POST'])
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

        # Redirect to next page or dashboard
        next_page = request.args.get('next')
        if not next_page or url_has_allowed_host_and_scheme(next_page):
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


def url_has_allowed_host_and_scheme(url):
    """Check if URL is safe for redirect"""
    from urllib.parse import urlparse
    parsed_url = urlparse(url)
    return parsed_url.scheme in ('', 'http', 'https') and parsed_url.netloc == ''
