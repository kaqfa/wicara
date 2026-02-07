"""
Plugin Testing Framework - Helper Utilities

Utility functions for plugin testing.
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional


def create_temp_directory() -> str:
    """
    Create a temporary directory for testing.

    Returns:
        Path to temporary directory
    """
    return tempfile.mkdtemp(prefix='wicara_plugin_test_')


def cleanup_directory(path: str):
    """
    Safely remove a directory and all its contents.

    Args:
        path: Directory path to remove
    """
    if os.path.exists(path):
        try:
            shutil.rmtree(path)
        except Exception as e:
            # Log but don't fail if cleanup fails
            print(f"Warning: Failed to cleanup directory {path}: {e}")


def create_plugin_structure(
    base_dir: str,
    plugin_name: str,
    plugin_class_code: Optional[str] = None
) -> str:
    """
    Create a minimal plugin directory structure.

    Args:
        base_dir: Base directory for plugin
        plugin_name: Name of plugin (e.g., 'test-plugin')
        plugin_class_code: Optional custom plugin class code

    Returns:
        Path to plugin directory
    """
    plugin_dir = os.path.join(base_dir, plugin_name)
    os.makedirs(plugin_dir, exist_ok=True)

    # Create __init__.py
    init_file = os.path.join(plugin_dir, '__init__.py')
    with open(init_file, 'w') as f:
        f.write(f'"""Test plugin: {plugin_name}"""\n')
        if plugin_class_code:
            # Import the plugin class from plugin.py
            f.write('from .plugin import TestPlugin\n')
            f.write('__all__ = ["TestPlugin"]\n')

    # Create plugin.py with plugin class if provided
    if plugin_class_code:
        plugin_file = os.path.join(plugin_dir, 'plugin.py')
        with open(plugin_file, 'w') as f:
            f.write(plugin_class_code)

    return plugin_dir


def load_json_file(file_path: str) -> Dict[str, Any]:
    """
    Load JSON file safely.

    Args:
        file_path: Path to JSON file

    Returns:
        Parsed JSON data

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    with open(file_path, 'r') as f:
        return json.load(f)


def save_json_file(file_path: str, data: Dict[str, Any]):
    """
    Save data to JSON file.

    Args:
        file_path: Path to save JSON file
        data: Data to serialize
    """
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)


def generate_test_config() -> Dict[str, Any]:
    """
    Generate a minimal test configuration.

    Returns:
        Test configuration dict
    """
    return {
        'sitename': 'Test Site',
        'description': 'Test site description',
        'keywords': ['test', 'wicara'],
        'admin-password': 'test-hash',
        'pages': [
            {
                'title': 'Home',
                'template': 'home.html',
                'url': '/',
                'menu-title': 'Home',
                'seo-description': 'Home page',
                'seo-keywords': ['home'],
                'fields': [
                    {
                        'name': 'hero-title',
                        'type': 'text',
                        'label': 'Hero Title',
                        'value': 'Welcome'
                    }
                ]
            }
        ],
        'footer': {
            'content': ['Copyright 2026']
        }
    }


def create_test_plugin_class(
    plugin_name: str,
    hooks: Optional[Dict[str, Any]] = None,
    metadata_override: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate plugin class code for testing.

    Args:
        plugin_name: Name of the plugin
        hooks: Optional dict of hooks to register (NOTE: hooks should be None for code generation,
               use fixtures.create_test_plugin for runtime hook registration)
        metadata_override: Optional metadata overrides

    Returns:
        Python code as string
    """
    metadata = {
        'name': plugin_name.replace('-', ' ').title(),
        'version': '1.0.0',
        'author': 'Test Author',
        'description': f'Test plugin: {plugin_name}'
    }

    if metadata_override:
        metadata.update(metadata_override)

    # Generate hook handler methods
    hook_methods = ""
    hooks_return = ""

    if hooks:
        # Generate methods for each hook
        for hook_name, handler in hooks.items():
            method_name = f"hook_{hook_name.replace('-', '_')}"

            # Generate a simple pass-through method
            hook_methods += f"\n    def {method_name}(self, *args, **kwargs):\n"
            hook_methods += f"        # Hook handler for {hook_name}\n"
            hook_methods += "        pass\n"

        # Generate get_hooks return dict
        hooks_return = "\n    def get_hooks(self):\n"
        hooks_return += "        return {\n"
        for hook_name, handler in hooks.items():
            method_name = f"hook_{hook_name.replace('-', '_')}"

            # Check if handler is a dict with priority
            if isinstance(handler, dict):
                priority = handler.get('priority', 10)
                hooks_return += f"            '{hook_name}': {{\n"
                hooks_return += f"                'handler': self.{method_name},\n"
                hooks_return += f"                'priority': {priority}\n"
                hooks_return += "            },\n"
            else:
                hooks_return += f"            '{hook_name}': self.{method_name},\n"
        hooks_return += "        }\n"

    code = f"""from app.plugins.base import BasePlugin

class TestPlugin(BasePlugin):
    def get_metadata(self):
        return {metadata}

    def init(self, app):
        self.app = app
        self.initialized = True
{hook_methods}{hooks_return}
"""

    return code


def verify_plugin_structure(plugin_dir: str) -> tuple[bool, Optional[str]]:
    """
    Verify plugin directory has valid structure.

    Args:
        plugin_dir: Path to plugin directory

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not os.path.exists(plugin_dir):
        return False, f"Plugin directory does not exist: {plugin_dir}"

    if not os.path.isdir(plugin_dir):
        return False, f"Plugin path is not a directory: {plugin_dir}"

    init_file = os.path.join(plugin_dir, '__init__.py')
    if not os.path.exists(init_file):
        return False, "Plugin missing __init__.py"

    # Plugin.py is optional but if it exists, should be valid Python
    plugin_file = os.path.join(plugin_dir, 'plugin.py')
    if os.path.exists(plugin_file):
        try:
            with open(plugin_file, 'r') as f:
                compile(f.read(), plugin_file, 'exec')
        except SyntaxError as e:
            return False, f"Plugin has syntax error: {e}"

    return True, None


def compare_dicts(dict1: Dict, dict2: Dict, path: str = "") -> list[str]:
    """
    Deep comparison of two dictionaries, returning list of differences.

    Args:
        dict1: First dictionary
        dict2: Second dictionary
        path: Current path in nested structure (for error messages)

    Returns:
        List of difference descriptions
    """
    differences = []

    # Check keys in dict1
    for key in dict1:
        current_path = f"{path}.{key}" if path else key
        if key not in dict2:
            differences.append(f"Key missing in second dict: {current_path}")
        elif isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
            differences.extend(compare_dicts(dict1[key], dict2[key], current_path))
        elif dict1[key] != dict2[key]:
            differences.append(f"Value differs at {current_path}: {dict1[key]} != {dict2[key]}")

    # Check for keys in dict2 that aren't in dict1
    for key in dict2:
        if key not in dict1:
            current_path = f"{path}.{key}" if path else key
            differences.append(f"Extra key in second dict: {current_path}")

    return differences
