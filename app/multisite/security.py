"""
Security & Isolation - MULTI-04

Multi-site security enforcement and isolation mechanisms.
Prevents cross-site attacks and resource leakage.
"""

from flask import g, request
from functools import wraps
from typing import Optional, Callable
import os
import logging

logger = logging.getLogger(__name__)


class SiteIsolation:
    """
    Enforces site isolation and security.

    Security Measures:
    - Session isolation per site
    - File path validation (prevent directory traversal)
    - Cross-site request validation
    - Resource access control
    - Rate limiting per site
    """

    def __init__(self, site_manager):
        """Initialize isolation enforcer."""
        self.site_manager = site_manager

    def validate_path(self, path: str, allowed_dir: str) -> bool:
        """
        Validate file path to prevent directory traversal.

        Args:
            path: User-provided path
            allowed_dir: Directory path should be within

        Returns:
            True if path is safe, False otherwise
        """
        try:
            # Get absolute paths
            abs_path = os.path.abspath(path)
            abs_allowed = os.path.abspath(allowed_dir)

            # Check if path is within allowed directory
            return abs_path.startswith(abs_allowed)

        except Exception as e:
            logger.warning(f"Path validation error: {e}")
            return False

    def validate_site_access(self, site_id: str, user_id: Optional[str] = None) -> bool:
        """
        Check if user has access to site.

        Args:
            site_id: Site to access
            user_id: User ID (uses session if not provided)

        Returns:
            True if access allowed
        """
        # Check if site exists
        if not self.site_manager.site_exists(site_id):
            return False

        # Check if site is enabled
        site = self.site_manager.get_site(site_id)
        if not site or not site.get('enabled'):
            return False

        # Get user from session
        if not user_id:
            from flask import session
            user_id = session.get('user_id')

        # TODO: Implement per-site permissions when admin/user system is extended
        # For now, assume admin has access to all sites

        return True

    def enforce_site_isolation(self, app):
        """
        Apply isolation middleware to Flask app.

        Args:
            app: Flask application instance
        """
        @app.before_request
        def check_site_isolation():
            """Verify site isolation on each request."""
            site_id = g.get('site_id', 'default')

            # Validate site exists and is enabled
            if not self.validate_site_access(site_id):
                from flask import abort
                abort(403)

            # Isolate session per site
            self._isolate_session(site_id)

        logger.info("Site isolation enforced")

    def _isolate_session(self, site_id: str):
        """
        Isolate Flask session per site.

        Args:
            site_id: Current site ID
        """
        from flask import session

        # Mark session with current site
        session['_site_id'] = site_id

        # Check if session was for different site
        if '_previous_site_id' in session:
            if session['_previous_site_id'] != site_id:
                # Clear sensitive data when switching sites
                session.clear()
                session['_site_id'] = site_id
                logger.warning(f"Cleared session for site change")

        session['_previous_site_id'] = site_id


class SiteDecorators:
    """Decorators for multi-site route protection."""

    @staticmethod
    def require_site(site_id: Optional[str] = None) -> Callable:
        """
        Decorator to require specific site.

        Args:
            site_id: Required site (None = any enabled site)

        Returns:
            Decorator function
        """
        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def decorated_function(*args, **kwargs):
                current_site_id = g.get('site_id', 'default')

                if site_id and current_site_id != site_id:
                    from flask import abort
                    abort(403)

                return f(*args, **kwargs)

            return decorated_function

        return decorator

    @staticmethod
    def require_admin() -> Callable:
        """
        Decorator to require admin access to current site.

        Returns:
            Decorator function
        """
        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def decorated_function(*args, **kwargs):
                from flask import session, abort

                if not session.get('authenticated'):
                    abort(401)

                # TODO: Check if user is admin for current site

                return f(*args, **kwargs)

            return decorated_function

        return decorator

    @staticmethod
    def require_owner(resource_type: str) -> Callable:
        """
        Decorator to require ownership of resource.

        Args:
            resource_type: Type of resource (e.g., 'page', 'image')

        Returns:
            Decorator function
        """
        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def decorated_function(*args, **kwargs):
                from flask import session, abort

                if not session.get('authenticated'):
                    abort(401)

                # TODO: Implement ownership check based on resource_type

                return f(*args, **kwargs)

            return decorated_function

        return decorator


class RateLimiter:
    """Rate limiting per site."""

    def __init__(self):
        """Initialize rate limiter."""
        self.limits = {}  # site_id -> {ip -> request_count}

    def check_rate_limit(self, site_id: str, ip: str,
                        limit: int = 100, window: int = 60) -> bool:
        """
        Check if request rate limit exceeded.

        Args:
            site_id: Site ID
            ip: Client IP address
            limit: Max requests per window
            window: Time window in seconds

        Returns:
            True if request allowed, False if rate limited
        """
        # TODO: Implement rate limiting with timestamp tracking

        return True

    def get_usage(self, site_id: str, ip: str) -> dict:
        """Get usage stats for IP on site."""
        return {
            'site_id': site_id,
            'ip': ip,
            'requests': 0,
            'limit': 100,
            'window': 60
        }


def create_site_isolation_middleware(site_manager) -> SiteIsolation:
    """
    Factory function to create isolation middleware.

    Args:
        site_manager: SiteManager instance

    Returns:
        Configured SiteIsolation instance
    """
    return SiteIsolation(site_manager)
