"""Cache backends - Implementation of different caching strategies.

Provides concrete implementations of cache backends:
- MemoryCache: In-memory caching using Python dictionaries
- FileCache: Disk-based caching using JSON files
- RedisCache: Redis server-based caching (optional)
"""

import os
import json
import pickle
import hashlib
import threading
from pathlib import Path
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import logging

from .manager import CacheBackend

logger = logging.getLogger(__name__)


class MemoryCache(CacheBackend):
    """In-memory cache backend using Python dictionaries.

    Suitable for single-process deployments and caching that doesn't need
    to persist across application restarts.

    Thread-safe for multi-threaded Flask servers.
    """

    def __init__(self):
        """Initialize in-memory cache."""
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        logger.debug("MemoryCache initialized")

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from memory cache."""
        with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]

            # Check expiration
            if entry['expires_at'] and datetime.now() > entry['expires_at']:
                del self._cache[key]
                return None

            return entry['value']

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store a value in memory cache."""
        try:
            with self._lock:
                expires_at = None
                if ttl:
                    expires_at = datetime.now() + timedelta(seconds=ttl)

                self._cache[key] = {
                    'value': value,
                    'expires_at': expires_at,
                    'created_at': datetime.now(),
                }
            return True
        except Exception as e:
            logger.error(f"MemoryCache set error: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """Delete a value from memory cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> bool:
        """Clear all cached values."""
        with self._lock:
            self._cache.clear()
            return True

    def exists(self, key: str) -> bool:
        """Check if a key exists in memory cache."""
        with self._lock:
            if key not in self._cache:
                return False

            entry = self._cache[key]
            if entry['expires_at'] and datetime.now() > entry['expires_at']:
                del self._cache[key]
                return False

            return True

    def get_stats(self) -> Dict[str, Any]:
        """Get memory cache statistics."""
        with self._lock:
            total_size = sum(
                len(pickle.dumps(entry['value']))
                for entry in self._cache.values()
            )
            expired_count = sum(
                1
                for entry in self._cache.values()
                if entry['expires_at'] and datetime.now() > entry['expires_at']
            )

            return {
                'type': 'memory',
                'total_keys': len(self._cache),
                'estimated_size_bytes': total_size,
                'expired_keys': expired_count,
            }

    def cleanup_expired(self) -> int:
        """Remove expired entries from cache.

        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = [
                key
                for key, entry in self._cache.items()
                if entry['expires_at'] and datetime.now() > entry['expires_at']
            ]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)


class FileCache(CacheBackend):
    """File-based cache backend using JSON files on disk.

    Suitable for persistent caching across application restarts.
    Slower than MemoryCache but provides durability.

    Stores each cache entry as a separate JSON file for simplicity
    and to avoid lock contention.
    """

    def __init__(self, cache_dir: str = None):
        """Initialize file-based cache.

        Args:
            cache_dir: Directory to store cache files. Defaults to .cache
        """
        self.cache_dir = Path(cache_dir or '.cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        logger.debug(f"FileCache initialized at {self.cache_dir}")

    def _get_cache_path(self, key: str) -> Path:
        """Get file path for cache key.

        Args:
            key: Cache key

        Returns:
            Path object for cache file
        """
        # Create safe filename from key
        safe_key = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{safe_key}.json"

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from file cache."""
        try:
            cache_path = self._get_cache_path(key)
            if not cache_path.exists():
                return None

            with open(cache_path, 'r') as f:
                entry = json.load(f)

            # Check expiration
            if entry.get('expires_at'):
                expires_at = datetime.fromisoformat(entry['expires_at'])
                if datetime.now() > expires_at:
                    cache_path.unlink()  # Delete expired file
                    return None

            return entry['value']
        except Exception as e:
            logger.debug(f"FileCache get error for key '{key}': {str(e)}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store a value in file cache."""
        try:
            cache_path = self._get_cache_path(key)

            expires_at = None
            if ttl:
                expires_at = (datetime.now() + timedelta(seconds=ttl)).isoformat()

            entry = {
                'key': key,
                'value': value,
                'expires_at': expires_at,
                'created_at': datetime.now().isoformat(),
            }

            with self._lock:
                with open(cache_path, 'w') as f:
                    json.dump(entry, f)
            return True
        except Exception as e:
            logger.error(f"FileCache set error: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """Delete a value from file cache."""
        try:
            cache_path = self._get_cache_path(key)
            if cache_path.exists():
                with self._lock:
                    cache_path.unlink()
                return True
            return False
        except Exception as e:
            logger.error(f"FileCache delete error: {str(e)}")
            return False

    def clear(self) -> bool:
        """Clear all cached values."""
        try:
            with self._lock:
                for file in self.cache_dir.glob('*.json'):
                    file.unlink()
            return True
        except Exception as e:
            logger.error(f"FileCache clear error: {str(e)}")
            return False

    def exists(self, key: str) -> bool:
        """Check if a key exists in file cache."""
        try:
            cache_path = self._get_cache_path(key)
            if not cache_path.exists():
                return False

            with open(cache_path, 'r') as f:
                entry = json.load(f)

            if entry.get('expires_at'):
                expires_at = datetime.fromisoformat(entry['expires_at'])
                if datetime.now() > expires_at:
                    cache_path.unlink()
                    return False

            return True
        except Exception as e:
            logger.debug(f"FileCache exists error: {str(e)}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get file cache statistics."""
        try:
            cache_files = list(self.cache_dir.glob('*.json'))
            total_size = sum(f.stat().st_size for f in cache_files)

            expired_count = 0
            for file in cache_files:
                try:
                    with open(file, 'r') as f:
                        entry = json.load(f)
                    if entry.get('expires_at'):
                        expires_at = datetime.fromisoformat(entry['expires_at'])
                        if datetime.now() > expires_at:
                            expired_count += 1
                except:
                    pass

            return {
                'type': 'file',
                'cache_directory': str(self.cache_dir),
                'total_keys': len(cache_files),
                'total_size_bytes': total_size,
                'expired_keys': expired_count,
            }
        except Exception as e:
            logger.error(f"FileCache stats error: {str(e)}")
            return {'type': 'file', 'error': str(e)}

    def cleanup_expired(self) -> int:
        """Remove expired entries from file cache.

        Returns:
            Number of entries removed
        """
        removed_count = 0
        try:
            for file in self.cache_dir.glob('*.json'):
                try:
                    with open(file, 'r') as f:
                        entry = json.load(f)
                    if entry.get('expires_at'):
                        expires_at = datetime.fromisoformat(entry['expires_at'])
                        if datetime.now() > expires_at:
                            with self._lock:
                                file.unlink()
                            removed_count += 1
                except:
                    pass
        except Exception as e:
            logger.error(f"FileCache cleanup error: {str(e)}")

        return removed_count


class RedisCache(CacheBackend):
    """Redis-based cache backend.

    Suitable for distributed deployments and high-performance caching.
    Requires redis-py library: pip install redis

    This is an optional backend for advanced deployments.
    """

    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
    ):
        """Initialize Redis cache.

        Args:
            host: Redis server hostname
            port: Redis server port
            db: Redis database number
            password: Redis password (optional)
        """
        try:
            import redis
            self.redis = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
            )
            # Test connection
            self.redis.ping()
            self.redis_available = True
            logger.info(f"RedisCache initialized at {host}:{port}")
        except ImportError:
            logger.warning(
                "redis-py not installed. RedisCache requires: pip install redis"
            )
            self.redis_available = False
        except Exception as e:
            logger.error(f"RedisCache connection error: {str(e)}")
            self.redis_available = False

    def _check_available(self) -> bool:
        """Check if Redis is available."""
        if not self.redis_available:
            logger.error("Redis not available. Falling back to no-op.")
            return False
        return True

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from Redis cache."""
        if not self._check_available():
            return None

        try:
            value = self.redis.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            logger.error(f"RedisCache get error: {str(e)}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store a value in Redis cache."""
        if not self._check_available():
            return False

        try:
            self.redis.set(key, json.dumps(value), ex=ttl)
            return True
        except Exception as e:
            logger.error(f"RedisCache set error: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """Delete a value from Redis cache."""
        if not self._check_available():
            return False

        try:
            return bool(self.redis.delete(key))
        except Exception as e:
            logger.error(f"RedisCache delete error: {str(e)}")
            return False

    def clear(self) -> bool:
        """Clear all cached values."""
        if not self._check_available():
            return False

        try:
            self.redis.flushdb()
            return True
        except Exception as e:
            logger.error(f"RedisCache clear error: {str(e)}")
            return False

    def exists(self, key: str) -> bool:
        """Check if a key exists in Redis cache."""
        if not self._check_available():
            return False

        try:
            return bool(self.redis.exists(key))
        except Exception as e:
            logger.error(f"RedisCache exists error: {str(e)}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics."""
        if not self._check_available():
            return {'type': 'redis', 'available': False}

        try:
            info = self.redis.info()
            return {
                'type': 'redis',
                'used_memory_human': info.get('used_memory_human', 'N/A'),
                'connected_clients': info.get('connected_clients', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
            }
        except Exception as e:
            logger.error(f"RedisCache stats error: {str(e)}")
            return {'type': 'redis', 'error': str(e)}
