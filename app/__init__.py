"""
WICARA CMS Application Package.
Flask application factory and initialization.
"""

from flask import Flask
from app.config import get_config
from app.logger import setup_logger
from app.errors import register_error_handlers
from app.blueprints import public_bp, admin_bp


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

    # Register blueprints
    app.logger.info('Registering blueprints...')
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)
    app.logger.info(f'Registered {len(app.blueprints)} blueprints')

    # Register error handlers
    app.logger.info('Registering error handlers...')
    register_error_handlers(app)

    # Create upload directory if it doesn't exist
    import os
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(app.config['LOG_FILE'])
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    app.logger.info('===== Application Factory Complete =====')

    return app
