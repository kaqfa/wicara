"""
Plugin Registry - Manages plugin metadata and dependencies

Tracks installed plugins, versions, dependencies, and configuration.
"""

from typing import Dict, List, Optional, Any
from packaging import version
import logging

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Registry for managing plugin metadata and dependencies.

    Maintains:
    - Installed plugins and their metadata
    - Version information
    - Dependency relationships
    - Plugin configuration
    """

    def __init__(self):
        """Initialize plugin registry."""
        self.plugins: Dict[str, Dict[str, Any]] = {}  # plugin_name -> metadata
        self._config: Dict[str, Dict[str, Any]] = {}  # plugin_name -> config

    def register(self, plugin_name: str, metadata: Dict[str, Any]) -> bool:
        """
        Register a plugin in the registry.

        Args:
            plugin_name: Unique plugin name
            metadata: Plugin metadata from get_metadata()

        Returns:
            True if registration successful, False if already registered

        Raises:
            ValueError: If required metadata fields are missing
        """
        if plugin_name in self.plugins:
            logger.warning(f"Plugin '{plugin_name}' is already registered")
            return False

        # Validate required fields
        required_fields = ['name', 'version', 'author', 'description']
        for field in required_fields:
            if field not in metadata:
                raise ValueError(f"Missing required metadata field: {field}")

        # Validate version format
        try:
            version.parse(metadata['version'])
        except version.InvalidVersion:
            raise ValueError(f"Invalid version format: {metadata['version']}")

        self.plugins[plugin_name] = {
            'name': metadata.get('name'),
            'version': metadata.get('version'),
            'author': metadata.get('author'),
            'description': metadata.get('description'),
            'depends_on': metadata.get('depends_on', []),
            'min_version': metadata.get('min_version'),
            'max_version': metadata.get('max_version'),
            'config_schema': metadata.get('config_schema'),
            'enabled': True,
        }

        logger.info(f"Registered plugin '{plugin_name}' v{metadata.get('version')}")
        return True

    def unregister(self, plugin_name: str) -> bool:
        """
        Unregister a plugin from the registry.

        Args:
            plugin_name: Name of plugin to unregister

        Returns:
            True if unregistered, False if not found
        """
        if plugin_name not in self.plugins:
            return False

        del self.plugins[plugin_name]
        if plugin_name in self._config:
            del self._config[plugin_name]

        logger.info(f"Unregistered plugin '{plugin_name}'")
        return True

    def get(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get plugin metadata."""
        return self.plugins.get(plugin_name)

    def get_all(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered plugins."""
        return self.plugins.copy()

    def exists(self, plugin_name: str) -> bool:
        """Check if plugin is registered."""
        return plugin_name in self.plugins

    def is_enabled(self, plugin_name: str) -> bool:
        """Check if plugin is enabled."""
        plugin = self.get(plugin_name)
        return plugin.get('enabled', False) if plugin else False

    def set_enabled(self, plugin_name: str, enabled: bool) -> bool:
        """Enable or disable a plugin."""
        if plugin_name not in self.plugins:
            return False

        self.plugins[plugin_name]['enabled'] = enabled
        logger.info(f"Plugin '{plugin_name}' {'enabled' if enabled else 'disabled'}")
        return True

    def validate_version(self, plugin_name: str, wicara_version: str) -> tuple[bool, Optional[str]]:
        """
        Validate plugin version compatibility with Wicara.

        Args:
            plugin_name: Plugin to validate
            wicara_version: Current Wicara version

        Returns:
            Tuple of (is_compatible, error_message)
        """
        plugin = self.get(plugin_name)
        if not plugin:
            return False, f"Plugin '{plugin_name}' not found"

        try:
            current = version.parse(wicara_version)

            if plugin.get('min_version'):
                min_v = version.parse(plugin['min_version'])
                if current < min_v:
                    return False, f"Requires Wicara >= {plugin['min_version']}"

            if plugin.get('max_version'):
                max_v = version.parse(plugin['max_version'])
                if current > max_v:
                    return False, f"Requires Wicara <= {plugin['max_version']}"

            return True, None

        except version.InvalidVersion as e:
            return False, f"Invalid version format: {str(e)}"

    def validate_dependencies(self, plugin_name: str) -> tuple[bool, List[str]]:
        """
        Validate plugin dependencies are installed.

        Args:
            plugin_name: Plugin to validate

        Returns:
            Tuple of (all_satisfied, missing_dependencies)
        """
        plugin = self.get(plugin_name)
        if not plugin:
            return False, [plugin_name]

        dependencies = plugin.get('depends_on', [])
        missing = []

        for dep in dependencies:
            if not self.exists(dep):
                missing.append(dep)

        return len(missing) == 0, missing

    def get_dependents(self, plugin_name: str) -> List[str]:
        """
        Get list of plugins that depend on given plugin.

        Args:
            plugin_name: Plugin name

        Returns:
            List of dependent plugin names
        """
        dependents = []
        for name, metadata in self.plugins.items():
            if plugin_name in metadata.get('depends_on', []):
                dependents.append(name)

        return dependents

    def set_config(self, plugin_name: str, config: Dict[str, Any]) -> bool:
        """Store plugin configuration."""
        if plugin_name not in self.plugins:
            return False

        self._config[plugin_name] = config
        return True

    def get_config(self, plugin_name: str) -> Dict[str, Any]:
        """Get plugin configuration."""
        return self._config.get(plugin_name, {})

    def to_dict(self) -> Dict[str, Any]:
        """Export registry as dict (for saving to config)."""
        return {
            'plugins': self.plugins,
            'config': self._config,
        }

    def from_dict(self, data: Dict[str, Any]):
        """Import registry from dict (for loading from config)."""
        self.plugins = data.get('plugins', {})
        self._config = data.get('config', {})

    def __repr__(self) -> str:
        enabled_count = sum(1 for p in self.plugins.values() if p.get('enabled'))
        return f"<PluginRegistry: {len(self.plugins)} plugins ({enabled_count} enabled)>"
