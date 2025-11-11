"""
Blueprints package for WICARA CMS.
Contains route blueprints for different parts of the application.
"""

from app.blueprints.public import public_bp
from app.blueprints.admin import admin_bp

__all__ = ['public_bp', 'admin_bp']
