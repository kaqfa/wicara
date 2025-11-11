"""Template Caching - Fragment and full template caching.

Provides caching for Jinja2 template rendering with dependency tracking
and selective cache warming.
"""

import hashlib
from typing import Optional, Dict, Any, Callable, List
import logging

from .manager import CacheManager

logger = logging.getLogger(__name__)


class TemplateCacheKey:
    """Helper class for generating consistent template cache keys."""

    @staticmethod
    def fragment(template_name: str, context_hash: str) -> str:
        """Generate cache key for template fragment.

        Args:
            template_name: Name of template
            context_hash: Hash of template context

        Returns:
            Cache key string
        """
        return f"template:fragment:{template_name}:{context_hash}"

    @staticmethod
    def full_page(url: str, context_hash: str) -> str:
        """Generate cache key for full page.

        Args:
            url: Page URL
            context_hash: Hash of page context

        Returns:
            Cache key string
        """
        return f"template:page:{url}:{context_hash}"

    @staticmethod
    def context_hash(context: Dict[str, Any]) -> str:
        """Generate consistent hash of template context.

        Args:
            context: Template context dictionary

        Returns:
            Hex digest hash of context
        """
        # Create stable JSON representation for hashing
        import json
        try:
            context_str = json.dumps(context, sort_keys=True, default=str)
            return hashlib.sha256(context_str.encode()).hexdigest()
        except Exception as e:
            logger.warning(f"Could not hash context: {str(e)}")
            return "unknown"


class TemplateCache:
    """Template fragment and page caching system.

    Features:
    - Fragment-level caching for reusable components
    - Full page caching for static content
    - Dependency tracking for cache invalidation
    - Context-aware cache keys
    - Selective cache warming
    """

    def __init__(
        self,
        cache_manager: CacheManager,
        default_ttl: int = 3600,  # 1 hour
    ):
        """Initialize template cache.

        Args:
            cache_manager: CacheManager instance
            default_ttl: Default cache TTL in seconds
        """
        self.cache_manager = cache_manager
        self.default_ttl = default_ttl
        self._dependencies: Dict[str, List[str]] = {}
        self._render_funcs: Dict[str, Callable] = {}

        logger.debug("TemplateCache initialized")

    def register_render_function(
        self,
        name: str,
        func: Callable,
    ) -> None:
        """Register a render function for cache warming.

        Args:
            name: Name of the render function
            func: Callable that performs rendering
        """
        self._render_funcs[name] = func
        logger.debug(f"Registered render function: {name}")

    def cache_fragment(
        self,
        template_name: str,
        context: Dict[str, Any],
        render_func: Callable,
        ttl: Optional[int] = None,
        dependencies: Optional[List[str]] = None,
    ) -> str:
        """Cache a template fragment.

        Args:
            template_name: Name of template
            context: Template context dictionary
            render_func: Callable that renders the template
            ttl: Cache TTL in seconds
            dependencies: List of cache keys this depends on

        Returns:
            Rendered template HTML
        """
        ttl = ttl or self.default_ttl
        context_hash = TemplateCacheKey.context_hash(context)
        cache_key = TemplateCacheKey.fragment(template_name, context_hash)

        # Try to get from cache
        cached = self.cache_manager.get(cache_key)
        if cached is not None:
            logger.debug(f"Template fragment cached: {template_name}")
            return cached

        # Render and cache
        logger.debug(f"Rendering template fragment: {template_name}")
        rendered = render_func(context)
        self.cache_manager.set(cache_key, rendered, ttl)

        # Track dependencies
        if dependencies:
            self._dependencies[cache_key] = dependencies

        return rendered

    def cache_page(
        self,
        url: str,
        context: Dict[str, Any],
        render_func: Callable,
        ttl: Optional[int] = None,
        dependencies: Optional[List[str]] = None,
    ) -> str:
        """Cache a full page rendering.

        Args:
            url: Page URL/path
            context: Page context dictionary
            render_func: Callable that renders the page
            ttl: Cache TTL in seconds
            dependencies: List of cache keys this depends on

        Returns:
            Rendered page HTML
        """
        ttl = ttl or self.default_ttl
        context_hash = TemplateCacheKey.context_hash(context)
        cache_key = TemplateCacheKey.full_page(url, context_hash)

        # Try to get from cache
        cached = self.cache_manager.get(cache_key)
        if cached is not None:
            logger.debug(f"Page cached: {url}")
            return cached

        # Render and cache
        logger.debug(f"Rendering page: {url}")
        rendered = render_func(context)
        self.cache_manager.set(cache_key, rendered, ttl)

        # Track dependencies
        if dependencies:
            self._dependencies[cache_key] = dependencies

        return rendered

    def invalidate_fragment(
        self,
        template_name: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Invalidate cached template fragment.

        Args:
            template_name: Name of template
            context: Optional context (if provided, only that version is invalidated)

        Returns:
            True if something was invalidated
        """
        if context is not None:
            # Invalidate specific context
            context_hash = TemplateCacheKey.context_hash(context)
            cache_key = TemplateCacheKey.fragment(template_name, context_hash)
            success = self.cache_manager.delete(cache_key)
            if success:
                logger.info(f"Invalidated fragment: {template_name}")
                self._dependencies.pop(cache_key, None)
            return success
        else:
            # Invalidate all versions of template
            prefix = f"template:fragment:{template_name}:"
            invalidated = 0
            for key in list(self._dependencies.keys()):
                if key.startswith(prefix):
                    self.cache_manager.delete(key)
                    self._dependencies.pop(key, None)
                    invalidated += 1

            if invalidated > 0:
                logger.info(f"Invalidated {invalidated} versions of {template_name}")

            return invalidated > 0

    def invalidate_page(
        self,
        url: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Invalidate cached page(s).

        Args:
            url: Optional URL (if provided, only that version is invalidated)
            context: Optional context (if provided, only that version is invalidated)

        Returns:
            True if something was invalidated
        """
        if url is not None and context is not None:
            # Invalidate specific page version
            context_hash = TemplateCacheKey.context_hash(context)
            cache_key = TemplateCacheKey.full_page(url, context_hash)
            success = self.cache_manager.delete(cache_key)
            if success:
                logger.info(f"Invalidated page: {url}")
                self._dependencies.pop(cache_key, None)
            return success
        elif url is not None:
            # Invalidate all versions of page
            prefix = f"template:page:{url}:"
            invalidated = 0
            for key in list(self._dependencies.keys()):
                if key.startswith(prefix):
                    self.cache_manager.delete(key)
                    self._dependencies.pop(key, None)
                    invalidated += 1

            if invalidated > 0:
                logger.info(f"Invalidated {invalidated} versions of page: {url}")

            return invalidated > 0
        else:
            # Invalidate all pages
            invalidated = 0
            for key in list(self._dependencies.keys()):
                if key.startswith("template:page:"):
                    self.cache_manager.delete(key)
                    self._dependencies.pop(key, None)
                    invalidated += 1

            if invalidated > 0:
                logger.info(f"Invalidated {invalidated} cached pages")

            return invalidated > 0

    def invalidate_by_dependency(self, dependency_key: str) -> int:
        """Invalidate all cached items that depend on a key.

        Args:
            dependency_key: Key that invalidation depends on

        Returns:
            Number of items invalidated
        """
        invalidated = 0
        keys_to_invalidate = []

        # Find all items depending on this key
        for cache_key, dependencies in self._dependencies.items():
            if dependency_key in dependencies:
                keys_to_invalidate.append(cache_key)

        # Invalidate them
        for key in keys_to_invalidate:
            self.cache_manager.delete(key)
            self._dependencies.pop(key, None)
            invalidated += 1

        if invalidated > 0:
            logger.info(
                f"Invalidated {invalidated} items depending on {dependency_key}"
            )

        return invalidated

    def warm_cache(self) -> Dict[str, Any]:
        """Warm cache with registered render functions.

        Returns:
            Dictionary with warming results
        """
        logger.info("Starting cache warming")
        results = {
            'total': len(self._render_funcs),
            'successful': 0,
            'failed': 0,
            'errors': [],
        }

        for name, func in self._render_funcs.items():
            try:
                logger.debug(f"Warming cache for: {name}")
                func()
                results['successful'] += 1
            except Exception as e:
                logger.error(f"Cache warming failed for {name}: {str(e)}")
                results['failed'] += 1
                results['errors'].append({'function': name, 'error': str(e)})

        logger.info(
            f"Cache warming complete: {results['successful']}/{results['total']} successful"
        )
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get template cache statistics.

        Returns:
            Dictionary with stats
        """
        return {
            'registered_render_functions': len(self._render_funcs),
            'tracked_dependencies': len(self._dependencies),
            'default_ttl': self.default_ttl,
        }
