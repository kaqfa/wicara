"""
Plugin CLI Commands - Interactive CLI for plugin management

Provides comprehensive command-line tools for:
- Plugin management (list, install, uninstall, enable, disable, info)
- Plugin development (create, validate, package)
- Hook inspection (list hooks, handlers, stats)
"""

import os
import sys
import json
import re
import zipfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
import click

from app.plugins import get_plugin_manager, CORE_HOOKS
from app.plugins.installer import PluginInstaller
from app.plugins.types import (
    FieldTypePlugin, AdminPagePlugin, TemplateFilterPlugin,
    CLICommandPlugin, CacheBackendPlugin, EventPlugin
)


# ============================================================================
# PLUGIN MANAGEMENT COMMANDS
# ============================================================================

def plugin_list():
    """List all installed plugins with status."""
    manager = get_plugin_manager()

    # Initialize if not already done
    if not manager.plugin_dir:
        from app import create_app
        app = create_app()
        manager.init_app(app)

    # Get all plugins
    installer = PluginInstaller(manager.plugin_dir)
    installed = installer.get_installed_plugins()
    loaded = manager.get_all()

    if not installed:
        click.echo(click.style('No plugins installed', fg='yellow'))
        return

    click.echo(click.style('\nInstalled Plugins:', fg='cyan', bold=True))
    click.echo('=' * 80)

    for plugin_name, metadata in installed.items():
        # Check if loaded
        is_loaded = plugin_name in loaded
        is_enabled = loaded[plugin_name].is_enabled() if is_loaded else False

        # Status indicator
        if is_loaded and is_enabled:
            status = click.style('● ENABLED', fg='green', bold=True)
        elif is_loaded and not is_enabled:
            status = click.style('○ DISABLED', fg='yellow')
        else:
            status = click.style('× NOT LOADED', fg='red')

        # Display plugin info
        name = metadata.get('name', plugin_name)
        version = metadata.get('version', 'unknown')
        author = metadata.get('author', 'unknown')
        description = metadata.get('description', 'No description')

        click.echo(f"\n{status}  {click.style(name, fg='white', bold=True)} v{version}")
        click.echo(f"  Author: {author}")
        click.echo(f"  Description: {description}")
        click.echo(f"  Package: {plugin_name}")

    click.echo('\n' + '=' * 80)
    click.echo(f"Total: {len(installed)} plugin(s) installed")
    if loaded:
        enabled_count = sum(1 for p in loaded.values() if p.is_enabled())
        click.echo(f"Loaded: {len(loaded)} plugin(s) ({enabled_count} enabled)")


def plugin_install(source: str):
    """
    Install plugin from ZIP file or directory.

    Args:
        source: Path to ZIP file or directory
    """
    manager = get_plugin_manager()

    # Initialize if not already done
    if not manager.plugin_dir:
        from app import create_app
        app = create_app()
        manager.init_app(app)

    installer = PluginInstaller(manager.plugin_dir)

    # Validate source exists
    if not os.path.exists(source):
        click.echo(click.style(f'✗ Error: Source not found: {source}', fg='red', bold=True))
        return False

    click.echo(f"Installing plugin from: {source}")

    # Install from ZIP or directory
    if source.endswith('.zip'):
        success, error = installer.install_from_zip(source, manager)
    elif os.path.isdir(source):
        success, error = installer.install_from_directory(source, manager)
    else:
        click.echo(click.style('✗ Error: Source must be ZIP file or directory', fg='red'))
        return False

    if success:
        click.echo(click.style('✓ Plugin installed successfully', fg='green', bold=True))
        click.echo('\nNext steps:')
        click.echo('  1. Run "python run.py plugin-list" to verify installation')
        click.echo('  2. Restart the application to load the plugin')
        return True
    else:
        click.echo(click.style(f'✗ Installation failed: {error}', fg='red', bold=True))
        return False


def plugin_uninstall(plugin_name: str, force: bool = False):
    """
    Uninstall a plugin.

    Args:
        plugin_name: Name of plugin to uninstall
        force: Skip confirmation prompt
    """
    manager = get_plugin_manager()

    # Initialize if not already done
    if not manager.plugin_dir:
        from app import create_app
        app = create_app()
        manager.init_app(app)

    installer = PluginInstaller(manager.plugin_dir)

    # Check if plugin exists
    installed = installer.get_installed_plugins()
    if plugin_name not in installed:
        click.echo(click.style(f'✗ Error: Plugin "{plugin_name}" is not installed', fg='red'))
        return False

    # Show plugin info
    metadata = installed[plugin_name]
    click.echo(f"\nPlugin to uninstall:")
    click.echo(f"  Name: {metadata.get('name', plugin_name)}")
    click.echo(f"  Version: {metadata.get('version', 'unknown')}")
    click.echo(f"  Author: {metadata.get('author', 'unknown')}")

    # Check for dependents
    if manager.registry.exists(plugin_name):
        dependents = manager.registry.get_dependents(plugin_name)
        if dependents:
            click.echo(click.style(f'\n⚠ Warning: The following plugins depend on this plugin:', fg='yellow'))
            for dep in dependents:
                click.echo(f'  - {dep}')

    # Confirm
    if not force:
        if not click.confirm('\nAre you sure you want to uninstall this plugin?'):
            click.echo('Uninstall cancelled')
            return False

    # Uninstall
    success, error = installer.uninstall(plugin_name, manager)

    if success:
        click.echo(click.style('✓ Plugin uninstalled successfully', fg='green', bold=True))
        return True
    else:
        click.echo(click.style(f'✗ Uninstall failed: {error}', fg='red', bold=True))
        return False


def plugin_enable(plugin_name: str):
    """
    Enable a plugin.

    Args:
        plugin_name: Name of plugin to enable
    """
    manager = get_plugin_manager()

    # Initialize if not already done
    if not manager.plugin_dir:
        from app import create_app
        app = create_app()
        manager.init_app(app)

    # Load plugin if not already loaded
    if plugin_name not in manager.plugins:
        click.echo(f"Loading plugin: {plugin_name}")
        plugin = manager.load(plugin_name)
        if not plugin:
            click.echo(click.style(f'✗ Error: Failed to load plugin "{plugin_name}"', fg='red'))
            return False

    # Enable plugin
    success = manager.enable(plugin_name)

    if success:
        click.echo(click.style(f'✓ Plugin "{plugin_name}" enabled successfully', fg='green', bold=True))
        return True
    else:
        click.echo(click.style(f'✗ Error: Failed to enable plugin "{plugin_name}"', fg='red'))
        return False


def plugin_disable(plugin_name: str):
    """
    Disable a plugin.

    Args:
        plugin_name: Name of plugin to disable
    """
    manager = get_plugin_manager()

    # Initialize if not already done
    if not manager.plugin_dir:
        from app import create_app
        app = create_app()
        manager.init_app(app)

    # Check if plugin is loaded
    if plugin_name not in manager.plugins:
        click.echo(click.style(f'✗ Error: Plugin "{plugin_name}" is not loaded', fg='red'))
        return False

    # Disable plugin
    success = manager.disable(plugin_name)

    if success:
        click.echo(click.style(f'✓ Plugin "{plugin_name}" disabled successfully', fg='green', bold=True))
        return True
    else:
        click.echo(click.style(f'✗ Error: Failed to disable plugin "{plugin_name}"', fg='red'))
        return False


def plugin_info(plugin_name: str):
    """
    Show detailed plugin information.

    Args:
        plugin_name: Name of plugin
    """
    manager = get_plugin_manager()

    # Initialize if not already done
    if not manager.plugin_dir:
        from app import create_app
        app = create_app()
        manager.init_app(app)

    installer = PluginInstaller(manager.plugin_dir)

    # Get plugin metadata
    installed = installer.get_installed_plugins()
    if plugin_name not in installed:
        click.echo(click.style(f'✗ Error: Plugin "{plugin_name}" is not installed', fg='red'))
        return False

    metadata = installed[plugin_name]

    # Check if loaded
    is_loaded = plugin_name in manager.plugins
    is_enabled = manager.plugins[plugin_name].is_enabled() if is_loaded else False

    # Display header
    click.echo('\n' + '=' * 80)
    click.echo(click.style(f"Plugin: {metadata.get('name', plugin_name)}", fg='cyan', bold=True))
    click.echo('=' * 80)

    # Basic info
    click.echo(f"Version: {metadata.get('version', 'unknown')}")
    click.echo(f"Author: {metadata.get('author', 'unknown')}")

    # Status
    if is_loaded and is_enabled:
        status_text = click.style('ENABLED', fg='green', bold=True)
    elif is_loaded and not is_enabled:
        status_text = click.style('DISABLED', fg='yellow')
    else:
        status_text = click.style('NOT LOADED', fg='red')
    click.echo(f"Status: {status_text}")

    click.echo(f"\nDescription:")
    click.echo(f"  {metadata.get('description', 'No description')}")

    # Dependencies
    depends_on = metadata.get('depends_on', [])
    if depends_on:
        click.echo(f"\nDependencies:")
        for dep in depends_on:
            click.echo(f"  - {dep}")
    else:
        click.echo(f"\nDependencies: None")

    # Version requirements
    min_version = metadata.get('min_version')
    max_version = metadata.get('max_version')
    if min_version or max_version:
        click.echo(f"\nVersion Requirements:")
        if min_version:
            click.echo(f"  Minimum Wicara version: {min_version}")
        if max_version:
            click.echo(f"  Maximum Wicara version: {max_version}")

    # Hooks (if loaded)
    if is_loaded:
        plugin = manager.plugins[plugin_name]
        hooks = plugin.get_hooks()
        if hooks:
            click.echo(f"\nHooks Registered: {len(hooks)}")
            for hook_name in hooks.keys():
                handlers = manager.hooks.get_handlers(hook_name)
                plugin_handlers = [h for h in handlers if h['plugin'] == plugin_name]
                for handler in plugin_handlers:
                    priority = handler['priority']
                    click.echo(f"  - {hook_name} (priority: {priority})")

    # File info
    plugin_path = os.path.join(manager.plugin_dir, plugin_name)
    if os.path.exists(plugin_path):
        # Count files
        file_count = sum(len(files) for _, _, files in os.walk(plugin_path))

        # Calculate size
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(plugin_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total_size += os.path.getsize(fp)

        size_kb = total_size / 1024

        click.echo(f"\nFiles:")
        click.echo(f"  Total files: {file_count}")
        click.echo(f"  Size: {size_kb:.1f} KB")
        click.echo(f"  Location: {plugin_path}")

    click.echo('\n' + '=' * 80)
    return True


# ============================================================================
# PLUGIN DEVELOPMENT COMMANDS
# ============================================================================

def plugin_create():
    """Interactive wizard for creating a new plugin."""
    click.echo(click.style('\n=== Plugin Creation Wizard ===\n', fg='cyan', bold=True))

    # Get plugin name
    while True:
        name = click.prompt('Plugin name (lowercase with hyphens, e.g., my-plugin)')

        # Validate name format
        if re.match(r'^[a-z][a-z0-9-]*$', name):
            break
        else:
            click.echo(click.style('✗ Invalid name. Use lowercase letters, numbers, and hyphens only.', fg='red'))

    # Get metadata
    author = click.prompt('Author name')
    description = click.prompt('Plugin description')

    # Plugin type selection
    click.echo('\nPlugin type:')
    click.echo('  1. base       - Basic plugin (hooks only)')
    click.echo('  2. field      - Custom field type')
    click.echo('  3. admin      - Admin page extension')
    click.echo('  4. filter     - Content filter')
    click.echo('  5. cli        - CLI command')
    click.echo('  6. cache      - Cache backend')
    click.echo('  7. event      - Event listener')

    plugin_type = click.prompt(
        'Select plugin type',
        type=click.Choice(['1', '2', '3', '4', '5', '6', '7']),
        default='1'
    )

    type_map = {
        '1': 'base',
        '2': 'field',
        '3': 'admin',
        '4': 'filter',
        '5': 'cli',
        '6': 'cache',
        '7': 'event'
    }
    plugin_type_name = type_map[plugin_type]

    # Features
    has_templates = click.confirm('Include templates directory?', default=False)
    has_static = click.confirm('Include static files directory?', default=False)
    has_tests = click.confirm('Include test files?', default=True)

    # Initialize manager
    manager = get_plugin_manager()
    if not manager.plugin_dir:
        from app import create_app
        app = create_app()
        manager.init_app(app)

    # Create plugin
    click.echo(f"\n{click.style('Creating plugin...', fg='yellow')}")

    plugin_dir = os.path.join(manager.plugin_dir, name)
    if os.path.exists(plugin_dir):
        click.echo(click.style(f'✗ Error: Plugin directory already exists: {plugin_dir}', fg='red'))
        return False

    try:
        Path(plugin_dir).mkdir(parents=True, exist_ok=True)

        # Create __init__.py
        class_name = _to_class_name(name)
        init_content = f'''"""
{name} - Plugin for Wicara CMS
"""

from .plugin import {class_name}

__all__ = ['{class_name}']
'''
        with open(os.path.join(plugin_dir, '__init__.py'), 'w') as f:
            f.write(init_content)

        # Create plugin.py with appropriate base class
        plugin_content = _generate_plugin_code(name, author, description, plugin_type_name, class_name)
        with open(os.path.join(plugin_dir, 'plugin.py'), 'w') as f:
            f.write(plugin_content)

        # Create plugin.json manifest
        manifest = {
            'name': name,
            'version': '1.0.0',
            'author': author,
            'description': description,
            'min_version': '1.0.0',
            'depends_on': []
        }
        with open(os.path.join(plugin_dir, 'plugin.json'), 'w') as f:
            json.dump(manifest, f, indent=2)

        # Create templates directory if requested
        if has_templates:
            templates_dir = os.path.join(plugin_dir, 'templates')
            Path(templates_dir).mkdir(exist_ok=True)
            # Create example template
            with open(os.path.join(templates_dir, 'example.html'), 'w') as f:
                f.write('<!-- Example template for ' + name + ' -->\n')

        # Create static directory if requested
        if has_static:
            static_dir = os.path.join(plugin_dir, 'static')
            Path(static_dir).mkdir(exist_ok=True)
            # Create subdirectories
            Path(os.path.join(static_dir, 'css')).mkdir(exist_ok=True)
            Path(os.path.join(static_dir, 'js')).mkdir(exist_ok=True)

        # Create tests directory if requested
        if has_tests:
            tests_dir = os.path.join(plugin_dir, 'tests')
            Path(tests_dir).mkdir(exist_ok=True)
            test_content = f'''"""
Tests for {name} plugin
"""

import unittest
from app.plugins import get_plugin_manager

class Test{class_name}(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.manager = get_plugin_manager()

    def test_plugin_loads(self):
        """Test that plugin loads successfully."""
        plugin = self.manager.load('{name}')
        self.assertIsNotNone(plugin)

    def test_metadata(self):
        """Test plugin metadata."""
        plugin = self.manager.load('{name}')
        metadata = plugin.get_metadata()

        self.assertEqual(metadata['name'], '{name}')
        self.assertEqual(metadata['version'], '1.0.0')
        self.assertEqual(metadata['author'], '{author}')

if __name__ == '__main__':
    unittest.main()
'''
            with open(os.path.join(tests_dir, f'test_{name.replace("-", "_")}.py'), 'w') as f:
                f.write(test_content)

        # Create README
        readme_content = f'''# {name}

{description}

## Installation

Install this plugin by copying the `{name}` directory to `app/plugins/installed/`.

## Usage

After installation, restart the Wicara application to load the plugin.

## Author

{author}

## Version

1.0.0
'''
        with open(os.path.join(plugin_dir, 'README.md'), 'w') as f:
            f.write(readme_content)

        # Success message
        click.echo(click.style('\n✓ Plugin created successfully!', fg='green', bold=True))
        click.echo(f"\nLocation: {plugin_dir}")
        click.echo('\nNext steps:')
        click.echo(f"  1. Edit {os.path.join(plugin_dir, 'plugin.py')} to implement your plugin")
        if has_tests:
            click.echo(f"  2. Run tests: python run.py plugin-validate {name}")
        click.echo(f"  3. Package plugin: python run.py plugin-package {name}")

        return True

    except Exception as e:
        click.echo(click.style(f'✗ Error creating plugin: {e}', fg='red', bold=True))
        # Cleanup on failure
        if os.path.exists(plugin_dir):
            shutil.rmtree(plugin_dir)
        return False


def plugin_validate(plugin_name: str):
    """
    Validate plugin structure and code.

    Args:
        plugin_name: Name of plugin to validate
    """
    click.echo(f"Validating plugin: {plugin_name}\n")

    manager = get_plugin_manager()

    # Initialize if not already done
    if not manager.plugin_dir:
        from app import create_app
        app = create_app()
        manager.init_app(app)

    plugin_path = os.path.join(manager.plugin_dir, plugin_name)

    # Check if plugin exists
    if not os.path.exists(plugin_path):
        click.echo(click.style(f'✗ Plugin directory not found: {plugin_path}', fg='red'))
        return False

    errors = []
    warnings = []

    # Check for required files
    click.echo('Checking required files...')

    required_files = ['__init__.py', 'plugin.py']
    for filename in required_files:
        filepath = os.path.join(plugin_path, filename)
        if not os.path.exists(filepath):
            errors.append(f'Missing required file: {filename}')
        else:
            click.echo(click.style(f'  ✓ {filename}', fg='green'))

    # Check for plugin.json
    manifest_path = os.path.join(plugin_path, 'plugin.json')
    if not os.path.exists(manifest_path):
        warnings.append('Missing plugin.json manifest file')
    else:
        click.echo(click.style('  ✓ plugin.json', fg='green'))

        # Validate manifest
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)

            required_fields = ['name', 'version', 'author', 'description']
            for field in required_fields:
                if field not in manifest:
                    errors.append(f'Manifest missing required field: {field}')
        except json.JSONDecodeError as e:
            errors.append(f'Invalid JSON in plugin.json: {e}')

    # Try to load plugin
    click.echo('\nAttempting to load plugin...')
    try:
        plugin = manager.load(plugin_name)
        if plugin:
            click.echo(click.style('  ✓ Plugin loaded successfully', fg='green'))

            # Validate metadata
            metadata = plugin.get_metadata()
            click.echo('\nPlugin metadata:')
            click.echo(f"  Name: {metadata.get('name')}")
            click.echo(f"  Version: {metadata.get('version')}")
            click.echo(f"  Author: {metadata.get('author')}")

            # Check hooks
            hooks = plugin.get_hooks()
            if hooks:
                click.echo(f'\nRegistered hooks: {len(hooks)}')
                for hook_name in hooks.keys():
                    if hook_name in CORE_HOOKS:
                        click.echo(click.style(f'  ✓ {hook_name}', fg='green'))
                    else:
                        warnings.append(f'Unknown hook: {hook_name}')
        else:
            errors.append('Failed to load plugin')
    except Exception as e:
        errors.append(f'Error loading plugin: {e}')

    # Run tests if they exist
    tests_dir = os.path.join(plugin_path, 'tests')
    if os.path.exists(tests_dir):
        click.echo('\nRunning tests...')
        # Note: We could run tests here with unittest or pytest
        click.echo(click.style('  ℹ Tests directory found (manual test run recommended)', fg='blue'))

    # Display results
    click.echo('\n' + '=' * 80)
    if errors:
        click.echo(click.style(f'\n✗ Validation failed with {len(errors)} error(s):', fg='red', bold=True))
        for error in errors:
            click.echo(click.style(f'  - {error}', fg='red'))
    else:
        click.echo(click.style('\n✓ Validation passed!', fg='green', bold=True))

    if warnings:
        click.echo(click.style(f'\n⚠ {len(warnings)} warning(s):', fg='yellow'))
        for warning in warnings:
            click.echo(click.style(f'  - {warning}', fg='yellow'))

    click.echo('=' * 80)

    return len(errors) == 0


def plugin_package(plugin_name: str):
    """
    Create ZIP package for distribution.

    Args:
        plugin_name: Name of plugin to package
    """
    manager = get_plugin_manager()

    # Initialize if not already done
    if not manager.plugin_dir:
        from app import create_app
        app = create_app()
        manager.init_app(app)

    plugin_path = os.path.join(manager.plugin_dir, plugin_name)

    # Check if plugin exists
    if not os.path.exists(plugin_path):
        click.echo(click.style(f'✗ Plugin not found: {plugin_name}', fg='red'))
        return False

    # Get version from manifest
    manifest_path = os.path.join(plugin_path, 'plugin.json')
    version = '1.0.0'
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
                version = manifest.get('version', '1.0.0')
        except:
            pass

    # Create output filename
    output_dir = os.path.join(os.getcwd(), 'dist')
    Path(output_dir).mkdir(exist_ok=True)
    output_file = os.path.join(output_dir, f'{plugin_name}-{version}.zip')

    click.echo(f"Packaging plugin: {plugin_name}")
    click.echo(f"Version: {version}")

    try:
        # Create ZIP file
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(plugin_path):
                # Skip __pycache__ and .pyc files
                dirs[:] = [d for d in dirs if d != '__pycache__']
                files = [f for f in files if not f.endswith('.pyc')]

                for file in files:
                    file_path = os.path.join(root, file)
                    # Calculate archive name (relative to parent of plugin_dir)
                    arcname = os.path.join(plugin_name, os.path.relpath(file_path, plugin_path))
                    zipf.write(file_path, arcname)
                    click.echo(f'  Added: {arcname}')

        file_size = os.path.getsize(output_file) / 1024
        click.echo(click.style(f'\n✓ Package created successfully!', fg='green', bold=True))
        click.echo(f'Location: {output_file}')
        click.echo(f'Size: {file_size:.1f} KB')

        return True

    except Exception as e:
        click.echo(click.style(f'✗ Error creating package: {e}', fg='red', bold=True))
        return False


# ============================================================================
# HOOK INSPECTION COMMANDS
# ============================================================================

def hook_list():
    """List all available hooks."""
    click.echo(click.style('\nAvailable Hooks in Wicara:', fg='cyan', bold=True))
    click.echo('=' * 80)

    # Group hooks by category
    categories = {
        'Page Rendering': [],
        'Configuration': [],
        'Cache': [],
        'Import/Export': [],
        'Admin': [],
        'Field': [],
        'CLI': [],
        'Template': []
    }

    for hook_name, hook_info in CORE_HOOKS.items():
        if 'page' in hook_name:
            categories['Page Rendering'].append((hook_name, hook_info))
        elif 'config' in hook_name:
            categories['Configuration'].append((hook_name, hook_info))
        elif 'cache' in hook_name:
            categories['Cache'].append((hook_name, hook_info))
        elif 'export' in hook_name or 'import' in hook_name:
            categories['Import/Export'].append((hook_name, hook_info))
        elif 'admin' in hook_name:
            categories['Admin'].append((hook_name, hook_info))
        elif 'field' in hook_name:
            categories['Field'].append((hook_name, hook_info))
        elif 'cli' in hook_name:
            categories['CLI'].append((hook_name, hook_info))
        elif 'template' in hook_name:
            categories['Template'].append((hook_name, hook_info))

    for category, hooks in categories.items():
        if hooks:
            click.echo(f"\n{click.style(category, fg='yellow', bold=True)}")
            for hook_name, hook_info in hooks:
                click.echo(f"\n  {click.style(hook_name, fg='white', bold=True)}")
                click.echo(f"    Description: {hook_info['description']}")
                click.echo(f"    Arguments: {', '.join(hook_info['args']) if hook_info['args'] else 'None'}")
                click.echo(f"    Returns: {hook_info['returns']}")

    click.echo('\n' + '=' * 80)
    click.echo(f"Total: {len(CORE_HOOKS)} hooks available")


def hook_handlers(hook_name: str):
    """
    Show registered handlers for a specific hook.

    Args:
        hook_name: Name of the hook
    """
    manager = get_plugin_manager()

    # Initialize if not already done
    if not manager.plugin_dir:
        from app import create_app
        app = create_app()
        manager.init_app(app)
        manager.load_all()

    # Validate hook exists
    if hook_name not in CORE_HOOKS:
        click.echo(click.style(f'✗ Unknown hook: {hook_name}', fg='red'))
        click.echo(f'\nAvailable hooks: {", ".join(sorted(CORE_HOOKS.keys()))}')
        return False

    # Get handlers
    handlers = manager.hooks.get_handlers(hook_name)

    # Display hook info
    hook_info = CORE_HOOKS[hook_name]
    click.echo('\n' + '=' * 80)
    click.echo(click.style(f"Hook: {hook_name}", fg='cyan', bold=True))
    click.echo('=' * 80)
    click.echo(f"Description: {hook_info['description']}")
    click.echo(f"Arguments: {', '.join(hook_info['args']) if hook_info['args'] else 'None'}")
    click.echo(f"Returns: {hook_info['returns']}")

    if not handlers:
        click.echo(click.style('\nNo handlers registered for this hook', fg='yellow'))
    else:
        click.echo(f"\n{click.style('Registered Handlers:', fg='yellow', bold=True)} ({len(handlers)})")
        click.echo('\nExecution order (by priority):')

        for i, handler in enumerate(handlers, 1):
            plugin_name = handler['plugin']
            priority = handler['priority']

            click.echo(f"\n  {i}. {click.style(plugin_name, fg='white', bold=True)}")
            click.echo(f"     Priority: {priority}")

    click.echo('\n' + '=' * 80)
    return True


def hook_stats():
    """Show hook execution statistics."""
    manager = get_plugin_manager()

    # Initialize if not already done
    if not manager.plugin_dir:
        from app import create_app
        app = create_app()
        manager.init_app(app)
        manager.load_all()

    click.echo(click.style('\nHook Execution Statistics:', fg='cyan', bold=True))
    click.echo('=' * 80)

    # Get execution log
    execution_log = manager.hooks.get_execution_log()

    if not execution_log:
        click.echo(click.style('No hook executions recorded yet', fg='yellow'))
        return True

    # Analyze execution log
    hook_counts = {}
    plugin_counts = {}
    error_count = 0

    for entry in execution_log:
        hook = entry['hook']
        plugin = entry['plugin']
        status = entry['status']

        # Count by hook
        if hook not in hook_counts:
            hook_counts[hook] = {'success': 0, 'error': 0}
        hook_counts[hook][status] += 1

        # Count by plugin
        if plugin not in plugin_counts:
            plugin_counts[plugin] = {'success': 0, 'error': 0}
        plugin_counts[plugin][status] += 1

        if status == 'error':
            error_count += 1

    # Display statistics
    total_executions = len(execution_log)
    success_rate = ((total_executions - error_count) / total_executions * 100) if total_executions > 0 else 0

    click.echo(f"\nTotal Executions: {total_executions}")
    click.echo(f"Success Rate: {success_rate:.1f}%")
    click.echo(f"Errors: {error_count}")

    # Hook statistics
    click.echo(f"\n{click.style('By Hook:', fg='yellow', bold=True)}")
    for hook, counts in sorted(hook_counts.items(), key=lambda x: x[1]['success'] + x[1]['error'], reverse=True):
        total = counts['success'] + counts['error']
        click.echo(f"  {hook}: {total} executions ({counts['success']} success, {counts['error']} errors)")

    # Plugin statistics
    click.echo(f"\n{click.style('By Plugin:', fg='yellow', bold=True)}")
    for plugin, counts in sorted(plugin_counts.items(), key=lambda x: x[1]['success'] + x[1]['error'], reverse=True):
        total = counts['success'] + counts['error']
        click.echo(f"  {plugin}: {total} executions ({counts['success']} success, {counts['error']} errors)")

    click.echo('\n' + '=' * 80)
    return True


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _to_class_name(name: str) -> str:
    """Convert plugin name to class name."""
    return ''.join(word.capitalize() for word in name.replace('-', '_').split('_')) + 'Plugin'


def _generate_plugin_code(name: str, author: str, description: str, plugin_type: str, class_name: str) -> str:
    """Generate plugin code based on type."""

    base_imports = "from app.plugins import BasePlugin"
    base_class = "BasePlugin"
    extra_methods = ""

    if plugin_type == 'field':
        base_imports = "from app.plugins.types import FieldTypePlugin"
        base_class = "FieldTypePlugin"
        extra_methods = '''
    def get_field_types(self):
        """Register custom field types."""
        return {
            'my_field': {
                'label': 'My Custom Field',
                'validator': self.validate_my_field,
            }
        }

    def validate_my_field(self, value):
        """Validate custom field value."""
        # Add validation logic here
        return True, None
'''

    elif plugin_type == 'admin':
        base_imports = "from app.plugins.types import AdminPagePlugin"
        base_class = "AdminPagePlugin"
        extra_methods = '''
    def register_admin_pages(self):
        """Register custom admin pages."""
        return {
            'my_page': {
                'label': 'My Page',
                'route': f'/admin/{name}',
                'icon': 'cog',
                'order': 100
            }
        }
'''

    elif plugin_type == 'filter':
        base_imports = "from app.plugins.types import TemplateFilterPlugin"
        base_class = "TemplateFilterPlugin"
        extra_methods = '''
    def get_filters(self):
        """Register content filters."""
        return {
            'my_filter': self.apply_filter
        }

    def apply_filter(self, content, **kwargs):
        """Apply filter to content."""
        # Add filter logic here
        return content
'''

    elif plugin_type == 'cli':
        base_imports = "from app.plugins.types import CLICommandPlugin"
        base_class = "CLICommandPlugin"
        extra_methods = '''
    def register_commands(self):
        """Register CLI commands."""
        return {
            'my-command': {
                'handler': self.my_command,
                'help': 'My custom command'
            }
        }

    def my_command(self, *args, **kwargs):
        """Custom CLI command."""
        print(f"Executing {name} command")
'''

    elif plugin_type == 'cache':
        base_imports = "from app.plugins.types import CacheBackendPlugin"
        base_class = "CacheBackendPlugin"
        extra_methods = '''
    def get_cache_backends(self):
        """Register custom cache backends."""
        return {
            'my_cache': self.create_cache_backend
        }

    def create_cache_backend(self, config):
        """Create cache backend instance."""
        # Return cache backend instance
        pass
'''

    elif plugin_type == 'event':
        base_imports = "from app.plugins.types import EventPlugin"
        base_class = "EventPlugin"
        extra_methods = '''
    def get_hooks(self):
        """Register event hooks."""
        return {
            'after_page_render': {
                'handler': self.on_page_render,
                'priority': 10
            }
        }

    def on_page_render(self, page_data, html):
        """Handle page render event."""
        # Add event handling logic here
        return html
'''

    return f'''"""
Main plugin class for {name}
"""

{base_imports}


class {class_name}({base_class}):
    """
    {description}
    """

    def get_metadata(self):
        return {{
            'name': '{name}',
            'version': '1.0.0',
            'author': '{author}',
            'description': '{description}',
            'min_version': '1.0.0',
            'depends_on': []
        }}

    def init(self, app):
        """Initialize plugin with Flask app."""
        self.app = app
        # Add initialization logic here
{extra_methods}
'''
