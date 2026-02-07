"""
Plugin Testing Framework - Public API

Testing framework for Wicara plugins.

Provides:
- PluginTestCase: Base test case class with setUp/tearDown
- Test fixtures: create_test_plugin, create_mock_page, etc.
- Mock objects: MockFlaskApp, MockConfigManager, etc.
- Custom assertions: assert_plugin_loaded, assert_hook_registered, etc.
- Test runner: PluginTestRunner for isolated test execution
- Helpers: Utility functions for testing

Example:
    from app.plugins.testing import PluginTestCase, assert_plugin_loaded

    class TestMyPlugin(PluginTestCase):
        def test_plugin_loads(self):
            self.create_test_plugin('my-plugin')
            plugin = self.load_plugin('my-plugin')
            assert_plugin_loaded(self.plugin_manager, 'my-plugin')

        def test_hook_execution(self):
            self.create_test_plugin('my-plugin', hooks={
                'after_config_save': lambda config: {'modified': True}
            })
            self.load_plugin('my-plugin')
            result = self.execute_hook('after_config_save', {})
            self.assertEqual(result['modified'], True)
"""

# Base test case
from .fixtures import (
    PluginTestCase,
    PluginTestContext,
    create_test_plugin,
    create_mock_page,
    create_mock_field
)

# Mock objects
from .mocks import (
    MockFlaskApp,
    MockLogger,
    MockConfigManager,
    MockFileManager,
    MockTemplateManager,
    MockCacheManager
)

# Custom assertions
from .assertions import (
    PluginAssertionError,
    assert_plugin_loaded,
    assert_plugin_not_loaded,
    assert_plugin_enabled,
    assert_plugin_disabled,
    assert_hook_registered,
    assert_hook_not_registered,
    assert_hook_executed,
    assert_hook_execution_count,
    assert_plugin_metadata_valid,
    assert_plugin_dependencies_satisfied,
    assert_plugin_version_compatible,
    assert_plugin_initialized,
    assert_hook_priority,
    assert_plugin_config_valid
)

# Test runner
from .runner import (
    PluginTestRunner,
    PluginTestValidator
)

# Helpers
from .helpers import (
    create_temp_directory,
    cleanup_directory,
    create_plugin_structure,
    load_json_file,
    save_json_file,
    generate_test_config,
    create_test_plugin_class,
    verify_plugin_structure,
    compare_dicts
)

__all__ = [
    # Base test case
    'PluginTestCase',
    'PluginTestContext',
    'create_test_plugin',
    'create_mock_page',
    'create_mock_field',

    # Mock objects
    'MockFlaskApp',
    'MockLogger',
    'MockConfigManager',
    'MockFileManager',
    'MockTemplateManager',
    'MockCacheManager',

    # Assertions
    'PluginAssertionError',
    'assert_plugin_loaded',
    'assert_plugin_not_loaded',
    'assert_plugin_enabled',
    'assert_plugin_disabled',
    'assert_hook_registered',
    'assert_hook_not_registered',
    'assert_hook_executed',
    'assert_hook_execution_count',
    'assert_plugin_metadata_valid',
    'assert_plugin_dependencies_satisfied',
    'assert_plugin_version_compatible',
    'assert_plugin_initialized',
    'assert_hook_priority',
    'assert_plugin_config_valid',

    # Test runner
    'PluginTestRunner',
    'PluginTestValidator',

    # Helpers
    'create_temp_directory',
    'cleanup_directory',
    'create_plugin_structure',
    'load_json_file',
    'save_json_file',
    'generate_test_config',
    'create_test_plugin_class',
    'verify_plugin_structure',
    'compare_dicts',
]

__version__ = '1.0.0'
