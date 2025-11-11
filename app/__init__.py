"""
WICARA CMS Application Package.
Flask application factory and initialization.
"""

from flask import Flask
from app.config import get_config
from app.logger import setup_logger
from app.errors import register_error_handlers
from app.modules import auth_bp, admin_bp, public_bp
from app.core import ensure_directories


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

    # Register blueprints
    app.logger.info('Registering blueprints...')
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(public_bp)
    app.logger.info(f'Registered {len(app.blueprints)} blueprints')

    # Register error handlers
    app.logger.info('Registering error handlers...')
    register_error_handlers(app)

    app.logger.info('===== Application Factory Complete =====')

    return app
