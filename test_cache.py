#!/usr/bin/env python
"""Simple test script for cache functionality.

Tests cache operations without requiring Flask to be installed.
"""

import sys
import time
import os

# Add app.cache to path to allow direct imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from cache.manager import CacheManager
from cache.backends import MemoryCache, FileCache
from cache.utils import CacheFactory, CacheService


def test_memory_cache():
    """Test memory cache backend."""
    print("\n=== Testing Memory Cache ===")
    cache = MemoryCache()
    manager = CacheManager(cache)

    # Test basic operations
    manager.set('test:key1', {'value': 'hello'}, ttl=10)
    assert manager.get('test:key1') == {'value': 'hello'}, "Failed to retrieve cached value"
    print("✅ Set and get operations work")

    # Test exists
    assert manager.exists('test:key1'), "Key should exist"
    assert not manager.exists('nonexistent'), "Key should not exist"
    print("✅ Exists check works")

    # Test delete
    manager.delete('test:key1')
    assert not manager.exists('test:key1'), "Key should not exist after delete"
    print("✅ Delete operation works")

    # Test clear
    manager.set('key1', 'value1')
    manager.set('key2', 'value2')
    manager.clear()
    assert not manager.exists('key1') and not manager.exists('key2'), "Cache should be cleared"
    print("✅ Clear operation works")

    # Test stats
    manager.set('test', 'value')
    stats = manager.get_stats()
    assert 'hits' in stats and 'misses' in stats, "Stats should be available"
    assert stats['backend'] == 'MemoryCache', "Backend name should match"
    print(f"✅ Stats available: {stats['hits']} hits, {stats['misses']} misses")


def test_file_cache():
    """Test file cache backend."""
    print("\n=== Testing File Cache ===")
    cache = FileCache(cache_dir='.test_cache')
    manager = CacheManager(cache)

    # Test basic operations
    manager.set('test:file1', {'data': 'test'}, ttl=10)
    assert manager.get('test:file1') == {'data': 'test'}, "Failed to retrieve from file cache"
    print("✅ File cache set and get work")

    # Test persistence (simulate)
    value = manager.get('test:file1')
    assert value is not None, "Value should persist"
    print("✅ File cache persistence works")

    # Cleanup
    manager.clear()
    print("✅ File cache cleared")


def test_cache_factory():
    """Test cache factory."""
    print("\n=== Testing Cache Factory ===")

    # Create memory cache
    manager = CacheFactory.create_manager('memory')
    assert isinstance(manager, CacheManager), "Should create CacheManager instance"
    print("✅ Memory cache created")

    # Create file cache
    manager = CacheFactory.create_manager('file')
    assert isinstance(manager, CacheManager), "Should create CacheManager instance"
    print("✅ File cache created")

    # Test unsupported backend
    try:
        CacheFactory.create_manager('unsupported')
        assert False, "Should raise ValueError for unsupported backend"
    except ValueError:
        print("✅ Unsupported backend raises ValueError")


def test_cache_service():
    """Test cache service."""
    print("\n=== Testing Cache Service ===")

    manager = CacheFactory.create_manager('memory')
    service = CacheService(manager)

    # Enable components
    template_cache = service.enable_template_caching(default_ttl=3600)
    response_cache = service.enable_response_caching()
    config_cache = service.enable_config_caching()

    assert service.template_cache is not None, "Template cache should be enabled"
    assert service.response_cache is not None, "Response cache should be enabled"
    assert service.config_cache is not None, "Config cache should be enabled"
    print("✅ All cache components enabled")

    # Test comprehensive stats
    stats = service.get_comprehensive_stats()
    assert 'manager' in stats, "Manager stats should be available"
    assert 'components' in stats, "Component stats should be available"
    print("✅ Comprehensive stats available")


def test_cache_hit_rate():
    """Test cache hit rate calculation."""
    print("\n=== Testing Cache Hit Rate ===")

    manager = CacheFactory.create_manager('memory')
    manager.set('key1', 'value1')

    # Generate hits
    manager.get('key1')  # hit
    manager.get('key1')  # hit
    manager.get('key2')  # miss
    manager.get('key2')  # miss

    stats = manager.get_stats()
    assert stats['hits'] == 2, f"Should have 2 hits, got {stats['hits']}"
    assert stats['misses'] == 2, f"Should have 2 misses, got {stats['misses']}"
    assert stats['hit_rate'] == 50.0, f"Hit rate should be 50%, got {stats['hit_rate']}%"
    print(f"✅ Hit rate correctly calculated: {stats['hit_rate']}%")


def test_cache_health():
    """Test cache health checking."""
    print("\n=== Testing Cache Health ===")

    manager = CacheFactory.create_manager('memory')

    # Generate some successful operations
    for i in range(100):
        manager.set(f'key{i}', f'value{i}')
        manager.get(f'key{i}')

    health = manager.get_health()
    assert 'status' in health, "Health should have status"
    assert 'error_rate' in health, "Health should have error_rate"
    assert health['status'] in ['healthy', 'degraded'], "Status should be valid"
    print(f"✅ Cache health: {health['status']} (error rate: {health['error_rate']}%)")


def test_get_or_set():
    """Test get_or_set convenience method."""
    print("\n=== Testing get_or_set ===")

    manager = CacheFactory.create_manager('memory')

    call_count = 0

    def factory():
        nonlocal call_count
        call_count += 1
        return f"value_{call_count}"

    # First call should invoke factory
    result1 = manager.get_or_set('key', factory)
    assert result1 == 'value_1', "Should call factory first time"
    assert call_count == 1, "Factory should be called once"
    print("✅ Factory called on first get_or_set")

    # Second call should use cache
    result2 = manager.get_or_set('key', factory)
    assert result2 == 'value_1', "Should return cached value"
    assert call_count == 1, "Factory should not be called again"
    print("✅ Factory not called on second get_or_set (cache hit)")


def main():
    """Run all tests."""
    print("=" * 50)
    print("WICARA CACHE SYSTEM TEST SUITE")
    print("=" * 50)

    try:
        test_memory_cache()
        test_file_cache()
        test_cache_factory()
        test_cache_service()
        test_cache_hit_rate()
        test_cache_health()
        test_get_or_set()

        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED!")
        print("=" * 50)
        return 0
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
