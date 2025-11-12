"""Cache module for Wicara CMS.

Provides abstraction layer for multiple caching backends with statistics
and monitoring capabilities.
"""

from .manager import CacheManager, CacheBackend
from .backends import MemoryCache, FileCache, RedisCache

__all__ = [
    'CacheManager',
    'CacheBackend',
    'MemoryCache',
    'FileCache',
    'RedisCache',
]
