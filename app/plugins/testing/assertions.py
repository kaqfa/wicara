"""
Plugin Testing Framework - Custom Assertions

Custom assertion functions for plugin testing.
"""

from typing import Optional, Dict, Any, List
from app.plugins.manager import PluginManager
from app.plugins.base import BasePlugin


class PluginAssertionError(AssertionError):
    """Custom exception for plugin assertion failures."""
    pass


def assert_plugin_loaded(
    plugin_manager: PluginManager,
    plugin_name: str,
    message: Optional[str] = None
):
    """
    Assert that a plugin is loaded in the plugin manager.

    Args:
        plugin_manager: PluginManager instance
        plugin_name: Name of plugin to check
        message: Optional custom error message

    Raises:
        PluginAssertionError: If plugin is not loaded
    """
    if plugin_name not in plugin_manager.plugins:
        error_msg = message or f"Plugin '{plugin_name}' is not loaded"
        raise PluginAssertionError(error_msg)


def assert_plugin_not_loaded(
    plugin_manager: PluginManager,
    plugin_name: str,
    message: Optional[str] = None
):
    """
    Assert that a plugin is NOT loaded.

    Args:
        plugin_manager: PluginManager instance
        plugin_name: Name of plugin to check
        message: Optional custom error message

    Raises:
        PluginAssertionError: If plugin is loaded
    """
    if plugin_name in plugin_manager.plugins:
        error_msg = message or f"Plugin '{plugin_name}' should not be loaded"
        raise PluginAssertionError(error_msg)


def assert_plugin_enabled(
    plugin_manager: PluginManager,
    plugin_name: str,
    message: Optional[str] = None
):
    """
    Assert that a plugin is enabled.

    Args:
        plugin_manager: PluginManager instance
        plugin_name: Name of plugin to check
        message: Optional custom error message

    Raises:
        PluginAssertionError: If plugin is not enabled or not loaded
    """
    assert_plugin_loaded(plugin_manager, plugin_name)
    plugin = plugin_manager.get(plugin_name)
    if not plugin.is_enabled():
        error_msg = message or f"Plugin '{plugin_name}' is not enabled"
        raise PluginAssertionError(error_msg)


def assert_plugin_disabled(
    plugin_manager: PluginManager,
    plugin_name: str,
    message: Optional[str] = None
):
    """
    Assert that a plugin is disabled.

    Args:
        plugin_manager: PluginManager instance
        plugin_name: Name of plugin to check
        message: Optional custom error message

    Raises:
        PluginAssertionError: If plugin is not disabled or not loaded
    """
    assert_plugin_loaded(plugin_manager, plugin_name)
    plugin = plugin_manager.get(plugin_name)
    if plugin.is_enabled():
        error_msg = message or f"Plugin '{plugin_name}' should be disabled"
        raise PluginAssertionError(error_msg)


def assert_hook_registered(
    plugin_manager: PluginManager,
    hook_name: str,
    plugin_name: Optional[str] = None,
    message: Optional[str] = None
):
    """
    Assert that a hook is registered.

    Args:
        plugin_manager: PluginManager instance
        hook_name: Name of hook to check
        plugin_name: Optional plugin name to check specific registration
        message: Optional custom error message

    Raises:
        PluginAssertionError: If hook is not registered
    """
    handlers = plugin_manager.hooks.get_handlers(hook_name)

    if not handlers:
        error_msg = message or f"Hook '{hook_name}' has no registered handlers"
        raise PluginAssertionError(error_msg)

    if plugin_name:
        plugin_registered = any(h['plugin'] == plugin_name for h in handlers)
        if not plugin_registered:
            error_msg = message or f"Hook '{hook_name}' not registered by plugin '{plugin_name}'"
            raise PluginAssertionError(error_msg)


def assert_hook_not_registered(
    plugin_manager: PluginManager,
    hook_name: str,
    plugin_name: Optional[str] = None,
    message: Optional[str] = None
):
    """
    Assert that a hook is NOT registered.

    Args:
        plugin_manager: PluginManager instance
        hook_name: Name of hook to check
        plugin_name: Optional plugin name to check specific registration
        message: Optional custom error message

    Raises:
        PluginAssertionError: If hook is registered
    """
    handlers = plugin_manager.hooks.get_handlers(hook_name)

    if plugin_name:
        plugin_registered = any(h['plugin'] == plugin_name for h in handlers)
        if plugin_registered:
            error_msg = message or f"Hook '{hook_name}' should not be registered by plugin '{plugin_name}'"
            raise PluginAssertionError(error_msg)
    else:
        if handlers:
            error_msg = message or f"Hook '{hook_name}' should not have registered handlers"
            raise PluginAssertionError(error_msg)


def assert_hook_executed(
    plugin_manager: PluginManager,
    hook_name: str,
    message: Optional[str] = None
):
    """
    Assert that a hook was executed at least once.

    Args:
        plugin_manager: PluginManager instance
        hook_name: Name of hook to check
        message: Optional custom error message

    Raises:
        PluginAssertionError: If hook was not executed
    """
    execution_log = plugin_manager.hooks.get_execution_log()
    executed = any(entry['hook'] == hook_name for entry in execution_log)

    if not executed:
        error_msg = message or f"Hook '{hook_name}' was not executed"
        raise PluginAssertionError(error_msg)


def assert_hook_execution_count(
    plugin_manager: PluginManager,
    hook_name: str,
    expected_count: int,
    message: Optional[str] = None
):
    """
    Assert that a hook was executed a specific number of times.

    Args:
        plugin_manager: PluginManager instance
        hook_name: Name of hook to check
        expected_count: Expected execution count
        message: Optional custom error message

    Raises:
        PluginAssertionError: If execution count doesn't match
    """
    execution_log = plugin_manager.hooks.get_execution_log()
    actual_count = sum(1 for entry in execution_log if entry['hook'] == hook_name)

    if actual_count != expected_count:
        error_msg = message or (
            f"Hook '{hook_name}' executed {actual_count} times, expected {expected_count}"
        )
        raise PluginAssertionError(error_msg)


def assert_plugin_metadata_valid(
    plugin: BasePlugin,
    required_fields: Optional[List[str]] = None,
    message: Optional[str] = None
):
    """
    Assert that plugin metadata is complete and valid.

    Args:
        plugin: Plugin instance
        required_fields: Optional list of required metadata fields
        message: Optional custom error message

    Raises:
        PluginAssertionError: If metadata is invalid
    """
    metadata = plugin.get_metadata()

    # Default required fields
    if required_fields is None:
        required_fields = ['name', 'version', 'author', 'description']

    # Check each required field
    missing_fields = []
    for field in required_fields:
        if field not in metadata or not metadata[field]:
            missing_fields.append(field)

    if missing_fields:
        error_msg = message or (
            f"Plugin metadata missing required fields: {', '.join(missing_fields)}"
        )
        raise PluginAssertionError(error_msg)

    # Validate version format (basic semantic version check)
    version = metadata.get('version', '')
    if version and not _is_valid_version(version):
        error_msg = message or f"Invalid version format: {version} (expected semantic version)"
        raise PluginAssertionError(error_msg)


def assert_plugin_dependencies_satisfied(
    plugin_manager: PluginManager,
    plugin_name: str,
    message: Optional[str] = None
):
    """
    Assert that all plugin dependencies are satisfied.

    Args:
        plugin_manager: PluginManager instance
        plugin_name: Name of plugin to check
        message: Optional custom error message

    Raises:
        PluginAssertionError: If dependencies are not satisfied
    """
    is_satisfied, missing = plugin_manager.registry.validate_dependencies(plugin_name)

    if not is_satisfied:
        error_msg = message or (
            f"Plugin '{plugin_name}' has unsatisfied dependencies: {', '.join(missing)}"
        )
        raise PluginAssertionError(error_msg)


def assert_plugin_version_compatible(
    plugin_manager: PluginManager,
    plugin_name: str,
    wicara_version: Optional[str] = None,
    message: Optional[str] = None
):
    """
    Assert that plugin is compatible with Wicara version.

    Args:
        plugin_manager: PluginManager instance
        plugin_name: Name of plugin to check
        wicara_version: Optional Wicara version (uses manager's version if not provided)
        message: Optional custom error message

    Raises:
        PluginAssertionError: If version is not compatible
    """
    version_to_check = wicara_version or plugin_manager.wicara_version
    is_compatible, error = plugin_manager.registry.validate_version(
        plugin_name, version_to_check
    )

    if not is_compatible:
        error_msg = message or (
            f"Plugin '{plugin_name}' is not compatible: {error}"
        )
        raise PluginAssertionError(error_msg)


def assert_plugin_initialized(
    plugin: BasePlugin,
    message: Optional[str] = None
):
    """
    Assert that plugin has been initialized.

    Args:
        plugin: Plugin instance
        message: Optional custom error message

    Raises:
        PluginAssertionError: If plugin is not initialized
    """
    if plugin.app is None:
        error_msg = message or "Plugin has not been initialized (app is None)"
        raise PluginAssertionError(error_msg)


def assert_hook_priority(
    plugin_manager: PluginManager,
    hook_name: str,
    plugin_name: str,
    expected_priority: int,
    message: Optional[str] = None
):
    """
    Assert that a plugin's hook has specific priority.

    Args:
        plugin_manager: PluginManager instance
        hook_name: Name of hook
        plugin_name: Plugin that registered the hook
        expected_priority: Expected priority value
        message: Optional custom error message

    Raises:
        PluginAssertionError: If priority doesn't match
    """
    handlers = plugin_manager.hooks.get_handlers(hook_name)

    plugin_handler = None
    for handler in handlers:
        if handler['plugin'] == plugin_name:
            plugin_handler = handler
            break

    if not plugin_handler:
        raise PluginAssertionError(
            f"Plugin '{plugin_name}' has not registered hook '{hook_name}'"
        )

    actual_priority = plugin_handler['priority']
    if actual_priority != expected_priority:
        error_msg = message or (
            f"Hook '{hook_name}' priority is {actual_priority}, expected {expected_priority}"
        )
        raise PluginAssertionError(error_msg)


def assert_plugin_config_valid(
    plugin: BasePlugin,
    message: Optional[str] = None
):
    """
    Assert that plugin configuration is valid according to schema.

    Args:
        plugin: Plugin instance
        message: Optional custom error message

    Raises:
        PluginAssertionError: If config is invalid
    """
    schema = plugin.get_config_schema()
    if schema is None:
        # No schema defined, always valid
        return

    config = plugin.get_config()

    # Basic validation (could be extended with jsonschema library)
    if 'required' in schema:
        for field in schema['required']:
            if field not in config:
                error_msg = message or f"Plugin config missing required field: {field}"
                raise PluginAssertionError(error_msg)


# Helper functions

def _is_valid_version(version: str) -> bool:
    """
    Check if version string is valid semantic version.

    Args:
        version: Version string to validate

    Returns:
        True if valid semantic version
    """
    import re
    # Basic semantic version regex: X.Y.Z
    pattern = r'^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$'
    return bool(re.match(pattern, version))
