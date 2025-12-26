"""
Plugin Installer - PLG-04

Handles plugin installation, removal, and updates.
"""

import os
import json
import shutil
import zipfile
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


PLUGIN_MANIFEST_FILE = 'plugin.json'


class PluginInstaller:
    """
    Manages plugin installation and removal.

    Supports:
    - Installation from ZIP file
    - Installation from directory
    - Plugin validation
    - Dependency checking
    - Clean removal
    """

    def __init__(self, plugin_dir: str):
        """
        Initialize installer.

        Args:
            plugin_dir: Directory where plugins are installed
        """
        self.plugin_dir = plugin_dir
        Path(plugin_dir).mkdir(parents=True, exist_ok=True)

    def install_from_zip(self, zip_path: str, plugin_manager) -> Tuple[bool, Optional[str]]:
        """
        Install plugin from ZIP file.

        ZIP should contain plugin package in root:
        plugin-name/
            __init__.py
            plugin.json
            ...

        Args:
            zip_path: Path to plugin ZIP file
            plugin_manager: PluginManager instance for validation

        Returns:
            Tuple of (success, error_message)
        """
        if not os.path.exists(zip_path):
            return False, f"ZIP file not found: {zip_path}"

        temp_dir = None
        try:
            # Extract ZIP
            temp_dir = os.path.join(self.plugin_dir, '.temp_extract')
            Path(temp_dir).mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(temp_dir)

            # Find plugin directory (should be single top-level dir)
            entries = os.listdir(temp_dir)
            if len(entries) != 1:
                return False, "ZIP should contain single plugin directory"

            plugin_dir_name = entries[0]
            source_dir = os.path.join(temp_dir, plugin_dir_name)

            if not os.path.isdir(source_dir):
                return False, "ZIP should contain directory, not file"

            # Validate plugin
            is_valid, error = self._validate_plugin_dir(source_dir, plugin_dir_name)
            if not is_valid:
                return False, error

            # Move to plugins directory
            dest_dir = os.path.join(self.plugin_dir, plugin_dir_name)
            if os.path.exists(dest_dir):
                return False, f"Plugin '{plugin_dir_name}' already installed"

            shutil.move(source_dir, dest_dir)
            logger.info(f"Installed plugin: {plugin_dir_name} from {zip_path}")

            return True, None

        except Exception as e:
            logger.error(f"Failed to install plugin from ZIP: {e}")
            return False, str(e)

        finally:
            # Cleanup temp directory
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def install_from_directory(self, source_dir: str, plugin_manager) -> Tuple[bool, Optional[str]]:
        """
        Install plugin from directory.

        Args:
            source_dir: Path to plugin directory
            plugin_manager: PluginManager instance for validation

        Returns:
            Tuple of (success, error_message)
        """
        if not os.path.isdir(source_dir):
            return False, f"Directory not found: {source_dir}"

        try:
            plugin_name = os.path.basename(source_dir.rstrip('/\\'))

            # Validate plugin
            is_valid, error = self._validate_plugin_dir(source_dir, plugin_name)
            if not is_valid:
                return False, error

            # Copy to plugins directory
            dest_dir = os.path.join(self.plugin_dir, plugin_name)
            if os.path.exists(dest_dir):
                return False, f"Plugin '{plugin_name}' already installed"

            shutil.copytree(source_dir, dest_dir)
            logger.info(f"Installed plugin: {plugin_name} from {source_dir}")

            return True, None

        except Exception as e:
            logger.error(f"Failed to install plugin from directory: {e}")
            return False, str(e)

    def uninstall(self, plugin_name: str, plugin_manager) -> Tuple[bool, Optional[str]]:
        """
        Uninstall a plugin.

        Args:
            plugin_name: Name of plugin to uninstall
            plugin_manager: PluginManager instance

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Check if plugin is loaded
            if plugin_manager.get(plugin_name):
                # Unload first
                if not plugin_manager.unload(plugin_name):
                    return False, "Cannot uninstall plugin - dependent plugins exist"

            # Remove directory
            plugin_dir = os.path.join(self.plugin_dir, plugin_name)
            if os.path.exists(plugin_dir):
                shutil.rmtree(plugin_dir)

            logger.info(f"Uninstalled plugin: {plugin_name}")
            return True, None

        except Exception as e:
            logger.error(f"Failed to uninstall plugin '{plugin_name}': {e}")
            return False, str(e)

    def _validate_plugin_dir(self, plugin_dir: str, plugin_name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate plugin directory structure.

        Args:
            plugin_dir: Path to plugin directory
            plugin_name: Plugin name

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for __init__.py
        init_file = os.path.join(plugin_dir, '__init__.py')
        if not os.path.exists(init_file):
            return False, "Plugin must contain __init__.py"

        # Check for plugin.json (manifest)
        manifest_file = os.path.join(plugin_dir, PLUGIN_MANIFEST_FILE)
        if os.path.exists(manifest_file):
            try:
                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)

                # Validate manifest
                required = ['name', 'version', 'author', 'description']
                for field in required:
                    if field not in manifest:
                        return False, f"Manifest missing required field: {field}"

            except json.JSONDecodeError:
                return False, "Invalid plugin.json (not valid JSON)"

        return True, None

    def get_installed_plugins(self) -> Dict[str, Dict[str, Any]]:
        """
        Get list of installed plugins with metadata.

        Returns:
            Dict mapping plugin names to metadata
        """
        installed = {}

        try:
            for item in os.listdir(self.plugin_dir):
                if item.startswith('.') or item.startswith('_'):
                    continue

                plugin_path = os.path.join(self.plugin_dir, item)
                if not os.path.isdir(plugin_path):
                    continue

                # Check for __init__.py
                if not os.path.exists(os.path.join(plugin_path, '__init__.py')):
                    continue

                # Try to load manifest
                manifest_file = os.path.join(plugin_path, PLUGIN_MANIFEST_FILE)
                if os.path.exists(manifest_file):
                    try:
                        with open(manifest_file, 'r') as f:
                            manifest = json.load(f)
                            installed[item] = manifest
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid plugin.json in {item}")
                else:
                    # Plugin without manifest
                    installed[item] = {
                        'name': item,
                        'version': 'unknown',
                        'author': 'unknown',
                        'description': 'No description'
                    }

        except FileNotFoundError:
            pass

        return installed

    def create_plugin_template(self, plugin_name: str, author: str = "Unknown") -> Tuple[bool, Optional[str]]:
        """
        Create a new plugin template.

        Creates basic plugin structure with example code.

        Args:
            plugin_name: Name of plugin to create
            author: Author name

        Returns:
            Tuple of (success, error_message)
        """
        try:
            plugin_dir = os.path.join(self.plugin_dir, plugin_name)

            if os.path.exists(plugin_dir):
                return False, f"Plugin directory already exists: {plugin_dir}"

            Path(plugin_dir).mkdir(parents=True, exist_ok=True)

            # Create __init__.py
            init_content = f'''"""
{plugin_name} - Plugin for Wicara CMS
"""

from .plugin import {self._to_class_name(plugin_name)}

__all__ = ['{self._to_class_name(plugin_name)}']
'''
            with open(os.path.join(plugin_dir, '__init__.py'), 'w') as f:
                f.write(init_content)

            # Create plugin.py
            plugin_content = f'''"""
Main plugin class for {plugin_name}
"""

from app.plugins import BasePlugin


class {self._to_class_name(plugin_name)}(BasePlugin):
    """
    {plugin_name} - Example plugin for Wicara CMS
    """

    def get_metadata(self):
        return {{
            'name': '{plugin_name}',
            'version': '1.0.0',
            'author': '{author}',
            'description': 'Description of {plugin_name}',
            'min_version': '1.0.0'
        }}

    def init(self, app):
        """Initialize plugin with Flask app."""
        pass

    def get_hooks(self):
        """Register plugin hooks."""
        return {{}}
'''
            with open(os.path.join(plugin_dir, 'plugin.py'), 'w') as f:
                f.write(plugin_content)

            # Create plugin.json manifest
            manifest = {
                'name': plugin_name,
                'version': '1.0.0',
                'author': author,
                'description': f'Description of {plugin_name}',
                'min_version': '1.0.0'
            }
            with open(os.path.join(plugin_dir, 'plugin.json'), 'w') as f:
                json.dump(manifest, f, indent=2)

            logger.info(f"Created plugin template: {plugin_name}")
            return True, None

        except Exception as e:
            logger.error(f"Failed to create plugin template: {e}")
            return False, str(e)

    @staticmethod
    def _to_class_name(name: str) -> str:
        """Convert plugin name to class name."""
        return ''.join(word.capitalize() for word in name.replace('-', '_').split('_')) + 'Plugin'
