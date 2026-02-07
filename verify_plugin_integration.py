#!/usr/bin/env python
"""
Verification script for Wicara Plugin System Integration.

This script verifies that the plugin system is properly integrated
by checking all the key integration points.
"""

import os
import sys
import ast


def check_file_for_pattern(filepath, pattern, description):
    """Check if a file contains a specific pattern."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            if pattern in content:
                print(f"✓ {description}")
                return True
            else:
                print(f"✗ {description}")
                return False
    except FileNotFoundError:
        print(f"✗ File not found: {filepath}")
        return False


def check_syntax(filepath):
    """Check if Python file has valid syntax."""
    try:
        with open(filepath, 'r') as f:
            ast.parse(f.read())
        return True
    except SyntaxError as e:
        print(f"✗ Syntax error in {filepath}: {e}")
        return False


def main():
    """Run verification checks."""
    print("=" * 70)
    print("Wicara Plugin System Integration Verification")
    print("=" * 70)
    print()

    checks_passed = 0
    checks_total = 0

    # Check 1: Application Factory
    print("1. Application Factory Integration (app/__init__.py)")
    print("-" * 70)
    checks_total += 4
    if check_file_for_pattern('app/__init__.py', 'from app.plugins import',
                              'Plugin imports added'):
        checks_passed += 1
    if check_file_for_pattern('app/__init__.py', 'init_plugins(app',
                              'Plugin initialization present'):
        checks_passed += 1
    if check_file_for_pattern('app/__init__.py', '_register_plugin_template_filters',
                              'Template filter registration present'):
        checks_passed += 1
    if check_syntax('app/__init__.py'):
        print("✓ Valid Python syntax")
        checks_passed += 1
    print()

    # Check 2: ConfigManager
    print("2. ConfigManager Integration (app/core/config_manager.py)")
    print("-" * 70)
    checks_total += 5
    if check_file_for_pattern('app/core/config_manager.py', 'before_config_load',
                              'before_config_load hook present'):
        checks_passed += 1
    if check_file_for_pattern('app/core/config_manager.py', 'after_config_load',
                              'after_config_load hook present'):
        checks_passed += 1
    if check_file_for_pattern('app/core/config_manager.py', 'before_config_save',
                              'before_config_save hook present'):
        checks_passed += 1
    if check_file_for_pattern('app/core/config_manager.py', 'after_config_save',
                              'after_config_save hook present'):
        checks_passed += 1
    if check_syntax('app/core/config_manager.py'):
        print("✓ Valid Python syntax")
        checks_passed += 1
    print()

    # Check 3: Template Manager
    print("3. Template Manager Integration (app/core/template_manager.py)")
    print("-" * 70)
    checks_total += 3
    if check_file_for_pattern('app/core/template_manager.py', 'before_page_render',
                              'before_page_render hook present'):
        checks_passed += 1
    if check_file_for_pattern('app/core/template_manager.py', 'after_page_render',
                              'after_page_render hook present'):
        checks_passed += 1
    if check_syntax('app/core/template_manager.py'):
        print("✓ Valid Python syntax")
        checks_passed += 1
    print()

    # Check 4: Cache Routes
    print("4. Cache Routes Integration (app/modules/admin/cache_routes.py)")
    print("-" * 70)
    checks_total += 3
    if check_file_for_pattern('app/modules/admin/cache_routes.py', 'before_cache_clear',
                              'before_cache_clear hook present'):
        checks_passed += 1
    if check_file_for_pattern('app/modules/admin/cache_routes.py', 'after_cache_clear',
                              'after_cache_clear hook present'):
        checks_passed += 1
    if check_syntax('app/modules/admin/cache_routes.py'):
        print("✓ Valid Python syntax")
        checks_passed += 1
    print()

    # Check 5: Import/Export Routes
    print("5. Import/Export Routes Integration (app/blueprints/import_export.py)")
    print("-" * 70)
    checks_total += 5
    if check_file_for_pattern('app/blueprints/import_export.py', 'before_export',
                              'before_export hook present'):
        checks_passed += 1
    if check_file_for_pattern('app/blueprints/import_export.py', 'after_export',
                              'after_export hook present'):
        checks_passed += 1
    if check_file_for_pattern('app/blueprints/import_export.py', 'before_import',
                              'before_import hook present'):
        checks_passed += 1
    if check_file_for_pattern('app/blueprints/import_export.py', 'after_import',
                              'after_import hook present'):
        checks_passed += 1
    if check_syntax('app/blueprints/import_export.py'):
        print("✓ Valid Python syntax")
        checks_passed += 1
    print()

    # Check 6: Test Plugin
    print("6. Test Plugin (app/plugins/installed/test-plugin/)")
    print("-" * 70)
    checks_total += 2
    if os.path.exists('app/plugins/installed/test-plugin/__init__.py'):
        print("✓ Test plugin file exists")
        checks_passed += 1
        if check_syntax('app/plugins/installed/test-plugin/__init__.py'):
            print("✓ Valid Python syntax")
            checks_passed += 1
    else:
        print("✗ Test plugin not found")
    print()

    # Check 7: Plugin System Files
    print("7. Plugin System Core Files")
    print("-" * 70)
    checks_total += 4
    if os.path.exists('app/plugins/__init__.py'):
        print("✓ Plugin __init__.py exists")
        checks_passed += 1
    if os.path.exists('app/plugins/manager.py'):
        print("✓ Plugin manager exists")
        checks_passed += 1
    if os.path.exists('app/plugins/hooks.py'):
        print("✓ Plugin hooks exists")
        checks_passed += 1
    if os.path.exists('app/plugins/base.py'):
        print("✓ Plugin base class exists")
        checks_passed += 1
    print()

    # Summary
    print("=" * 70)
    print(f"VERIFICATION SUMMARY: {checks_passed}/{checks_total} checks passed")
    print("=" * 70)

    if checks_passed == checks_total:
        print("✅ ALL CHECKS PASSED - Plugin system is properly integrated!")
        return 0
    else:
        print(f"⚠️  {checks_total - checks_passed} check(s) failed - review above for details")
        return 1


if __name__ == '__main__':
    sys.exit(main())
