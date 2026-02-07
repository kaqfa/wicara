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
from app.blueprints.import_export import import_export_bp
from app.core import ensure_directories
from app.cache.utils import CacheFactory, CacheService
from app.modules.admin.cache_routes import cache_bp, set_cache_service
from app.modules.admin.plugin_routes import plugin_bp
from app.plugins import init_plugins, get_plugin_manager


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
    # Set template_folder to parent directory (templates/ is outside app/)
    template_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
    static_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    app = Flask(__name__, instance_relative_config=False,
                template_folder=template_folder, static_folder=static_folder)

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

    # Initialize plugin system
    app.logger.info('Initializing plugin system...')
    try:
        plugin_manager = init_plugins(app, plugin_dir='app/plugins/installed')

        # Load all enabled plugins
        loaded_plugins = plugin_manager.load_all()
        app.logger.info(f'Loaded {len(loaded_plugins)} plugins')

        # Register plugin-defined template filters
        _register_plugin_template_filters(app, plugin_manager)

        # Register plugin-defined template globals
        _register_plugin_template_globals(app, plugin_manager)

        app.logger.info('Plugin system initialized successfully')
    except Exception as e:
        app.logger.warning(f'Plugin system initialization failed: {str(e)}')
        # Plugin system failure should not prevent app from starting

    # Register blueprints
    app.logger.info('Registering blueprints...')
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(import_export_bp)
    app.register_blueprint(public_bp)
    if app.cache_service:
        app.register_blueprint(cache_bp)
    app.register_blueprint(plugin_bp)
    app.logger.info(f'Registered {len(app.blueprints)} blueprints')

    # Register error handlers
    app.logger.info('Registering error handlers...')
    register_error_handlers(app)

    app.logger.info('===== Application Factory Complete =====')

    return app


def _register_plugin_template_filters(app, plugin_manager):
    """
    Register template filters provided by plugins.

    Args:
        app: Flask application instance
        plugin_manager: PluginManager instance
    """
    try:
        # Execute register_template_filters hook to collect filters from all plugins
        filters_list = plugin_manager.hooks.execute_multiple('register_template_filters')

        # Merge all filter dictionaries
        for filters in filters_list:
            if filters and isinstance(filters, dict):
                for filter_name, filter_func in filters.items():
                    if callable(filter_func):
                        app.jinja_env.filters[filter_name] = filter_func
                        app.logger.debug(f"Registered template filter: {filter_name}")
    except Exception as e:
        app.logger.error(f'Error registering plugin template filters: {str(e)}')


def _register_plugin_template_globals(app, plugin_manager):
    """
    Register template global variables provided by plugins.

    Args:
        app: Flask application instance
        plugin_manager: PluginManager instance
    """
    try:
        # Execute register_template_globals hook to collect globals from all plugins
        globals_list = plugin_manager.hooks.execute_multiple('register_template_globals')

        # Merge all global dictionaries
        for globals_dict in globals_list:
            if globals_dict and isinstance(globals_dict, dict):
                for global_name, global_value in globals_dict.items():
                    app.jinja_env.globals[global_name] = global_value
                    app.logger.debug(f"Registered template global: {global_name}")
    except Exception as e:
        app.logger.error(f'Error registering plugin template globals: {str(e)}')
