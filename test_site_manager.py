#!/usr/bin/env python3
"""
Simple test script for SiteManager (ECS-01).

Tests SiteManager functionality in both legacy and sites mode.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.site_manager import SiteManager


def test_legacy_mode():
    """Test SiteManager in legacy mode."""
    print("\n" + "="*60)
    print("Testing Legacy Mode")
    print("="*60)

    manager = SiteManager(legacy_mode=True)
    print(f"✓ Created SiteManager: {manager}")

    # Test path methods
    config_path = manager.get_config_path()
    print(f"✓ Config path: {config_path}")
    assert config_path == 'config.json', f"Expected 'config.json', got '{config_path}'"

    templates_dir = manager.get_templates_dir()
    print(f"✓ Templates dir: {templates_dir}")
    assert templates_dir == 'templates', f"Expected 'templates', got '{templates_dir}'"

    static_dir = manager.get_static_dir()
    print(f"✓ Static dir: {static_dir}")
    assert static_dir == 'static', f"Expected 'static', got '{static_dir}'"

    uploads_dir = manager.get_uploads_dir()
    print(f"✓ Uploads dir: {uploads_dir}")
    assert uploads_dir == 'static/images/uploads', f"Expected 'static/images/uploads', got '{uploads_dir}'"

    # Test site methods
    sites = manager.get_all_sites()
    print(f"✓ All sites: {sites}")
    assert sites == ['default'], f"Expected ['default'], got {sites}"

    # Test site creation (should fail in legacy mode)
    success, message = manager.create_site('test-site')
    print(f"✓ Create site (expected to fail): {message}")
    assert not success, "Site creation should fail in legacy mode"

    print("\n✅ All legacy mode tests passed!")
    return True


def test_sites_mode():
    """Test SiteManager in sites mode."""
    print("\n" + "="*60)
    print("Testing Sites Mode")
    print("="*60)

    # Create temporary directory for testing
    temp_dir = tempfile.mkdtemp(prefix='wicara_test_')
    print(f"✓ Created temp directory: {temp_dir}")

    try:
        manager = SiteManager(
            sites_dir=os.path.join(temp_dir, 'sites'),
            default_site='default',
            legacy_mode=False
        )
        print(f"✓ Created SiteManager: {manager}")

        # Test path methods
        config_path = manager.get_config_path()
        print(f"✓ Config path: {config_path}")
        assert 'sites/default/config.json' in config_path, f"Unexpected config path: {config_path}"

        templates_dir = manager.get_templates_dir()
        print(f"✓ Templates dir: {templates_dir}")
        assert 'sites/default/templates' in templates_dir, f"Unexpected templates dir: {templates_dir}"

        static_dir = manager.get_static_dir()
        print(f"✓ Static dir: {static_dir}")
        assert 'sites/default/static' in static_dir, f"Unexpected static dir: {static_dir}"

        uploads_dir = manager.get_uploads_dir()
        print(f"✓ Uploads dir: {uploads_dir}")
        assert 'sites/default/static/images/uploads' in uploads_dir, f"Unexpected uploads dir: {uploads_dir}"

        # Test site creation
        success, message = manager.create_site('test-site')
        print(f"✓ Create site: {message}")
        assert success, f"Site creation failed: {message}"

        # Test site existence
        exists = manager.site_exists('test-site')
        print(f"✓ Site exists: {exists}")
        assert exists, "Created site should exist"

        # Test getting all sites
        sites = manager.get_all_sites()
        print(f"✓ All sites: {sites}")
        assert 'test-site' in sites, f"Created site not in list: {sites}"

        # Test site structure
        success = manager.ensure_site_structure('another-site')
        print(f"✓ Ensure site structure: {success}")
        assert success, "Failed to ensure site structure"

        # Verify directories were created
        site_path = os.path.join(temp_dir, 'sites', 'another-site')
        templates_path = os.path.join(site_path, 'templates')
        uploads_path = os.path.join(site_path, 'static', 'images', 'uploads')

        assert os.path.isdir(templates_path), f"Templates dir not created: {templates_path}"
        assert os.path.isdir(uploads_path), f"Uploads dir not created: {uploads_path}"
        print(f"✓ Directory structure verified")

        # Test with different site_id
        config_path_site2 = manager.get_config_path('test-site')
        print(f"✓ Config path for 'test-site': {config_path_site2}")
        assert 'sites/test-site/config.json' in config_path_site2, f"Unexpected path: {config_path_site2}"

        # Test template site copying
        success, message = manager.create_site('copied-site', template_site='test-site')
        print(f"✓ Create site with template: {message}")
        assert success, f"Failed to create site with template: {message}"

        print("\n✅ All sites mode tests passed!")
        return True

    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"✓ Cleaned up temp directory")


def test_site_structure():
    """Test ensure_site_structure method."""
    print("\n" + "="*60)
    print("Testing Site Structure Creation")
    print("="*60)

    temp_dir = tempfile.mkdtemp(prefix='wicara_test_struct_')
    print(f"✓ Created temp directory: {temp_dir}")

    try:
        manager = SiteManager(
            sites_dir=os.path.join(temp_dir, 'sites'),
            default_site='default',
            legacy_mode=False
        )

        # Ensure structure for default site
        success = manager.ensure_site_structure()
        print(f"✓ Ensure default site structure: {success}")
        assert success, "Failed to ensure default site structure"

        # Verify all directories exist
        site_path = os.path.join(temp_dir, 'sites', 'default')
        expected_dirs = [
            site_path,
            os.path.join(site_path, 'templates'),
            os.path.join(site_path, 'static'),
            os.path.join(site_path, 'static', 'images'),
            os.path.join(site_path, 'static', 'images', 'uploads'),
        ]

        for expected_dir in expected_dirs:
            assert os.path.isdir(expected_dir), f"Directory not created: {expected_dir}"
            print(f"  ✓ {expected_dir}")

        print("\n✅ Site structure tests passed!")
        return True

    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"✓ Cleaned up temp directory")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("SiteManager Test Suite (ECS-01)")
    print("="*60)

    tests = [
        ("Legacy Mode", test_legacy_mode),
        ("Sites Mode", test_sites_mode),
        ("Site Structure", test_site_structure),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with error:")
            print(f"   {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")

    if failed == 0:
        print("\n🎉 All tests passed successfully!")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
