"""
Plugin Testing Framework - Example Tests

Demonstrates how to use the plugin testing framework.
These tests also verify that the framework itself works correctly.
"""

import unittest
from app.plugins.testing import (
    PluginTestCase,
    PluginTestContext,
    assert_plugin_loaded,
    assert_plugin_enabled,
    assert_hook_registered,
    assert_hook_executed,
    assert_plugin_metadata_valid,
    assert_plugin_initialized,
    create_test_plugin,
    create_mock_page
)


class ExamplePluginTestCase(PluginTestCase):
    """
    Example test case demonstrating PluginTestCase usage.

    This shows how to:
    - Create test plugins
    - Load and unload plugins
    - Test hook execution
    - Use custom assertions
    """

    def test_create_and_load_plugin(self):
        """Test creating and loading a simple plugin."""
        # Create a test plugin
        self.create_test_plugin('example-plugin')

        # Load the plugin
        plugin = self.load_plugin('example-plugin')

        # Assertions
        self.assertIsNotNone(plugin)
        assert_plugin_loaded(self.plugin_manager, 'example-plugin')
        assert_plugin_initialized(plugin)

    def test_plugin_metadata(self):
        """Test plugin metadata validation."""
        # Create plugin with custom metadata
        self.create_test_plugin(
            'metadata-test-plugin',
            metadata={
                'name': 'Metadata Test Plugin',
                'version': '2.0.0',
                'author': 'Test Author',
                'description': 'Testing metadata'
            }
        )

        # Load and validate
        plugin = self.load_plugin('metadata-test-plugin')
        assert_plugin_metadata_valid(plugin)

        # Check specific metadata values
        metadata = plugin.get_metadata()
        self.assertEqual(metadata['name'], 'Metadata Test Plugin')
        self.assertEqual(metadata['version'], '2.0.0')

    def test_hook_registration(self):
        """Test hook registration and execution."""
        # Create plugin with hook (using simplified approach)
        self.create_test_plugin(
            'hook-test-plugin',
            hooks={
                'after_config_save': None  # Will generate a placeholder method
            }
        )

        # Load plugin
        plugin = self.load_plugin('hook-test-plugin')

        # Verify hook is registered
        assert_hook_registered(
            self.plugin_manager,
            'after_config_save',
            'hook-test-plugin'
        )

    def test_hook_execution(self):
        """Test executing hooks and getting results."""
        # Use the factory function to create a plugin with actual hook implementation
        from app.plugins.base import BasePlugin

        class ExecutionTestPlugin(BasePlugin):
            def get_metadata(self):
                return {
                    'name': 'Execution Test Plugin',
                    'version': '1.0.0',
                    'author': 'Test Author',
                    'description': 'Test hook execution'
                }

            def init(self, app):
                self.app = app

            def get_hooks(self):
                return {
                    'before_page_render': self.before_page_render_handler
                }

            def before_page_render_handler(self, page_data, context):
                context['injected_by_plugin'] = 'test value'
                return context

        # Manually register the plugin
        plugin = ExecutionTestPlugin()
        plugin.manager = self.plugin_manager
        plugin.app = self.app
        plugin.init(self.app)

        # Register in manager
        self.plugin_manager.plugins['execution-test-plugin'] = plugin
        self.plugin_manager.registry.register('execution-test-plugin', plugin.get_metadata())

        # Register hooks
        hooks = plugin.get_hooks()
        for hook_name, handler in hooks.items():
            self.plugin_manager.hooks.register(hook_name, handler, plugin_name='execution-test-plugin')

        # Execute hook
        page_data = create_mock_page()
        context = {'existing': 'data'}
        result = self.execute_hook('before_page_render', page_data, context)

        # Verify hook was executed
        assert_hook_executed(self.plugin_manager, 'before_page_render')

        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result['injected_by_plugin'], 'test value')

    def test_multiple_plugins(self):
        """Test loading multiple plugins."""
        # Create multiple plugins
        self.create_test_plugin('plugin-one')
        self.create_test_plugin('plugin-two')
        self.create_test_plugin('plugin-three')

        # Load all plugins
        plugin1 = self.load_plugin('plugin-one')
        plugin2 = self.load_plugin('plugin-two')
        plugin3 = self.load_plugin('plugin-three')

        # Verify all loaded
        self.assertIsNotNone(plugin1)
        self.assertIsNotNone(plugin2)
        self.assertIsNotNone(plugin3)

        # Check plugin manager stats
        stats = self.plugin_manager.get_stats()
        self.assertEqual(stats['total_plugins'], 3)

    def test_enable_disable_plugin(self):
        """Test enabling and disabling plugins."""
        # Create and load plugin
        self.create_test_plugin('toggle-plugin')
        plugin = self.load_plugin('toggle-plugin')

        # Plugin should be enabled by default
        self.assertTrue(plugin.is_enabled())

        # Disable plugin
        self.disable_plugin('toggle-plugin')
        self.assertFalse(plugin.is_enabled())

        # Re-enable plugin
        self.enable_plugin('toggle-plugin')
        self.assertTrue(plugin.is_enabled())

    def test_plugin_unload(self):
        """Test unloading plugins."""
        # Create and load plugin
        self.create_test_plugin('unload-test-plugin')
        plugin = self.load_plugin('unload-test-plugin')
        self.assertIsNotNone(plugin)

        # Unload plugin
        success = self.unload_plugin('unload-test-plugin')
        self.assertTrue(success)

        # Verify plugin is unloaded
        self.assertIsNone(self.get_plugin('unload-test-plugin'))

    def test_mock_config_manager(self):
        """Test using mock config manager."""
        # Access mock config manager
        config = self.config_manager.load_config()

        # Verify default config exists
        self.assertIn('sitename', config)
        self.assertEqual(config['sitename'], 'Test Site')

        # Modify config
        config['sitename'] = 'Modified Site'
        self.config_manager.save_config(config)

        # Verify modification
        new_config = self.config_manager.load_config()
        self.assertEqual(new_config['sitename'], 'Modified Site')

    def test_mock_file_manager(self):
        """Test using mock file manager."""
        # Save a file
        test_content = b'test file content'
        path = self.file_manager.save_file(test_content, 'test.txt')

        # Verify file was saved
        self.assertTrue(self.file_manager.file_exists('test.txt'))

        # Retrieve file
        content = self.file_manager.get_file('test.txt')
        self.assertEqual(content, test_content)

        # Delete file
        deleted = self.file_manager.delete_file('test.txt')
        self.assertTrue(deleted)
        self.assertFalse(self.file_manager.file_exists('test.txt'))

    def test_hook_execution_order(self):
        """Test hook execution with different priorities."""
        # Create plugins with different priorities using code generation
        self.create_test_plugin(
            'high-priority-plugin',
            hooks={
                'after_config_save': {'priority': 20}
            }
        )
        self.create_test_plugin(
            'medium-priority-plugin',
            hooks={
                'after_config_save': {'priority': 10}
            }
        )
        self.create_test_plugin(
            'low-priority-plugin',
            hooks={
                'after_config_save': {'priority': 5}
            }
        )

        # Load all plugins
        self.load_plugin('high-priority-plugin')
        self.load_plugin('medium-priority-plugin')
        self.load_plugin('low-priority-plugin')

        # Verify all hooks are registered
        handlers = self.get_hook_handlers('after_config_save')
        self.assertEqual(len(handlers), 3)

        # Verify priorities are correct (sorted descending)
        priorities = [h['priority'] for h in handlers]
        self.assertEqual(priorities, [20, 10, 5])


class ExampleContextManagerTest(unittest.TestCase):
    """
    Example using PluginTestContext context manager.

    Demonstrates usage without inheriting from PluginTestCase.
    """

    def test_context_manager_usage(self):
        """Test using context manager for isolated testing."""
        with PluginTestContext() as ctx:
            # Create and load plugin
            ctx.create_plugin('context-test-plugin')
            plugin = ctx.load_plugin('context-test-plugin')

            # Verify plugin loaded
            self.assertIsNotNone(plugin)
            self.assertIn('context-test-plugin', ctx.plugin_manager.plugins)

        # After context exit, everything should be cleaned up


class ExampleFactoryFunctionTest(unittest.TestCase):
    """
    Example using factory functions for quick testing.

    Demonstrates creating plugins programmatically.
    """

    def test_factory_function(self):
        """Test using create_test_plugin factory."""
        # Create plugin instance directly with actual callable hook
        def test_hook(config):
            return config

        plugin = create_test_plugin(
            name='factory-plugin',
            version='1.5.0',
            hooks={
                'after_config_load': test_hook
            }
        )

        # Verify plugin
        metadata = plugin.get_metadata()
        self.assertEqual(metadata['version'], '1.5.0')
        self.assertIn('Factory Plugin', metadata['name'])

        # Verify hooks
        hooks = plugin.get_hooks()
        self.assertIn('after_config_load', hooks)
        self.assertEqual(hooks['after_config_load'], test_hook)


class ExampleAssertionsTest(PluginTestCase):
    """
    Example demonstrating all custom assertions.
    """

    def test_all_assertions(self):
        """Test all custom assertion functions."""
        # Create test plugin
        self.create_test_plugin(
            'assertions-test-plugin',
            hooks={
                'after_config_save': None
            }
        )

        # Load plugin
        plugin = self.load_plugin('assertions-test-plugin')

        # Test plugin assertions
        assert_plugin_loaded(self.plugin_manager, 'assertions-test-plugin')
        assert_plugin_enabled(self.plugin_manager, 'assertions-test-plugin')
        assert_plugin_initialized(plugin)
        assert_plugin_metadata_valid(plugin)

        # Test hook assertions
        assert_hook_registered(
            self.plugin_manager,
            'after_config_save',
            'assertions-test-plugin'
        )

        # Execute hook
        self.execute_hook('after_config_save', {})

        # Test execution assertion
        assert_hook_executed(self.plugin_manager, 'after_config_save')


# Run tests if executed directly
if __name__ == '__main__':
    unittest.main(verbosity=2)
