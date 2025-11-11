"""
WICARA Modules Package
Contains feature modules with blueprints and logic.
"""

from app.modules.auth import auth_bp, login_required
from app.modules.admin import admin_bp
from app.modules.public import public_bp

__all__ = ['auth_bp', 'admin_bp', 'public_bp', 'login_required']
