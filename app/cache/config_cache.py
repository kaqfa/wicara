"""Configuration Caching - Cached wrapper for ConfigManager.

Provides automatic cache invalidation when config.json changes,
reducing JSON parsing overhead.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from .manager import CacheManager

logger = logging.getLogger(__name__)


class CachedConfigManager:
    """Wraps ConfigManager with automatic cache invalidation.

    Caches parsed JSON configuration and automatically invalidates
    cache when the config file is modified.

    Features:
    - Automatic file change detection via mtime
    - Configurable cache TTL
    - Manual cache invalidation
    - Cache statistics tracking
    """

    def __init__(
        self,
        cache_manager: CacheManager,
        config_path: str = 'config.json',
        cache_ttl: int = 300,  # 5 minutes default
    ):
        """Initialize cached config manager.

        Args:
            cache_manager: CacheManager instance
            config_path: Path to config.json file
            cache_ttl: Cache time-to-live in seconds
        """
        self.cache_manager = cache_manager
        self.config_path = Path(config_path)
        self.cache_ttl = cache_ttl
        self._file_mtime: Optional[float] = None
        self._cache_key = 'config:main'
        self._load_method = None

        logger.debug(f"CachedConfigManager initialized for {config_path}")

    def set_load_method(self, load_func):
        """Set the actual config load function.

        Args:
            load_func: Callable that loads and validates config
        """
        self._load_method = load_func

    def _get_file_mtime(self) -> Optional[float]:
        """Get config file modification time."""
        try:
            if self.config_path.exists():
                return self.config_path.stat().st_mtime
            return None
        except Exception as e:
            logger.warning(f"Could not get file mtime: {str(e)}")
            return None

    def _file_changed(self) -> bool:
        """Check if config file has changed.

        Returns:
            True if file was modified or doesn't exist in cache
        """
        current_mtime = self._get_file_mtime()

        if self._file_mtime is None:
            self._file_mtime = current_mtime
            return True

        if current_mtime is None:
            return True

        if current_mtime != self._file_mtime:
            logger.info("Config file modified, invalidating cache")
            self._file_mtime = current_mtime
            return True

        return False

    def load(self) -> Optional[Dict[str, Any]]:
        """Load configuration with caching.

        Checks if file has changed since last load. If unchanged,
        returns cached value. If changed, reloads and recaches.

        Returns:
            Configuration dictionary or None if load fails
        """
        # Check if file has changed
        if self._file_changed():
            logger.debug("Cache invalidated due to file change")
            self.cache_manager.delete(self._cache_key)

        # Try to get from cache
        cached_config = self.cache_manager.get(self._cache_key)
        if cached_config is not None:
            logger.debug("Config loaded from cache")
            return cached_config

        # Load from disk
        if self._load_method is None:
            logger.error("Load method not set for CachedConfigManager")
            return None

        logger.debug("Loading config from disk")
        config = self._load_method()

        if config is not None:
            self.cache_manager.set(self._cache_key, config, self.cache_ttl)

        return config

    def invalidate(self) -> None:
        """Manually invalidate config cache.

        Call this after updating config programmatically.
        """
        self.cache_manager.delete(self._cache_key)
        self._file_mtime = self._get_file_mtime()
        logger.info("Config cache manually invalidated")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        return {
            'config_cache_ttl': self.cache_ttl,
            'config_path': str(self.config_path),
            'file_exists': self.config_path.exists(),
            'file_mtime': self._file_mtime,
        }
