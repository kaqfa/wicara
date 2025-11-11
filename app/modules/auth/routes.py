"""
Authentication routes for WICARA CMS admin panel.
Handles login and logout operations.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from werkzeug.security import check_password_hash
from datetime import datetime
from app.core import load_config

auth_bp = Blueprint('auth', __name__, url_prefix='/admin')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Admin login route.

    GET: Display login form
    POST: Process login with password
    """
    if request.method == 'POST':
        password = request.form.get('password')
        config = load_config(current_app.config['CONFIG_FILE'], logger=current_app.logger)

        if config and check_password_hash(config['admin-password'], password):
            session['admin_logged_in'] = True
            session['login_time'] = datetime.now().timestamp()
            flash('Login successful', 'success')
            current_app.logger.info('Admin login successful')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid password', 'error')
            current_app.logger.warning('Failed admin login attempt')

    return render_template('admin/login.html')


@auth_bp.route('/logout')
def logout():
    """
    Admin logout route.

    Clears session and redirects to login page.
    """
    session.clear()
    flash('Logged out successfully', 'success')
    current_app.logger.info('Admin logged out')
    return redirect(url_for('auth.login'))
