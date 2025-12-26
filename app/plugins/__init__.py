"""
Wicara Plugin System - PLG-01, PLG-02

Extensibility ecosystem for Wicara CMS.
Provides plugin architecture, hook system, and plugin management.

Key Components:
- PluginManager: Plugin discovery, loading, lifecycle management
- BasePlugin: Abstract plugin base class
- HookDispatcher: Hook execution with priority system
- PluginRegistry: Plugin metadata and dependency resolution
"""

from .manager import PluginManager
from .base import BasePlugin
from .hooks import HookDispatcher, CORE_HOOKS

__all__ = [
    'PluginManager',
    'BasePlugin',
    'HookDispatcher',
    'CORE_HOOKS',
]

# Global plugin manager instance
_plugin_manager = None


def get_plugin_manager():
    """Get or create global plugin manager instance."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


def init_plugins(app, plugin_dir=None):
    """Initialize plugin system with Flask app."""
    manager = get_plugin_manager()
    manager.init_app(app, plugin_dir)
    return manager
