"""
Plugin Manager - PLG-01, PLG-04

Main plugin orchestration system.
Handles plugin discovery, loading, validation, and lifecycle management.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import importlib.util
import logging

from .base import BasePlugin
from .hooks import HookDispatcher, CORE_HOOKS
from .registry import PluginRegistry

logger = logging.getLogger(__name__)


class PluginManager:
    """
    Main plugin manager for Wicara.

    Responsibilities:
    - Discover plugins from filesystem
    - Load and initialize plugins
    - Validate dependencies and versions
    - Manage plugin lifecycle (enable, disable, uninstall)
    - Provide plugin API to plugins
    - Manage hook execution
    """

    def __init__(self):
        """Initialize plugin manager."""
        self.app = None
        self.plugin_dir = None
        self.plugins: Dict[str, BasePlugin] = {}
        self.registry = PluginRegistry()
        self.hooks = HookDispatcher()
        self.wicara_version = "1.0.0"

    def init_app(self, app, plugin_dir: Optional[str] = None):
        """
        Initialize plugin manager with Flask app.

        Args:
            app: Flask application instance
            plugin_dir: Path to plugins directory (default: app/plugins)
        """
        self.app = app
        self.plugin_dir = plugin_dir or os.path.join(
            os.path.dirname(__file__), 'installed'
        )

        # Create plugins directory if it doesn't exist
        Path(self.plugin_dir).mkdir(parents=True, exist_ok=True)

        logger.info(f"Plugin manager initialized with plugin_dir: {self.plugin_dir}")

    def discover(self) -> List[str]:
        """
        Discover available plugins in plugin directory.

        Returns:
            List of plugin package names found
        """
        if not self.plugin_dir:
            logger.warning("Plugin manager not initialized with app")
            return []

        plugins = []
        try:
            for item in os.listdir(self.plugin_dir):
                path = os.path.join(self.plugin_dir, item)
                if os.path.isdir(path) and not item.startswith('_'):
                    # Check if plugin has __init__.py
                    if os.path.exists(os.path.join(path, '__init__.py')):
                        plugins.append(item)
                        logger.debug(f"Discovered plugin: {item}")
        except FileNotFoundError:
            logger.warning(f"Plugin directory not found: {self.plugin_dir}")

        return plugins

    def load(self, plugin_name: str) -> Optional[BasePlugin]:
        """
        Load and initialize a plugin.

        Args:
            plugin_name: Name of plugin to load (package name)

        Returns:
            BasePlugin instance or None if load failed

        Raises:
            ValueError: If plugin doesn't inherit from BasePlugin
            ImportError: If plugin package cannot be imported
        """
        if not self.plugin_dir:
            logger.error("Plugin manager not initialized")
            return None

        if plugin_name in self.plugins:
            logger.warning(f"Plugin '{plugin_name}' is already loaded")
            return self.plugins[plugin_name]

        # Add plugin directory to sys.path temporarily
        plugin_path = os.path.join(self.plugin_dir, plugin_name)
        if plugin_path not in sys.path:
            sys.path.insert(0, self.plugin_dir)

        try:
            # Import plugin module
            plugin_module = importlib.import_module(plugin_name)

            # Find plugin class (first BasePlugin subclass)
            plugin_class = None
            for attr_name in dir(plugin_module):
                attr = getattr(plugin_module, attr_name)
                if (isinstance(attr, type) and
                    issubclass(attr, BasePlugin) and
                    attr is not BasePlugin):
                    plugin_class = attr
                    break

            if not plugin_class:
                raise ValueError(f"Plugin '{plugin_name}' has no BasePlugin subclass")

            # Create plugin instance
            plugin = plugin_class()
            plugin.manager = self
            plugin.app = self.app

            # Register plugin
            metadata = plugin.get_metadata()
            self.registry.register(plugin_name, metadata)

            # Validate version compatibility
            is_compatible, error = self.registry.validate_version(
                plugin_name, self.wicara_version
            )
            if not is_compatible:
                logger.error(f"Plugin '{plugin_name}' version incompatible: {error}")
                return None

            # Validate dependencies
            deps_ok, missing = self.registry.validate_dependencies(plugin_name)
            if not deps_ok:
                logger.error(f"Plugin '{plugin_name}' missing dependencies: {missing}")
                return None

            # Initialize plugin
            if self.app:
                plugin.init(self.app)

            # Register hooks
            hooks = plugin.get_hooks()
            for hook_name, hook_def in hooks.items():
                if isinstance(hook_def, dict):
                    # Hook with priority
                    handler = hook_def.get('handler')
                    priority = hook_def.get('priority', 10)
                else:
                    # Hook without priority
                    handler = hook_def
                    priority = 10

                self.hooks.register(
                    hook_name,
                    handler,
                    priority=priority,
                    plugin_name=plugin_name
                )

            self.plugins[plugin_name] = plugin
            logger.info(f"Loaded plugin: {plugin_name} v{metadata.get('version')}")
            return plugin

        except Exception as e:
            logger.error(f"Failed to load plugin '{plugin_name}': {e}", exc_info=True)
            return None

    def load_all(self) -> Dict[str, BasePlugin]:
        """
        Discover and load all available plugins.

        Returns:
            Dict of loaded plugins {name: instance}
        """
        if not self.plugin_dir:
            logger.error("Plugin manager not initialized")
            return {}

        discovered = self.discover()
        loaded = {}

        for plugin_name in discovered:
            plugin = self.load(plugin_name)
            if plugin:
                loaded[plugin_name] = plugin

        logger.info(f"Loaded {len(loaded)}/{len(discovered)} plugins")
        return loaded

    def unload(self, plugin_name: str) -> bool:
        """
        Unload a plugin.

        Args:
            plugin_name: Name of plugin to unload

        Returns:
            True if unloaded successfully
        """
        if plugin_name not in self.plugins:
            logger.warning(f"Plugin '{plugin_name}' is not loaded")
            return False

        plugin = self.plugins[plugin_name]

        # Check for dependents
        dependents = self.registry.get_dependents(plugin_name)
        if dependents:
            logger.error(f"Cannot unload plugin '{plugin_name}': required by {dependents}")
            return False

        # Shutdown plugin
        try:
            plugin.shutdown()
        except Exception as e:
            logger.error(f"Error shutting down plugin '{plugin_name}': {e}")

        # Remove from registry
        self.registry.unregister(plugin_name)

        # Remove plugin from dict
        del self.plugins[plugin_name]

        logger.info(f"Unloaded plugin: {plugin_name}")
        return True

    def enable(self, plugin_name: str) -> bool:
        """Enable a plugin."""
        if plugin_name not in self.plugins:
            return False

        self.plugins[plugin_name].enable()
        self.registry.set_enabled(plugin_name, True)
        logger.info(f"Enabled plugin: {plugin_name}")
        return True

    def disable(self, plugin_name: str) -> bool:
        """Disable a plugin."""
        if plugin_name not in self.plugins:
            return False

        self.plugins[plugin_name].disable()
        self.registry.set_enabled(plugin_name, False)
        logger.info(f"Disabled plugin: {plugin_name}")
        return True

    def get(self, plugin_name: str) -> Optional[BasePlugin]:
        """Get loaded plugin instance."""
        return self.plugins.get(plugin_name)

    def get_all(self) -> Dict[str, BasePlugin]:
        """Get all loaded plugins."""
        return self.plugins.copy()

    def get_enabled(self) -> Dict[str, BasePlugin]:
        """Get all enabled plugins."""
        return {
            name: plugin for name, plugin in self.plugins.items()
            if plugin.is_enabled()
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get plugin manager statistics."""
        enabled_count = sum(1 for p in self.plugins.values() if p.is_enabled())
        total_hooks = len(self.registry.plugins)
        total_handlers = sum(len(handlers) for handlers in self.hooks.hooks.values())

        return {
            'total_plugins': len(self.plugins),
            'enabled_plugins': enabled_count,
            'disabled_plugins': len(self.plugins) - enabled_count,
            'total_hooks': total_hooks,
            'total_handlers': total_handlers,
            'plugin_dir': self.plugin_dir,
        }

    def __repr__(self) -> str:
        enabled = sum(1 for p in self.plugins.values() if p.is_enabled())
        return f"<PluginManager: {len(self.plugins)} plugins ({enabled} enabled)>"
