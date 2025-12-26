"""
BasePlugin - Abstract base class for all Wicara plugins

All plugins must inherit from BasePlugin and implement required methods.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class BasePlugin(ABC):
    """
    Abstract base class for Wicara plugins.

    All plugins must:
    1. Inherit from BasePlugin
    2. Implement get_metadata() and init() methods
    3. Define supported hook types in get_hooks()

    Example:
        class MyPlugin(BasePlugin):
            def get_metadata(self):
                return {
                    'name': 'My Plugin',
                    'version': '1.0.0',
                    'author': 'John Doe',
                    'description': 'My custom plugin'
                }

            def init(self, app):
                # Initialize plugin
                pass

            def get_hooks(self):
                return {
                    'before_page_render': self.my_hook_handler
                }
    """

    def __init__(self):
        """Initialize base plugin."""
        self.app = None
        self.manager = None
        self._enabled = True
        self._config = {}

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """
        Return plugin metadata.

        Required fields:
        - name: str - Plugin name
        - version: str - Semantic version (e.g., "1.0.0")
        - author: str - Plugin author
        - description: str - Plugin description

        Optional fields:
        - depends_on: List[str] - Plugin dependencies
        - min_version: str - Minimum Wicara version required
        - max_version: str - Maximum Wicara version supported
        - config_schema: Dict - Configuration schema for validation

        Returns:
            Dict with plugin metadata
        """
        pass

    @abstractmethod
    def init(self, app):
        """
        Initialize plugin with Flask app.

        Called when plugin is loaded. Use this to:
        - Register routes (if admin page plugin)
        - Register command handlers (if CLI plugin)
        - Initialize plugin state
        - Perform startup tasks

        Args:
            app: Flask application instance
        """
        pass

    def get_hooks(self) -> Dict[str, callable]:
        """
        Register plugin hooks.

        Return dict mapping hook names to handler functions.
        Handlers can have optional priority (default: 10).

        Example:
            return {
                'before_page_render': {
                    'handler': self.on_page_render,
                    'priority': 20  # Higher priority = runs earlier
                },
                'after_config_save': self.on_config_saved  # Default priority: 10
            }

        Returns:
            Dict[str, callable] or Dict[str, Dict] - Hook definitions
        """
        return {}

    def get_config_schema(self) -> Optional[Dict[str, Any]]:
        """
        Return JSON schema for plugin configuration validation.

        Used to validate and store plugin-specific settings.

        Returns:
            JSON schema dict or None
        """
        return None

    def validate_dependencies(self, installed_plugins: List[str]) -> bool:
        """
        Validate that required dependencies are installed.

        Args:
            installed_plugins: List of installed plugin names

        Returns:
            True if all dependencies are satisfied, False otherwise
        """
        metadata = self.get_metadata()
        dependencies = metadata.get('depends_on', [])

        for dep in dependencies:
            if dep not in installed_plugins:
                return False

        return True

    def enable(self):
        """Enable this plugin."""
        self._enabled = True

    def disable(self):
        """Disable this plugin."""
        self._enabled = False

    def is_enabled(self) -> bool:
        """Check if plugin is enabled."""
        return self._enabled

    def set_config(self, config: Dict[str, Any]):
        """Set plugin configuration."""
        self._config = config

    def get_config(self) -> Dict[str, Any]:
        """Get plugin configuration."""
        return self._config

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get specific config value."""
        return self._config.get(key, default)

    def shutdown(self):
        """
        Cleanup when plugin is unloaded.

        Override to perform cleanup tasks (close connections, etc).
        """
        pass

    def __repr__(self) -> str:
        metadata = self.get_metadata()
        return f"<{metadata.get('name', 'Unknown')} v{metadata.get('version', '?')}>"
