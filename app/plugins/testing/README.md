# Plugin Testing Framework

Production-ready testing framework for Wicara CMS plugins.

## Overview

The Plugin Testing Framework provides comprehensive tools for testing Wicara plugins in isolation, including:

- **PluginTestCase**: Base test case class with setUp/tearDown
- **Test Fixtures**: Factory functions for creating test plugins and data
- **Mock Objects**: Isolated mocks for Flask app, ConfigManager, FileManager, etc.
- **Custom Assertions**: Plugin-specific assertion functions
- **Test Runner**: Isolated test execution and validation
- **Helpers**: Utility functions for common testing tasks

## Quick Start

### Basic Test Example

```python
from app.plugins.testing import PluginTestCase, assert_plugin_loaded

class TestMyPlugin(PluginTestCase):
    def test_plugin_loads(self):
        # Create a test plugin
        self.create_test_plugin('my-plugin')

        # Load the plugin
        plugin = self.load_plugin('my-plugin')

        # Assert it loaded correctly
        assert_plugin_loaded(self.plugin_manager, 'my-plugin')
        self.assertIsNotNone(plugin)
```

### Testing Hook Execution

```python
from app.plugins.testing import PluginTestCase, assert_hook_executed
from app.plugins.base import BasePlugin

class TestHooks(PluginTestCase):
    def test_hook_execution(self):
        # Define custom plugin with hook
        class MyHookPlugin(BasePlugin):
            def get_metadata(self):
                return {
                    'name': 'My Hook Plugin',
                    'version': '1.0.0',
                    'author': 'Test',
                    'description': 'Test'
                }

            def init(self, app):
                self.app = app

            def get_hooks(self):
                return {
                    'after_config_save': self.on_config_save
                }

            def on_config_save(self, config):
                config['modified'] = True
                return config

        # Register plugin manually
        plugin = MyHookPlugin()
        plugin.manager = self.plugin_manager
        plugin.app = self.app
        plugin.init(self.app)

        self.plugin_manager.plugins['my-hook-plugin'] = plugin
        self.plugin_manager.registry.register('my-hook-plugin', plugin.get_metadata())

        # Register hooks
        for hook_name, handler in plugin.get_hooks().items():
            self.plugin_manager.hooks.register(hook_name, handler, plugin_name='my-hook-plugin')

        # Execute hook
        config = {}
        result = self.execute_hook('after_config_save', config)

        # Verify
        assert_hook_executed(self.plugin_manager, 'after_config_save')
        self.assertTrue(result['modified'])
```

### Using Mock Objects

```python
from app.plugins.testing import PluginTestCase

class TestWithMocks(PluginTestCase):
    def test_config_operations(self):
        # Mock config manager is automatically available
        config = self.config_manager.load_config()
        config['sitename'] = 'Test Site'
        self.config_manager.save_config(config)

        # Verify
        new_config = self.config_manager.load_config()
        self.assertEqual(new_config['sitename'], 'Test Site')

    def test_file_operations(self):
        # Mock file manager
        content = b'test content'
        path = self.file_manager.save_file(content, 'test.txt')

        self.assertTrue(self.file_manager.file_exists('test.txt'))
        self.assertEqual(self.file_manager.get_file('test.txt'), content)
```

### Using Context Manager

```python
from app.plugins.testing import PluginTestContext

def test_with_context():
    with PluginTestContext() as ctx:
        ctx.create_plugin('test-plugin')
        plugin = ctx.load_plugin('test-plugin')
        assert plugin is not None
        # Automatic cleanup when exiting context
```

## Components

### 1. PluginTestCase

Base test case class providing:
- Automatic test environment setup/teardown
- Temporary plugin directory
- Mock Flask app
- Plugin manager instance
- Mock managers (config, file, template, cache)

**Methods:**
- `create_test_plugin(name, hooks, metadata)` - Create test plugin
- `load_plugin(name)` - Load plugin
- `unload_plugin(name)` - Unload plugin
- `execute_hook(name, *args, **kwargs)` - Execute hook
- `get_plugin(name)` - Get plugin instance
- `enable_plugin(name)` / `disable_plugin(name)` - Toggle plugin

### 2. Test Fixtures

**create_test_plugin(name, version, hooks, metadata)**
- Factory function to create plugin instances

**create_mock_page(title, url, template, fields)**
- Create mock page configuration

**create_mock_field(name, type, value, label)**
- Create mock field configuration

### 3. Mock Objects

**MockFlaskApp**
- Minimal Flask app interface
- Route registration tracking
- Template filter/global tracking

**MockConfigManager**
- In-memory configuration
- Load/save tracking
- Page CRUD operations

**MockFileManager**
- In-memory file storage
- Upload/delete tracking

**MockTemplateManager**
- Mock template rendering
- Context tracking

**MockCacheManager**
- In-memory caching
- Operation statistics

### 4. Custom Assertions

**Plugin Assertions:**
- `assert_plugin_loaded(manager, name)`
- `assert_plugin_not_loaded(manager, name)`
- `assert_plugin_enabled(manager, name)`
- `assert_plugin_disabled(manager, name)`
- `assert_plugin_initialized(plugin)`
- `assert_plugin_metadata_valid(plugin, required_fields)`
- `assert_plugin_dependencies_satisfied(manager, name)`
- `assert_plugin_version_compatible(manager, name, version)`

**Hook Assertions:**
- `assert_hook_registered(manager, hook_name, plugin_name)`
- `assert_hook_not_registered(manager, hook_name, plugin_name)`
- `assert_hook_executed(manager, hook_name)`
- `assert_hook_execution_count(manager, hook_name, count)`
- `assert_hook_priority(manager, hook_name, plugin_name, priority)`

### 5. Test Runner

**PluginTestRunner**
- Discover and run plugin tests
- Validate plugin structure and code
- Generate test reports
- Security scanning

**Methods:**
- `run_plugin_tests(plugin_name, pattern, verbosity)`
- `validate_plugin(plugin_name)`
- `validate_all_plugins()`
- `run_single_test(plugin_name, test_class, test_method)`
- `get_test_coverage(plugin_name)`

### 6. Helper Functions

- `create_temp_directory()` - Create temp directory
- `cleanup_directory(path)` - Safe directory removal
- `create_plugin_structure(base_dir, name, code)` - Create plugin files
- `verify_plugin_structure(plugin_dir)` - Validate structure
- `generate_test_config()` - Generate test configuration
- `compare_dicts(dict1, dict2)` - Deep dict comparison

## Running Tests

### Run Example Tests

```bash
# Run all example tests
python -m unittest app.plugins.testing.example_test -v

# Run specific test class
python -m unittest app.plugins.testing.example_test.ExamplePluginTestCase -v

# Run specific test method
python -m unittest app.plugins.testing.example_test.ExamplePluginTestCase.test_plugin_loads -v
```

### Run Plugin Tests

```python
from app.plugins.testing import PluginTestRunner

runner = PluginTestRunner(plugin_dir='app/plugins/installed')

# Run all tests for a plugin
result = runner.run_plugin_tests('my-plugin')

# Validate plugin structure
is_valid, issues = runner.validate_plugin('my-plugin')
if not is_valid:
    print(f"Validation issues: {issues}")

# Get test coverage
coverage = runner.get_test_coverage('my-plugin')
print(f"Test files: {coverage['test_files']}")
```

## Best Practices

### 1. Use PluginTestCase for Integration Tests

```python
class TestPluginIntegration(PluginTestCase):
    def test_full_workflow(self):
        # Test complete plugin lifecycle
        self.create_test_plugin('workflow-plugin')
        plugin = self.load_plugin('workflow-plugin')
        # ... test operations ...
        self.unload_plugin('workflow-plugin')
```

### 2. Use Factory Functions for Unit Tests

```python
from app.plugins.testing import create_test_plugin

def test_metadata():
    plugin = create_test_plugin(name='test', version='2.0.0')
    metadata = plugin.get_metadata()
    assert metadata['version'] == '2.0.0'
```

### 3. Test Hook Execution Order

```python
def test_priority_order(self):
    # Create plugins with different priorities
    self.create_test_plugin('high', hooks={'after_save': {'priority': 20}})
    self.create_test_plugin('low', hooks={'after_save': {'priority': 5}})

    self.load_plugin('high')
    self.load_plugin('low')

    handlers = self.get_hook_handlers('after_save')
    priorities = [h['priority'] for h in handlers]
    self.assertEqual(priorities, [20, 5])  # High to low
```

### 4. Validate Plugin Structure

```python
from app.plugins.testing import PluginTestRunner

runner = PluginTestRunner()
is_valid, issues = runner.validate_plugin('my-plugin')

assert is_valid, f"Plugin validation failed: {issues}"
```

### 5. Use Mock Managers

```python
def test_with_mocks(self):
    # Access pre-configured mocks
    config = self.config_manager.load_config()
    self.file_manager.save_file(b'data', 'test.txt')

    # Verify mock operations
    self.assertEqual(self.config_manager.get_save_count(), 0)
    self.assertEqual(self.file_manager.get_upload_count(), 1)
```

## Architecture

```
app/plugins/testing/
├── __init__.py          - Public API exports
├── fixtures.py          - PluginTestCase, test fixtures
├── mocks.py             - Mock objects (Flask, Config, File, etc.)
├── assertions.py        - Custom plugin assertions
├── runner.py            - Test runner with validation
├── helpers.py           - Utility functions
├── example_test.py      - Example test suite
└── README.md            - This file
```

## Integration with Plugin System

The testing framework integrates seamlessly with the existing plugin system:

```python
# In your plugin tests
from app.plugins import PluginManager, BasePlugin
from app.plugins.testing import PluginTestCase

class TestMyPlugin(PluginTestCase):
    # PluginManager and BasePlugin are available
    # Test environment is isolated
    pass
```

## Security Validation

The test runner includes basic security checks:

```python
runner = PluginTestRunner()
is_valid, issues = runner.validate_plugin('my-plugin')

# Checks for:
# - eval(), exec() usage
# - os.system() calls
# - Unrestricted file access
# - Dynamic imports
```

## Examples

See `example_test.py` for comprehensive examples demonstrating:
- Plugin creation and loading
- Hook registration and execution
- Multiple plugin management
- Enable/disable functionality
- Mock object usage
- Custom assertions
- Priority-based execution
- Context manager usage

## Version

1.0.0 - Production Ready

## License

Part of Wicara CMS - See main project LICENSE
