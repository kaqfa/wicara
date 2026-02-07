"""
Plugin Testing Framework - Test Fixtures

Base test case class and test fixtures for plugin testing.
"""

import os
import sys
import tempfile
import shutil
import unittest
from typing import Dict, Any, Optional, List
from pathlib import Path

from app.plugins.manager import PluginManager
from app.plugins.base import BasePlugin
from .mocks import (
    MockFlaskApp,
    MockConfigManager,
    MockFileManager,
    MockTemplateManager,
    MockCacheManager
)
from .helpers import (
    create_plugin_structure,
    create_test_plugin_class,
    generate_test_config
)


class PluginTestCase(unittest.TestCase):
    """
    Base test case for plugin testing.

    Provides isolated testing environment with:
    - Temporary plugin directory
    - Mock Flask app
    - Plugin manager instance
    - Mock config/file/template/cache managers
    - Automatic cleanup

    Example:
        class TestMyPlugin(PluginTestCase):
            def test_plugin_loads(self):
                plugin = self.load_plugin('my-plugin')
                self.assertIsNotNone(plugin)

            def test_hook_execution(self):
                plugin = self.load_plugin('my-plugin')
                result = self.execute_hook('after_config_save', {'test': 'data'})
                self.assertIsNotNone(result)
    """

    def setUp(self):
        """
        Set up test environment.

        Creates:
        - Temporary plugin directory
        - Mock Flask app
        - Plugin manager
        - Mock managers (config, file, template, cache)
        """
        # Create temporary plugin directory
        self.plugin_dir = tempfile.mkdtemp(prefix='wicara_test_plugins_')

        # Create mock Flask app
        self.app = MockFlaskApp(config={
            'TESTING': True,
            'SECRET_KEY': 'test-secret-key',
            'DEBUG': True
        })

        # Initialize plugin manager
        self.plugin_manager = PluginManager()
        self.plugin_manager.init_app(self.app, plugin_dir=self.plugin_dir)

        # Create mock managers
        self.config_manager = MockConfigManager(generate_test_config())
        self.file_manager = MockFileManager()
        self.template_manager = MockTemplateManager()
        self.cache_manager = MockCacheManager()

        # Store mock managers in app for plugin access
        self.app.config_manager = self.config_manager
        self.app.file_manager = self.file_manager
        self.app.template_manager = self.template_manager
        self.app.cache_manager = self.cache_manager

        # Track created plugins for cleanup
        self._created_plugins = []

    def tearDown(self):
        """
        Clean up test environment.

        Unloads all plugins and removes temporary directories.
        """
        # Unload all plugins
        for plugin_name in list(self.plugin_manager.plugins.keys()):
            try:
                self.plugin_manager.unload(plugin_name)
            except Exception as e:
                print(f"Warning: Failed to unload plugin {plugin_name}: {e}")

        # Remove temporary plugin directory
        if os.path.exists(self.plugin_dir):
            try:
                shutil.rmtree(self.plugin_dir)
            except Exception as e:
                print(f"Warning: Failed to cleanup plugin directory: {e}")

        # Remove plugin directory from sys.path
        if self.plugin_dir in sys.path:
            sys.path.remove(self.plugin_dir)

        # Clear hook execution log
        self.plugin_manager.hooks.clear_execution_log()

    def create_test_plugin(
        self,
        plugin_name: str,
        hooks: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a test plugin in the test plugin directory.

        Args:
            plugin_name: Name of plugin (e.g., 'test-plugin')
            hooks: Optional dict of hooks to register
            metadata: Optional metadata overrides

        Returns:
            Path to created plugin directory
        """
        plugin_code = create_test_plugin_class(plugin_name, hooks, metadata)
        plugin_dir = create_plugin_structure(
            self.plugin_dir,
            plugin_name,
            plugin_code
        )
        self._created_plugins.append(plugin_name)
        return plugin_dir

    def load_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """
        Load a plugin in the test environment.

        Args:
            plugin_name: Name of plugin to load

        Returns:
            Loaded plugin instance or None if load failed
        """
        return self.plugin_manager.load(plugin_name)

    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin.

        Args:
            plugin_name: Name of plugin to unload

        Returns:
            True if unloaded successfully
        """
        return self.plugin_manager.unload(plugin_name)

    def execute_hook(self, hook_name: str, *args, **kwargs) -> Any:
        """
        Execute a hook with test data.

        Args:
            hook_name: Name of hook to execute
            *args: Positional arguments for hook
            **kwargs: Keyword arguments for hook

        Returns:
            Hook execution result
        """
        return self.plugin_manager.hooks.execute(hook_name, *args, **kwargs)

    def execute_hook_multiple(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """
        Execute a hook and collect all results.

        Args:
            hook_name: Name of hook to execute
            *args: Positional arguments for hook
            **kwargs: Keyword arguments for hook

        Returns:
            List of results from all handlers
        """
        return self.plugin_manager.hooks.execute_multiple(hook_name, *args, **kwargs)

    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """
        Get loaded plugin instance.

        Args:
            plugin_name: Name of plugin

        Returns:
            Plugin instance or None
        """
        return self.plugin_manager.get(plugin_name)

    def enable_plugin(self, plugin_name: str) -> bool:
        """
        Enable a plugin.

        Args:
            plugin_name: Name of plugin

        Returns:
            True if enabled successfully
        """
        return self.plugin_manager.enable(plugin_name)

    def disable_plugin(self, plugin_name: str) -> bool:
        """
        Disable a plugin.

        Args:
            plugin_name: Name of plugin

        Returns:
            True if disabled successfully
        """
        return self.plugin_manager.disable(plugin_name)

    def get_hook_handlers(self, hook_name: str) -> List[Dict[str, Any]]:
        """
        Get registered handlers for a hook.

        Args:
            hook_name: Name of hook

        Returns:
            List of handler info dicts
        """
        return self.plugin_manager.hooks.get_handlers(hook_name)

    def get_hook_execution_log(self) -> List[Dict[str, Any]]:
        """
        Get hook execution log.

        Returns:
            List of execution log entries
        """
        return self.plugin_manager.hooks.get_execution_log()

    def clear_hook_execution_log(self):
        """Clear hook execution log."""
        self.plugin_manager.hooks.clear_execution_log()

    def assert_plugin_loaded(self, plugin_name: str):
        """Assert plugin is loaded."""
        self.assertIn(plugin_name, self.plugin_manager.plugins,
                     f"Plugin '{plugin_name}' should be loaded")

    def assert_plugin_not_loaded(self, plugin_name: str):
        """Assert plugin is not loaded."""
        self.assertNotIn(plugin_name, self.plugin_manager.plugins,
                        f"Plugin '{plugin_name}' should not be loaded")

    def assert_hook_registered(self, hook_name: str, plugin_name: Optional[str] = None):
        """Assert hook is registered."""
        handlers = self.get_hook_handlers(hook_name)
        self.assertTrue(handlers, f"Hook '{hook_name}' should have handlers")

        if plugin_name:
            plugin_registered = any(h['plugin'] == plugin_name for h in handlers)
            self.assertTrue(plugin_registered,
                          f"Hook '{hook_name}' should be registered by '{plugin_name}'")

    def assert_hook_executed(self, hook_name: str):
        """Assert hook was executed."""
        log = self.get_hook_execution_log()
        executed = any(entry['hook'] == hook_name for entry in log)
        self.assertTrue(executed, f"Hook '{hook_name}' should have been executed")


def create_test_plugin(
    name: str = 'test-plugin',
    version: str = '1.0.0',
    hooks: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> BasePlugin:
    """
    Factory function to create a minimal test plugin instance.

    Args:
        name: Plugin name
        version: Plugin version
        hooks: Optional hooks to register
        metadata: Optional metadata overrides

    Returns:
        BasePlugin instance

    Example:
        plugin = create_test_plugin(
            name='my-test-plugin',
            hooks={'after_config_save': lambda config: print('saved')}
        )
    """
    from app.plugins.base import BasePlugin

    class TestPlugin(BasePlugin):
        def __init__(self):
            super().__init__()
            self._metadata = {
                'name': name.replace('-', ' ').title(),
                'version': version,
                'author': 'Test Author',
                'description': f'Test plugin: {name}'
            }
            if metadata:
                self._metadata.update(metadata)
            self._hooks = hooks or {}

        def get_metadata(self) -> Dict[str, Any]:
            return self._metadata

        def init(self, app):
            self.app = app
            self.initialized = True

        def get_hooks(self) -> Dict[str, Any]:
            # Return hooks as-is since this is a runtime instance
            return self._hooks if self._hooks else {}

    return TestPlugin()


def create_mock_page(
    title: str = 'Test Page',
    url: str = '/test',
    template: str = 'test.html',
    fields: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Create a mock page configuration for testing.

    Args:
        title: Page title
        url: Page URL
        template: Template filename
        fields: Optional list of fields

    Returns:
        Page configuration dict
    """
    return {
        'title': title,
        'template': template,
        'url': url,
        'menu-title': title,
        'seo-description': f'{title} description',
        'seo-keywords': ['test'],
        'fields': fields or [
            {
                'name': 'test-field',
                'type': 'text',
                'label': 'Test Field',
                'value': 'test value'
            }
        ]
    }


def create_mock_field(
    name: str = 'test-field',
    field_type: str = 'text',
    value: str = 'test value',
    label: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a mock field configuration for testing.

    Args:
        name: Field name
        field_type: Field type (text, textarea, image)
        value: Field value
        label: Optional field label

    Returns:
        Field configuration dict
    """
    return {
        'name': name,
        'type': field_type,
        'label': label or name.replace('-', ' ').title(),
        'value': value
    }


class PluginTestContext:
    """
    Context manager for isolated plugin testing.

    Provides temporary plugin environment that automatically cleans up.

    Example:
        with PluginTestContext() as ctx:
            plugin = ctx.create_plugin('test-plugin')
            ctx.load_plugin('test-plugin')
            result = ctx.execute_hook('after_config_save', {})
    """

    def __init__(self):
        """Initialize test context."""
        self.plugin_dir = None
        self.plugin_manager = None
        self.app = None
        self.config_manager = None
        self.file_manager = None

    def __enter__(self):
        """Enter context - set up test environment."""
        # Create temporary plugin directory
        self.plugin_dir = tempfile.mkdtemp(prefix='wicara_test_plugins_')

        # Create mock Flask app
        self.app = MockFlaskApp(config={'TESTING': True})

        # Initialize plugin manager
        self.plugin_manager = PluginManager()
        self.plugin_manager.init_app(self.app, plugin_dir=self.plugin_dir)

        # Create mock managers
        self.config_manager = MockConfigManager(generate_test_config())
        self.file_manager = MockFileManager()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context - clean up test environment."""
        # Unload all plugins
        if self.plugin_manager:
            for plugin_name in list(self.plugin_manager.plugins.keys()):
                try:
                    self.plugin_manager.unload(plugin_name)
                except Exception:
                    pass

        # Remove temporary directory
        if self.plugin_dir and os.path.exists(self.plugin_dir):
            try:
                shutil.rmtree(self.plugin_dir)
            except Exception:
                pass

    def create_plugin(self, plugin_name: str, hooks: Optional[Dict] = None) -> str:
        """Create test plugin."""
        plugin_code = create_test_plugin_class(plugin_name, hooks)
        return create_plugin_structure(self.plugin_dir, plugin_name, plugin_code)

    def load_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """Load plugin."""
        return self.plugin_manager.load(plugin_name)

    def execute_hook(self, hook_name: str, *args, **kwargs):
        """Execute hook."""
        return self.plugin_manager.hooks.execute(hook_name, *args, **kwargs)
