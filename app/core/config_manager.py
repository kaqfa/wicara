"""
WICARA Core Module: Configuration Manager
Handles loading, saving, and validation of application configuration.
"""

import json
import os
from pathlib import Path
from app.core.validators import validate_config_schema
from app.core.file_manager import create_backup


class ConfigManager:
    """Configuration manager for WICARA CMS."""

    def __init__(self, config_file='config.json', logger=None):
        """
        Initialize configuration manager.

        Args:
            config_file: Path to configuration file
            logger: Logger instance for logging
        """
        self.config_file = config_file
        self.logger = logger
        self._config = None

    def load(self, validate=True):
        """
        Load configuration from JSON file.

        Attempts to load config.json and optionally validates it against schema.
        If file doesn't exist, creates default configuration.

        Args:
            validate: Whether to validate configuration schema

        Returns:
            Configuration dictionary or None if error
        """
        try:
            # Execute before_config_load hook
            try:
                from app.plugins import get_plugin_manager
                manager = get_plugin_manager()
                if manager:
                    manager.hooks.execute('before_config_load', self.config_file)
            except Exception as e:
                if self.logger:
                    self.logger.debug(f'Plugin hook before_config_load error: {e}')

            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Validate configuration schema if requested
            if validate:
                errors = validate_config_schema(config)
                if errors:
                    error_msg = 'Configuration validation failed: ' + '; '.join(errors[:3])
                    if self.logger:
                        self.logger.error(f'Config validation errors: {errors}')
                    return None

            # Execute after_config_load hook
            try:
                from app.plugins import get_plugin_manager
                manager = get_plugin_manager()
                if manager:
                    result = manager.hooks.execute('after_config_load', config)
                    # If hook returns modified config, use it
                    if result is not None and isinstance(result, dict):
                        config = result
            except Exception as e:
                if self.logger:
                    self.logger.debug(f'Plugin hook after_config_load error: {e}')

            self._config = config
            return config

        except FileNotFoundError:
            if self.logger:
                self.logger.warning(f'Config file not found: {self.config_file}, creating default')
            return self.create_default()

        except json.JSONDecodeError as e:
            if self.logger:
                self.logger.error(f'JSON decode error: {e}')
            return None

        except PermissionError:
            if self.logger:
                self.logger.error('Permission denied reading config file')
            return None

        except Exception as e:
            if self.logger:
                self.logger.error(f'Unexpected error loading config: {e}')
            return None

    def save(self, config, validate=True):
        """
        Save configuration to JSON file with automatic backup.

        Creates a backup of the existing config file before saving new configuration.
        Optionally validates configuration before saving.

        Args:
            config: Configuration dictionary to save
            validate: Whether to validate before saving

        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate configuration schema before saving
            if validate:
                errors = validate_config_schema(config)
                if errors:
                    error_msg = 'Configuration validation failed: ' + '; '.join(errors[:3])
                    if self.logger:
                        self.logger.error(f'Config validation errors: {errors}')
                    return False

            # Execute before_config_save hook
            try:
                from app.plugins import get_plugin_manager
                manager = get_plugin_manager()
                if manager:
                    result = manager.hooks.execute('before_config_save', config)
                    # If hook returns modified config, use it
                    if result is not None and isinstance(result, dict):
                        config = result
            except Exception as e:
                if self.logger:
                    self.logger.debug(f'Plugin hook before_config_save error: {e}')

            # Create backup before saving
            create_backup(self.config_file)

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            self._config = config

            # Execute after_config_save hook
            try:
                from app.plugins import get_plugin_manager
                manager = get_plugin_manager()
                if manager:
                    manager.hooks.execute('after_config_save', config)
            except Exception as e:
                if self.logger:
                    self.logger.debug(f'Plugin hook after_config_save error: {e}')

            return True

        except PermissionError:
            if self.logger:
                self.logger.error('Permission denied saving config file')
            return False

        except json.JSONEncodeError as e:
            if self.logger:
                self.logger.error(f'JSON encode error: {e}')
            return False

        except Exception as e:
            if self.logger:
                self.logger.error(f'Unexpected error saving config: {e}')
            return False

    def create_default(self):
        """
        Create default configuration file.

        Generates a default configuration with one home page and saves it.

        Returns:
            Default configuration dictionary
        """
        default_config = {
            "admin-password": "scrypt:32768:8:1$dLQFhTGZDuFqolmd$deb5e1b924768ba1b4a37ce9c17366950c81d7eca0bf194609bac21fdd40d64921e84c5fb514c84f4f18a647c4e2d97e64f5ffd3bf4eca2a20b5dd57edf12c91",
            "sitename": "My Website",
            "description": "A simple website built with Editable Static Web",
            "keywords": ["website", "profile", "business"],
            "pages": [
                {
                    "title": "Home - My Website",
                    "template": "home.html",
                    "menu-title": "Home",
                    "url": "/",
                    "seo-description": "Welcome to my website",
                    "seo-keywords": ["home", "welcome"],
                    "fields": [
                        {
                            "name": "hero-title",
                            "type": "text",
                            "label": "Hero Title",
                            "value": "Welcome to Our Website"
                        },
                        {
                            "name": "hero-description",
                            "type": "textarea",
                            "label": "Hero Description",
                            "value": "We provide amazing services for your business"
                        }
                    ]
                }
            ],
            "footer": {
                "content": [
                    "Copyright © 2025 My Website. All rights reserved."
                ]
            }
        }

        if self.save(default_config, validate=False):
            return default_config
        return None

    def get(self, *keys, default=None):
        """
        Get configuration value by dot-notation path.

        Args:
            *keys: Keys to traverse in configuration
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        if self._config is None:
            self.load(validate=False)

        value = self._config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default

        return value if value is not None else default

    def get_page_by_url(self, url):
        """
        Get page configuration by URL.

        Args:
            url: Page URL to search for

        Returns:
            Page configuration dictionary or None
        """
        if self._config is None:
            self.load(validate=False)

        if self._config is None:
            return None

        for page in self._config.get('pages', []):
            if page.get('url') == url:
                return page

        return None

    @property
    def config(self):
        """Get current configuration dictionary."""
        return self._config

    @property
    def is_loaded(self):
        """Check if configuration is loaded."""
        return self._config is not None


def load_config(config_file='config.json', validate=True, logger=None):
    """
    Load configuration from JSON file (functional interface).

    This is a convenience function that creates a ConfigManager instance
    and loads the configuration.

    Args:
        config_file: Path to config.json file
        validate: Whether to validate configuration schema
        logger: Logger instance for logging

    Returns:
        Configuration dictionary or None if error
    """
    manager = ConfigManager(config_file, logger)
    return manager.load(validate=validate)


def save_config(config, config_file='config.json', validate=True, logger=None):
    """
    Save configuration to JSON file (functional interface).

    Args:
        config: Configuration dictionary to save
        config_file: Path to config.json file
        validate: Whether to validate before saving
        logger: Logger instance for logging

    Returns:
        True if successful, False otherwise
    """
    manager = ConfigManager(config_file, logger)
    return manager.save(config, validate=validate)
