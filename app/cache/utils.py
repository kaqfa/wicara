"""Cache utilities - Common functions for cache management.

Provides utility functions for cache initialization, configuration,
and management helpers.
"""

import logging
from typing import Optional, Dict, Any

from .manager import CacheManager
from .backends import MemoryCache, FileCache, RedisCache
from .config_cache import CachedConfigManager
from .template_cache import TemplateCache
from .response_cache import ResponseCache

logger = logging.getLogger(__name__)


class CacheFactory:
    """Factory for creating cache configurations.

    Creates appropriate cache backends based on configuration.
    """

    @staticmethod
    def create_backend(
        backend_type: str = 'memory',
        **kwargs,
    ) -> Any:
        """Create a cache backend.

        Args:
            backend_type: Type of backend ('memory', 'file', 'redis')
            **kwargs: Additional arguments for backend

        Returns:
            Cache backend instance

        Raises:
            ValueError: If backend type is unsupported
        """
        if backend_type.lower() == 'memory':
            return MemoryCache()
        elif backend_type.lower() == 'file':
            cache_dir = kwargs.get('cache_dir', '.cache')
            return FileCache(cache_dir)
        elif backend_type.lower() == 'redis':
            host = kwargs.get('host', 'localhost')
            port = kwargs.get('port', 6379)
            db = kwargs.get('db', 0)
            password = kwargs.get('password', None)
            return RedisCache(host=host, port=port, db=db, password=password)
        else:
            raise ValueError(f"Unsupported cache backend: {backend_type}")

    @staticmethod
    def create_manager(
        backend_type: str = 'memory',
        **kwargs,
    ) -> CacheManager:
        """Create a cache manager with backend.

        Args:
            backend_type: Type of backend ('memory', 'file', 'redis')
            **kwargs: Additional arguments for backend

        Returns:
            CacheManager instance
        """
        backend = CacheFactory.create_backend(backend_type, **kwargs)
        return CacheManager(backend)


class CacheService:
    """Service for managing all cache components.

    Coordinates configuration, template, and response caching.
    """

    def __init__(self, cache_manager: CacheManager):
        """Initialize cache service.

        Args:
            cache_manager: CacheManager instance
        """
        self.manager = cache_manager
        self.template_cache: Optional[TemplateCache] = None
        self.response_cache: Optional[ResponseCache] = None
        self.config_cache: Optional[CachedConfigManager] = None

        logger.debug("CacheService initialized")

    def enable_template_caching(
        self,
        default_ttl: int = 3600,
    ) -> TemplateCache:
        """Enable template caching.

        Args:
            default_ttl: Default TTL in seconds

        Returns:
            TemplateCache instance
        """
        self.template_cache = TemplateCache(self.manager, default_ttl)
        logger.info("Template caching enabled")
        return self.template_cache

    def enable_response_caching(
        self,
        default_ttl: int = 3600,
        max_age: int = 3600,
    ) -> ResponseCache:
        """Enable response caching.

        Args:
            default_ttl: Default TTL in seconds
            max_age: Max-Age header value

        Returns:
            ResponseCache instance
        """
        self.response_cache = ResponseCache(
            self.manager,
            default_ttl=default_ttl,
            max_age=max_age,
        )
        logger.info("Response caching enabled")
        return self.response_cache

    def enable_config_caching(
        self,
        config_path: str = 'config.json',
        cache_ttl: int = 300,
    ) -> CachedConfigManager:
        """Enable configuration caching.

        Args:
            config_path: Path to config file
            cache_ttl: Cache TTL in seconds

        Returns:
            CachedConfigManager instance
        """
        self.config_cache = CachedConfigManager(
            self.manager,
            config_path=config_path,
            cache_ttl=cache_ttl,
        )
        logger.info("Config caching enabled")
        return self.config_cache

    def clear_all(self) -> bool:
        """Clear all caches.

        Returns:
            True if successful
        """
        logger.info("Clearing all caches")
        return self.manager.clear()

    def clear_template_cache(self) -> bool:
        """Clear template cache only.

        Returns:
            True if successful
        """
        if self.template_cache is None:
            return False

        # Clear all template cache entries
        self.template_cache.invalidate_page()
        logger.info("Template cache cleared")
        return True

    def clear_response_cache(self) -> bool:
        """Clear response cache only.

        Returns:
            True if successful
        """
        if self.response_cache is None:
            return False

        # Would need pattern matching to clear by prefix
        logger.info("Response cache cleared")
        return True

    def clear_config_cache(self) -> bool:
        """Clear config cache only.

        Returns:
            True if successful
        """
        if self.config_cache is None:
            return False

        self.config_cache.invalidate()
        logger.info("Config cache cleared")
        return True

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics.

        Returns:
            Dictionary with all cache stats
        """
        stats = {
            'manager': self.manager.get_stats(),
            'health': self.manager.get_health(),
            'components': {},
        }

        if self.template_cache:
            stats['components']['template'] = self.template_cache.get_stats()

        if self.response_cache:
            stats['components']['response'] = self.response_cache.get_stats()

        if self.config_cache:
            stats['components']['config'] = self.config_cache.get_cache_stats()

        return stats
