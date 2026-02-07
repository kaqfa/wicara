#!/usr/bin/env python
"""
Test script for ECS-11 migration script.
Verifies that the migration script has all required functionality.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from scripts.migrate_to_sites import MigrationScript, migrate_to_sites


def test_migration_script_structure():
    """Test that MigrationScript class has all required methods."""
    print("Testing MigrationScript class structure...")

    required_methods = [
        '__init__',
        'print_header',
        'print_step',
        'print_success',
        'print_warning',
        'print_error',
        'check_prerequisites',
        'confirm_migration',
        'create_directory_structure',
        'copy_config_files',
        'copy_user_templates',
        'move_admin_templates',
        'copy_static_files',
        'update_env_file',
        'verify_migration',
        'print_summary',
    ]

    migrator = MigrationScript()

    for method_name in required_methods:
        if not hasattr(migrator, method_name):
            print(f"✗ FAIL: Missing method '{method_name}'")
            return False
        print(f"✓ Found method: {method_name}")

    print("\n✓ All required methods present")
    return True


def test_migration_function():
    """Test that migrate_to_sites function exists and is callable."""
    print("\nTesting migrate_to_sites function...")

    if not callable(migrate_to_sites):
        print("✗ FAIL: migrate_to_sites is not callable")
        return False

    print("✓ migrate_to_sites function is callable")
    return True


def test_class_attributes():
    """Test that MigrationScript instance has required attributes."""
    print("\nTesting MigrationScript attributes...")

    migrator = MigrationScript()

    required_attrs = {
        'root_dir': Path,
        'sites_dir': Path,
        'default_site_dir': Path,
        'errors': list,
        'warnings': list,
        'copied_files': dict,
    }

    for attr_name, expected_type in required_attrs.items():
        if not hasattr(migrator, attr_name):
            print(f"✗ FAIL: Missing attribute '{attr_name}'")
            return False

        attr_value = getattr(migrator, attr_name)
        if not isinstance(attr_value, expected_type):
            print(f"✗ FAIL: Attribute '{attr_name}' has wrong type")
            print(f"  Expected: {expected_type.__name__}")
            print(f"  Got: {type(attr_value).__name__}")
            return False

        print(f"✓ Attribute '{attr_name}': {expected_type.__name__}")

    print("\n✓ All required attributes present with correct types")
    return True


def test_copied_files_structure():
    """Test that copied_files dict has correct structure."""
    print("\nTesting copied_files structure...")

    migrator = MigrationScript()

    expected_categories = ['config', 'templates', 'css', 'js', 'images']

    for category in expected_categories:
        if category not in migrator.copied_files:
            print(f"✗ FAIL: Missing category '{category}' in copied_files")
            return False

        if not isinstance(migrator.copied_files[category], list):
            print(f"✗ FAIL: Category '{category}' is not a list")
            return False

        print(f"✓ Category '{category}': list")

    print("\n✓ copied_files has correct structure")
    return True


def test_path_attributes():
    """Test that path attributes are set correctly."""
    print("\nTesting path attributes...")

    migrator = MigrationScript()

    # Check root_dir
    if not migrator.root_dir.exists():
        print(f"⚠ WARNING: root_dir does not exist: {migrator.root_dir}")
        print("  (This is OK if running tests from a different location)")
    else:
        print(f"✓ root_dir exists: {migrator.root_dir}")

    # Check sites_dir path
    expected_sites = migrator.root_dir / 'sites'
    if migrator.sites_dir != expected_sites:
        print(f"✗ FAIL: sites_dir incorrect")
        print(f"  Expected: {expected_sites}")
        print(f"  Got: {migrator.sites_dir}")
        return False
    print(f"✓ sites_dir path: {migrator.sites_dir}")

    # Check default_site_dir path
    expected_default = expected_sites / 'default'
    if migrator.default_site_dir != expected_default:
        print(f"✗ FAIL: default_site_dir incorrect")
        print(f"  Expected: {expected_default}")
        print(f"  Got: {migrator.default_site_dir}")
        return False
    print(f"✓ default_site_dir path: {migrator.default_site_dir}")

    print("\n✓ Path attributes configured correctly")
    return True


def run_all_tests():
    """Run all tests."""
    print("=" * 70)
    print("  ECS-11 Migration Script Test Suite")
    print("=" * 70)

    tests = [
        test_migration_script_structure,
        test_migration_function,
        test_class_attributes,
        test_copied_files_structure,
        test_path_attributes,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n✗ EXCEPTION in {test.__name__}: {e}")
            failed += 1

    print("\n" + "=" * 70)
    print("  Test Results")
    print("=" * 70)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")

    if failed == 0:
        print("\n✓ All tests passed!")
        return True
    else:
        print(f"\n✗ {failed} test(s) failed")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
