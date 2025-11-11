"""Cache Manager - Core abstraction layer for cache backends.

Provides unified interface for multiple cache backends with statistics
and monitoring capabilities.
"""

import json
import time
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from cache."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store a value in cache."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        pass

    @abstractmethod
    def clear(self) -> bool:
        """Clear all cached values."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        pass


class CacheManager:
    """Main cache manager with abstraction for multiple backends.

    Provides unified interface for caching with support for multiple
    backends and comprehensive statistics tracking.

    Attributes:
        backend: The active cache backend instance
        stats: Dictionary tracking cache hits, misses, and other metrics
    """

    def __init__(self, backend: CacheBackend):
        """Initialize cache manager with a backend.

        Args:
            backend: A CacheBackend instance (MemoryCache, FileCache, RedisCache)
        """
        self.backend = backend
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'clears': 0,
            'errors': 0,
        }
        self._created_at = datetime.now()
        logger.info(f"CacheManager initialized with {backend.__class__.__name__}")

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from cache.

        Args:
            key: Cache key to retrieve

        Returns:
            Cached value or None if not found
        """
        try:
            value = self.backend.get(key)
            if value is not None:
                self.stats['hits'] += 1
                logger.debug(f"Cache hit: {key}")
            else:
                self.stats['misses'] += 1
                logger.debug(f"Cache miss: {key}")
            return value
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Cache get error for key '{key}': {str(e)}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store a value in cache.

        Args:
            key: Cache key to use
            value: Value to cache
            ttl: Time to live in seconds (None = no expiration)

        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.backend.set(key, value, ttl)
            if result:
                self.stats['sets'] += 1
                ttl_str = f" (TTL: {ttl}s)" if ttl else ""
                logger.debug(f"Cache set: {key}{ttl_str}")
            return result
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Cache set error for key '{key}': {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """Delete a value from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.backend.delete(key)
            if result:
                self.stats['deletes'] += 1
                logger.debug(f"Cache delete: {key}")
            return result
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Cache delete error for key '{key}': {str(e)}")
            return False

    def clear(self) -> bool:
        """Clear all cached values.

        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.backend.clear()
            if result:
                self.stats['clears'] += 1
                logger.info("Cache cleared")
            return result
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Cache clear error: {str(e)}")
            return False

    def exists(self, key: str) -> bool:
        """Check if a key exists in cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists, False otherwise
        """
        try:
            return self.backend.exists(key)
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Cache exists error for key '{key}': {str(e)}")
            return False

    def get_or_set(self, key: str, factory, ttl: Optional[int] = None) -> Any:
        """Get value from cache or compute and cache it.

        Args:
            key: Cache key
            factory: Callable that produces the value if not cached
            ttl: Time to live in seconds

        Returns:
            Cached value or newly computed value
        """
        value = self.get(key)
        if value is None:
            value = factory()
            self.set(key, value, ttl)
        return value

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics and metrics.

        Returns:
            Dictionary with cache statistics including:
            - hits: Number of cache hits
            - misses: Number of cache misses
            - hit_rate: Hit rate percentage
            - sets: Number of cache sets
            - deletes: Number of deletions
            - clears: Number of full clears
            - errors: Number of errors
            - uptime: Time since cache manager creation
            - backend_stats: Backend-specific statistics
        """
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (
            (self.stats['hits'] / total_requests * 100)
            if total_requests > 0
            else 0
        )
        uptime = datetime.now() - self._created_at

        stats = {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'hit_rate': round(hit_rate, 2),
            'sets': self.stats['sets'],
            'deletes': self.stats['deletes'],
            'clears': self.stats['clears'],
            'errors': self.stats['errors'],
            'uptime_seconds': int(uptime.total_seconds()),
            'created_at': self._created_at.isoformat(),
            'backend': self.backend.__class__.__name__,
        }

        # Add backend-specific statistics
        try:
            backend_stats = self.backend.get_stats()
            stats['backend_stats'] = backend_stats
        except Exception as e:
            logger.warning(f"Could not get backend stats: {str(e)}")

        return stats

    def reset_stats(self) -> None:
        """Reset cache statistics."""
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'clears': 0,
            'errors': 0,
        }
        self._created_at = datetime.now()
        logger.info("Cache statistics reset")

    def get_health(self) -> Dict[str, Any]:
        """Get cache health status.

        Returns:
            Dictionary with health information including:
            - status: 'healthy' or 'degraded'
            - error_rate: Percentage of operations that failed
            - recommendations: List of optimization suggestions
        """
        total_ops = (
            self.stats['hits'] + self.stats['misses'] + self.stats['sets']
            + self.stats['deletes']
        )
        error_rate = (
            (self.stats['errors'] / total_ops * 100)
            if total_ops > 0
            else 0
        )

        status = 'healthy' if error_rate < 1 else 'degraded'
        recommendations = []

        stats = self.get_stats()
        if stats['hit_rate'] < 50:
            recommendations.append(
                'Low cache hit rate. Consider adjusting cache TTL or key strategy.'
            )
        if error_rate > 1:
            recommendations.append(
                'High error rate. Check backend storage and permissions.'
            )

        return {
            'status': status,
            'error_rate': round(error_rate, 2),
            'total_operations': total_ops,
            'recommendations': recommendations,
        }
