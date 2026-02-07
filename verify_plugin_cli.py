#!/usr/bin/env python
"""
Verification script for plugin CLI commands.
Tests that all imports and basic functionality work correctly.
"""

import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.dirname(__file__))

def verify_imports():
    """Verify all required imports work."""
    print("Verifying imports...")
    errors = []

    try:
        from app.modules.cli import plugin_commands
        print("✓ plugin_commands module imported")
    except ImportError as e:
        errors.append(f"✗ Failed to import plugin_commands: {e}")

    try:
        from app.modules.cli import (
            plugin_list, plugin_install, plugin_uninstall,
            plugin_enable, plugin_disable, plugin_info,
            plugin_create, plugin_validate, plugin_package,
            hook_list, hook_handlers, hook_stats
        )
        print("✓ All plugin CLI functions imported")
    except ImportError as e:
        errors.append(f"✗ Failed to import CLI functions: {e}")

    try:
        from app.plugins import PluginManager, BasePlugin, HookDispatcher
        print("✓ Plugin system modules imported")
    except ImportError as e:
        errors.append(f"✗ Failed to import plugin system: {e}")

    try:
        from app.plugins.installer import PluginInstaller
        print("✓ PluginInstaller imported")
    except ImportError as e:
        errors.append(f"✗ Failed to import PluginInstaller: {e}")

    try:
        from app.plugins.types import (
            FieldTypePlugin, AdminPagePlugin, TemplateFilterPlugin,
            CLICommandPlugin, CacheBackendPlugin, EventPlugin
        )
        print("✓ Plugin types imported")
    except ImportError as e:
        errors.append(f"✗ Failed to import plugin types: {e}")

    try:
        import click
        print("✓ Click library available")
    except ImportError as e:
        errors.append(f"✗ Click library not available: {e}")

    return errors

def verify_functions():
    """Verify all CLI functions are callable."""
    print("\nVerifying function signatures...")
    errors = []

    try:
        from app.modules.cli import plugin_commands

        # Check all functions exist and are callable
        functions = [
            'plugin_list', 'plugin_install', 'plugin_uninstall',
            'plugin_enable', 'plugin_disable', 'plugin_info',
            'plugin_create', 'plugin_validate', 'plugin_package',
            'hook_list', 'hook_handlers', 'hook_stats'
        ]

        for func_name in functions:
            if hasattr(plugin_commands, func_name):
                func = getattr(plugin_commands, func_name)
                if callable(func):
                    print(f"✓ {func_name} is callable")
                else:
                    errors.append(f"✗ {func_name} is not callable")
            else:
                errors.append(f"✗ {func_name} not found")

    except Exception as e:
        errors.append(f"✗ Error verifying functions: {e}")

    return errors

def verify_run_py():
    """Verify run.py has all command handlers."""
    print("\nVerifying run.py integration...")
    errors = []

    try:
        with open('run.py', 'r') as f:
            content = f.read()

        # Check for command imports
        required_imports = [
            'plugin_list', 'plugin_install', 'plugin_uninstall',
            'plugin_enable', 'plugin_disable', 'plugin_info',
            'plugin_create', 'plugin_validate', 'plugin_package',
            'hook_list', 'hook_handlers', 'hook_stats'
        ]

        for import_name in required_imports:
            if import_name in content:
                print(f"✓ {import_name} imported in run.py")
            else:
                errors.append(f"✗ {import_name} not imported in run.py")

        # Check for command handlers
        commands = [
            'plugin-list', 'plugin-install', 'plugin-uninstall',
            'plugin-enable', 'plugin-disable', 'plugin-info',
            'plugin-create', 'plugin-validate', 'plugin-package',
            'hook-list', 'hook-handlers', 'hook-stats'
        ]

        for cmd in commands:
            if f"command == '{cmd}'" in content:
                print(f"✓ Handler for '{cmd}' found in run.py")
            else:
                errors.append(f"✗ Handler for '{cmd}' not found in run.py")

    except Exception as e:
        errors.append(f"✗ Error checking run.py: {e}")

    return errors

def main():
    """Run all verification checks."""
    print("=" * 80)
    print("Plugin CLI Implementation Verification")
    print("=" * 80)

    all_errors = []

    # Run verifications
    all_errors.extend(verify_imports())
    all_errors.extend(verify_functions())
    all_errors.extend(verify_run_py())

    # Summary
    print("\n" + "=" * 80)
    if all_errors:
        print(f"VERIFICATION FAILED: {len(all_errors)} error(s) found")
        print("=" * 80)
        for error in all_errors:
            print(error)
        return 1
    else:
        print("✓ ALL VERIFICATIONS PASSED")
        print("=" * 80)
        print("\nPlugin CLI commands are ready to use!")
        print("\nTry these commands:")
        print("  python run.py plugin-list")
        print("  python run.py plugin-create")
        print("  python run.py hook-list")
        print("  python run.py help")
        return 0

if __name__ == '__main__':
    sys.exit(main())
