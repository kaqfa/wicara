"""
WICARA CMS Application Package.
Flask application factory and initialization.
"""

import os
from flask import Flask
from app.config import get_config
from app.logger import setup_logger
from app.errors import register_error_handlers
from app.modules import auth_bp, admin_bp, public_bp
from app.core import ensure_directories
from app.cache.utils import CacheFactory, CacheService
from app.modules.admin.cache_routes import cache_bp, set_cache_service


def create_app(config=None):
    """
    Application Factory Pattern - Creates and configures Flask application instance.

    This function implements the Flask Application Factory pattern, which allows:
    - Creating multiple app instances with different configurations
    - Better testability and modularity
    - Proper dependency management
    - Environment-based configuration

    Args:
        config: Configuration class (optional). If not provided, uses environment-based config.

    Returns:
        Configured Flask application instance
    """
    # Create Flask app instance
    app = Flask(__name__, instance_relative_config=False)

    # Load configuration
    if config is None:
        config = get_config()

    app.config.from_object(config)

    # Setup logging
    setup_logger(app)
    app.logger.info('Application factory initialized')

    # Ensure required directories exist
    ensure_directories(app)

    # Initialize caching system
    app.logger.info('Initializing cache system...')
    cache_backend_type = os.environ.get('CACHE_BACKEND', 'memory').lower()
    try:
        cache_manager = CacheFactory.create_manager(cache_backend_type)
        cache_service = CacheService(cache_manager)

        # Enable cache components
        cache_service.enable_template_caching(default_ttl=3600)
        cache_service.enable_response_caching(default_ttl=3600, max_age=3600)
        cache_service.enable_config_caching(cache_ttl=300)

        # Store cache service in app context
        app.cache_service = cache_service
        set_cache_service(cache_service)

        app.logger.info(f'Cache system initialized with backend: {cache_backend_type}')
    except Exception as e:
        app.logger.warning(f'Cache system initialization failed: {str(e)}')
        app.cache_service = None

    # Register blueprints
    app.logger.info('Registering blueprints...')
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(public_bp)
    if app.cache_service:
        app.register_blueprint(cache_bp)
    app.logger.info(f'Registered {len(app.blueprints)} blueprints')

    # Register error handlers
    app.logger.info('Registering error handlers...')
    register_error_handlers(app)

    app.logger.info('===== Application Factory Complete =====')

    return app
