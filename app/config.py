"""
Configuration management for WICARA CMS.
Supports environment-based configuration for different environments.
"""

import os
from pathlib import Path


class Config:
    """Base configuration class with common settings."""

    # Application
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False

    # Session
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour in seconds
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # File Upload
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB
    UPLOAD_FOLDER = os.path.join('static', 'images', 'uploads')
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}

    # Configuration File
    CONFIG_FILE = 'config.json'

    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/wicara.log')

    # Application paths
    BASE_DIR = Path(__file__).parent.parent
    TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
    STATIC_DIR = os.path.join(BASE_DIR, 'static')


class DevelopmentConfig(Config):
    """Development environment configuration."""

    DEBUG = True
    SESSION_COOKIE_SECURE = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production environment configuration."""

    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True

    # Production uses explicit environment variables
    # SECRET_KEY validation happens in get_config() function


class TestingConfig(Config):
    """Testing environment configuration."""

    DEBUG = True
    TESTING = True
    SESSION_COOKIE_SECURE = False
    SECRET_KEY = 'test-secret-key'
    CONFIG_FILE = 'config.test.json'


def get_config():
    """
    Get configuration based on environment.

    Environment variable: FLASK_ENV
    - 'production': ProductionConfig
    - 'testing': TestingConfig
    - 'development' or default: DevelopmentConfig
    """
    env = os.environ.get('FLASK_ENV', 'development')

    config_map = {
        'production': ProductionConfig,
        'testing': TestingConfig,
        'development': DevelopmentConfig,
    }

    config_class = config_map.get(env, DevelopmentConfig)

    # Validate production configuration
    if env == 'production':
        if not os.environ.get('SECRET_KEY'):
            raise ValueError("SECRET_KEY environment variable must be set in production")

    return config_class
