"""
Logging configuration for WICARA CMS.
Provides structured logging across the application.
"""

import logging
import logging.handlers
import os
from pathlib import Path


def setup_logger(app):
    """
    Setup logging configuration for the Flask application.

    Args:
        app: Flask application instance
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(app.config['LOG_FILE'])
    if log_dir and not os.path.exists(log_dir):
        Path(log_dir).mkdir(parents=True, exist_ok=True)

    # Remove default Flask logger handlers
    app.logger.handlers.clear()

    # Get log level from config
    log_level = getattr(logging, app.config['LOG_LEVEL'].upper(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler - logs all levels
    if app.config['LOG_FILE']:
        file_handler = logging.handlers.RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)

    # Console handler - logs all levels
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    app.logger.addHandler(console_handler)

    # Set logger level
    app.logger.setLevel(log_level)

    # Log startup message
    app.logger.info('===== WICARA CMS Application Started =====')
    app.logger.info(f'Environment: {os.environ.get("FLASK_ENV", "development")}')
    app.logger.info(f'Debug: {app.debug}')
    app.logger.info(f'Log Level: {app.config["LOG_LEVEL"]}')
