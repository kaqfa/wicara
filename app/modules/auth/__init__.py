"""
WICARA Auth Module
Handles authentication and authorization for admin panel.
"""

from app.modules.auth.routes import auth_bp
from app.modules.auth.utils import login_required

__all__ = ['auth_bp', 'login_required']
