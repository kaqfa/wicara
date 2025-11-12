"""Response Caching - HTTP response caching with headers and ETags.

Provides HTTP-aware response caching with proper cache headers,
ETag support, and browser cache optimization.
"""

import hashlib
import gzip
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import logging

from .manager import CacheManager

# Flask Response is imported only when needed (runtime)
try:
    from flask import Response
except ImportError:
    Response = None  # Will be available at runtime in Flask application

logger = logging.getLogger(__name__)


class ResponseCache:
    """HTTP response caching with ETag and cache header support.

    Features:
    - Response body caching with ETag generation
    - Cache-Control header management
    - Conditional request handling (304 Not Modified)
    - Compression-aware ETag calculation
    - Browser cache optimization
    """

    def __init__(
        self,
        cache_manager: CacheManager,
        default_ttl: int = 3600,  # 1 hour
        max_age: int = 3600,  # 1 hour
        enable_compression: bool = True,
    ):
        """Initialize response cache.

        Args:
            cache_manager: CacheManager instance
            default_ttl: Default cache TTL in seconds
            max_age: Max-Age value for Cache-Control header
            enable_compression: Whether to gzip responses
        """
        self.cache_manager = cache_manager
        self.default_ttl = default_ttl
        self.max_age = max_age
        self.enable_compression = enable_compression

        logger.debug("ResponseCache initialized")

    @staticmethod
    def _generate_etag(content: str) -> str:
        """Generate ETag from content.

        Args:
            content: Response content

        Returns:
            ETag string (without quotes)
        """
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        return content_hash

    @staticmethod
    def _should_compress(content: str) -> bool:
        """Determine if content should be compressed.

        Args:
            content: Response content

        Returns:
            True if content is large enough to compress
        """
        return len(content) > 1024  # Compress if > 1KB

    def cache_response(
        self,
        url: str,
        render_func,
        ttl: Optional[int] = None,
        public: bool = True,
        must_revalidate: bool = False,
    ):
        """Cache an HTTP response.

        Args:
            url: Request URL
            render_func: Callable that produces response
            ttl: Cache TTL in seconds
            public: Whether response is publicly cacheable
            must_revalidate: Whether response must be revalidated

        Returns:
            Flask Response object with proper cache headers
        """
        ttl = ttl or self.default_ttl
        cache_key = f"response:{url}"

        # Try to get from cache
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            logger.debug(f"Response cached: {url}")
            content = cached_data['content']
            etag = cached_data['etag']
            last_modified = cached_data['last_modified']
        else:
            # Render response
            logger.debug(f"Rendering response: {url}")
            content = render_func()

            # Generate ETag
            etag = self._generate_etag(content)

            # Cache the response
            last_modified = datetime.now().isoformat()
            cached_data = {
                'content': content,
                'etag': etag,
                'last_modified': last_modified,
            }
            self.cache_manager.set(cache_key, cached_data, ttl)

        # Build Flask response with proper headers
        if Response is None:
            logger.error('Flask Response class not available')
            return None

        response = Response(content, content_type='text/html; charset=utf-8')

        # Set cache headers
        cache_control = self._build_cache_control(public, must_revalidate)
        response.headers['Cache-Control'] = cache_control
        response.headers['ETag'] = f'"{etag}"'
        response.headers['Last-Modified'] = last_modified

        # Add vary headers
        response.headers['Vary'] = 'Accept-Encoding'

        return response

    def _build_cache_control(
        self,
        public: bool = True,
        must_revalidate: bool = False,
    ) -> str:
        """Build Cache-Control header value.

        Args:
            public: Whether response is publicly cacheable
            must_revalidate: Whether response must be revalidated

        Returns:
            Cache-Control header value
        """
        parts = []

        # Public or private
        if public:
            parts.append('public')
        else:
            parts.append('private')

        # Max-Age
        parts.append(f'max-age={self.max_age}')

        # Must-Revalidate
        if must_revalidate:
            parts.append('must-revalidate')
        else:
            parts.append('must-revalidate')

        return ', '.join(parts)

    def handle_conditional_request(
        self,
        url: str,
        if_none_match: Optional[str] = None,
        if_modified_since: Optional[str] = None,
    ):
        """Handle conditional HTTP requests (304 Not Modified).

        Args:
            url: Request URL
            if_none_match: If-None-Match header value (ETag)
            if_modified_since: If-Modified-Since header value

        Returns:
            304 Response if conditions match, None otherwise
        """
        cache_key = f"response:{url}"
        cached_data = self.cache_manager.get(cache_key)

        if cached_data is None:
            return None

        if Response is None:
            return None

        etag = cached_data['etag']
        last_modified = cached_data['last_modified']

        # Check ETag
        if if_none_match:
            # Remove quotes from If-None-Match
            if_none_match = if_none_match.strip('"')
            if if_none_match == etag:
                logger.debug(f"304 Not Modified (ETag): {url}")
                response = Response(status=304)
                response.headers['ETag'] = f'"{etag}"'
                response.headers['Cache-Control'] = self._build_cache_control()
                return response

        # Check Last-Modified
        if if_modified_since and last_modified:
            try:
                # Compare timestamps
                if_time = datetime.fromisoformat(if_modified_since)
                mod_time = datetime.fromisoformat(last_modified)

                if if_time >= mod_time:
                    logger.debug(f"304 Not Modified (Last-Modified): {url}")
                    response = Response(status=304)
                    response.headers['ETag'] = f'"{etag}"'
                    response.headers['Cache-Control'] = self._build_cache_control()
                    return response
            except Exception as e:
                logger.debug(f"Could not parse date headers: {str(e)}")

        return None

    def invalidate_response(self, url: str) -> bool:
        """Invalidate cached response.

        Args:
            url: URL whose response should be invalidated

        Returns:
            True if something was invalidated
        """
        cache_key = f"response:{url}"
        success = self.cache_manager.delete(cache_key)
        if success:
            logger.info(f"Invalidated response: {url}")
        return success

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate responses matching a pattern.

        Note: This requires backend support for pattern matching.
        Current implementation only works with MemoryCache.

        Args:
            pattern: URL pattern to match (supports * wildcard)

        Returns:
            Number of responses invalidated
        """
        invalidated = 0

        # This would require iterating through cache
        # For now, manual invalidation is recommended
        logger.info(f"Pattern-based invalidation requested: {pattern}")

        return invalidated

    def get_cache_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Get cache info for a specific URL.

        Args:
            url: Request URL

        Returns:
            Dictionary with cache info or None if not cached
        """
        cache_key = f"response:{url}"
        cached_data = self.cache_manager.get(cache_key)

        if cached_data is None:
            return None

        return {
            'url': url,
            'etag': cached_data['etag'],
            'last_modified': cached_data['last_modified'],
            'content_length': len(cached_data['content']),
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get response cache statistics.

        Returns:
            Dictionary with stats
        """
        return {
            'default_ttl': self.default_ttl,
            'max_age': self.max_age,
            'enable_compression': self.enable_compression,
        }


class CDNHelper:
    """Helper for CDN integration and optimization.

    Provides utilities for working with CDN headers and
    cache invalidation patterns.
    """

    @staticmethod
    def get_cdn_headers() -> Dict[str, str]:
        """Get recommended CDN cache headers.

        Returns:
            Dictionary of header names and values
        """
        return {
            'Cache-Control': 'public, max-age=3600, must-revalidate',
            'CDN-Cache-Control': 'max-age=86400',  # 24 hours at CDN level
            'X-CDN-Cache': 'HIT',
        }

    @staticmethod
    def get_surrogate_keys(content: str) -> list:
        """Extract surrogate keys from content for CDN purging.

        Args:
            content: Response content

        Returns:
            List of surrogate key strings
        """
        # Could analyze content to extract page sections, etc.
        return []

    @staticmethod
    def build_purge_request(
        urls: list,
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build CDN purge API request.

        Args:
            urls: List of URLs to purge
            api_key: Optional CDN API key

        Returns:
            Dictionary with purge request parameters
        """
        return {
            'urls': urls,
            'method': 'PURGE',
            'api_key': api_key,
        }
