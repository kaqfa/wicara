"""
Authentication utilities for WICARA CMS.
Provides decorators and helpers for authentication.
"""

from flask import session, redirect, url_for
from functools import wraps


def login_required(f):
    """
    Decorator to check if user is logged in.

    Redirects to login page if user is not authenticated.

    Args:
        f: Function to decorate

    Returns:
        Decorated function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def is_admin_logged_in():
    """
    Check if admin user is currently logged in.

    Returns:
        True if logged in, False otherwise
    """
    return session.get('admin_logged_in', False)


def get_login_time():
    """
    Get the timestamp when user logged in.

    Returns:
        Login timestamp or None
    """
    return session.get('login_time')
