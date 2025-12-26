"""
Plugin Types - PLG-03

Different plugin type base classes and interfaces.
"""

from abc import abstractmethod
from typing import Dict, Any, List, Callable, Type
from .base import BasePlugin


# ============================================================================
# FIELD TYPE PLUGIN
# ============================================================================

class FieldTypePlugin(BasePlugin):
    """
    Base class for custom field type plugins.

    Allows plugins to register custom field types beyond text, textarea, image.

    Example:
        class RichTextFieldPlugin(FieldTypePlugin):
            def get_field_types(self):
                return {
                    'rich_text': {
                        'label': 'Rich Text Editor',
                        'input_template': 'fields/rich_text.html',
                        'validator': self.validate_rich_text,
                        'display_template': 'fields/rich_text_display.html'
                    }
                }
    """

    @abstractmethod
    def get_field_types(self) -> Dict[str, Dict[str, Any]]:
        """
        Return dictionary of custom field types.

        Each field type definition should include:
        - label: Display name for the field type
        - input_template: Path to form input template
        - validator: Function to validate field value
        - display_template: Path to template for displaying value
        - default_value: Optional default value
        - config_schema: Optional schema for field-specific config

        Returns:
            Dict mapping field type names to their definitions
        """
        pass

    def get_hooks(self) -> Dict[str, Callable]:
        """Register field type hooks."""
        return {
            'register_field_types': {
                'handler': self.get_field_types,
                'priority': 20
            }
        }


# ============================================================================
# ADMIN PAGE PLUGIN
# ============================================================================

class AdminPagePlugin(BasePlugin):
    """
    Base class for plugins that add custom admin pages.

    Allows plugins to add new sections to the admin panel.

    Example:
        class AnalyticsPlugin(AdminPagePlugin):
            def register_admin_pages(self):
                return {
                    'analytics': {
                        'label': 'Analytics',
                        'route': '/admin/analytics',
                        'template': 'admin/analytics.html',
                        'icon': 'chart-bar',
                        'permission': 'admin'
                    }
                }

            def init(self, app):
                # Register route
                @app.route('/admin/analytics')
                def analytics():
                    return render_template('admin/analytics.html')
    """

    @abstractmethod
    def register_admin_pages(self) -> Dict[str, Dict[str, Any]]:
        """
        Return dictionary of custom admin pages.

        Each page definition should include:
        - label: Display name in menu
        - route: URL path for the page
        - template: Template file to render
        - icon: Icon name (for sidebar)
        - permission: Required permission level
        - order: Menu order (optional)

        Returns:
            Dict mapping page IDs to their definitions
        """
        pass

    def get_hooks(self) -> Dict[str, Callable]:
        """Register admin menu hooks."""
        return {
            'register_admin_menu': {
                'handler': self.register_admin_pages,
                'priority': 15
            }
        }


# ============================================================================
# TEMPLATE FILTER PLUGIN
# ============================================================================

class TemplateFilterPlugin(BasePlugin):
    """
    Base class for plugins that add custom Jinja2 filters and globals.

    Allows plugins to register custom template functions and variables.

    Example:
        class TextFiltersPlugin(TemplateFilterPlugin):
            def get_template_filters(self):
                return {
                    'capitalize_all': self.capitalize_all,
                    'word_count': self.word_count,
                    'markdown': self.to_markdown
                }

            def capitalize_all(self, text):
                return ' '.join(word.capitalize() for word in text.split())

            def word_count(self, text):
                return len(text.split())

            def to_markdown(self, text):
                # Convert markdown to HTML
                pass
    """

    @abstractmethod
    def get_template_filters(self) -> Dict[str, Callable]:
        """
        Return dictionary of custom Jinja2 filters.

        Each filter function should accept input and return modified output.

        Returns:
            Dict mapping filter names to functions
        """
        pass

    def get_template_globals(self) -> Dict[str, Any]:
        """
        Return dictionary of global template variables.

        Optional method for providing global template variables.

        Returns:
            Dict of global variables
        """
        return {}

    def get_hooks(self) -> Dict[str, Callable]:
        """Register template hooks."""
        hooks = {
            'register_template_filters': {
                'handler': self.get_template_filters,
                'priority': 20
            }
        }

        if self.get_template_globals():
            hooks['register_template_globals'] = {
                'handler': self.get_template_globals,
                'priority': 20
            }

        return hooks


# ============================================================================
# CLI COMMAND PLUGIN
# ============================================================================

class CLICommandPlugin(BasePlugin):
    """
    Base class for plugins that add custom CLI commands.

    Allows plugins to register custom management commands.

    Example:
        class BackupPlugin(CLICommandPlugin):
            def register_cli_commands(self):
                return [
                    {
                        'name': 'backup-full',
                        'handler': self.backup_full,
                        'help': 'Create full backup',
                        'args': []
                    },
                    {
                        'name': 'restore-backup',
                        'handler': self.restore_backup,
                        'help': 'Restore from backup',
                        'args': [
                            {'name': 'backup_path', 'help': 'Path to backup file'}
                        ]
                    }
                ]
    """

    @abstractmethod
    def register_cli_commands(self) -> List[Dict[str, Any]]:
        """
        Return list of custom CLI commands.

        Each command definition should include:
        - name: Command name (e.g., 'my-command')
        - handler: Function to execute when command runs
        - help: Help text for command
        - args: List of argument definitions (optional)

        Argument definition:
        {
            'name': 'arg_name',
            'help': 'Argument description',
            'type': 'str' | 'int',
            'required': True/False
        }

        Returns:
            List of command definitions
        """
        pass

    def get_hooks(self) -> Dict[str, Callable]:
        """Register CLI command hooks."""
        return {
            'register_cli_commands': {
                'handler': self.register_cli_commands,
                'priority': 15
            }
        }


# ============================================================================
# CACHE BACKEND PLUGIN
# ============================================================================

class CacheBackendPlugin(BasePlugin):
    """
    Base class for plugins that add custom cache backends.

    Allows plugins to register custom caching strategies.

    Example:
        class MemcachedCachePlugin(CacheBackendPlugin):
            def get_cache_backend(self):
                return {
                    'name': 'memcached',
                    'class': MemcachedBackend,
                    'description': 'Memcached distributed cache'
                }
    """

    @abstractmethod
    def get_cache_backend(self) -> Dict[str, Any]:
        """
        Return custom cache backend definition.

        Definition should include:
        - name: Backend name (for CACHE_BACKEND setting)
        - class: Cache backend class (must inherit from base cache class)
        - description: Description of backend
        - config_schema: Optional configuration schema

        Returns:
            Dict with cache backend definition
        """
        pass

    def get_hooks(self) -> Dict[str, Callable]:
        """Register cache backend hooks."""
        return {
            'register_cache_backends': {
                'handler': self.get_cache_backend,
                'priority': 20
            }
        }


# ============================================================================
# EVENT PLUGIN
# ============================================================================

class EventPlugin(BasePlugin):
    """
    Base class for plugins that listen to events in Wicara.

    Useful for plugins that need to react to certain system events.

    Example:
        class EmailNotificationPlugin(EventPlugin):
            def on_config_saved(self, config):
                # Send email notification
                self.send_email(f"Config saved at {datetime.now()}")

            def get_hooks(self):
                return {
                    'after_config_save': {
                        'handler': self.on_config_saved,
                        'priority': 10
                    },
                    'after_import': {
                        'handler': self.on_import_complete,
                        'priority': 10
                    }
                }
    """

    # This is a flexible plugin type that can listen to any hook
    # Subclasses should override get_hooks() to register their event handlers

    def get_hooks(self) -> Dict[str, Callable]:
        """Override to register event handlers."""
        return {}
