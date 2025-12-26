"""
Site Router - MULTI-01

Domain-based routing middleware for multi-site support.
Routes requests to appropriate site based on domain.
"""

from flask import request, g
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SiteRouter:
    """
    Routes requests to correct site based on domain.

    Features:
    - Domain-to-site mapping
    - Fallback to default site
    - Subdomain support (e.g., site1.example.com)
    - Path-based routing fallback
    - Request context site injection
    """

    def __init__(self):
        """Initialize site router."""
        self.site_manager = None

    def init_app(self, app, site_manager):
        """
        Initialize router with Flask app.

        Args:
            app: Flask application instance
            site_manager: SiteManager instance
        """
        self.site_manager = site_manager
        app.before_request(self.route_to_site)
        logger.info("Site router initialized")

    def route_to_site(self):
        """
        Determine which site should handle request.

        Stored in g.site_id for access in route handlers.
        """
        if not self.site_manager:
            g.site_id = 'default'
            return

        # Get domain from request
        domain = self._get_domain()
        site_id = self.site_manager.get_site_by_domain(domain)

        if not site_id:
            site_id = 'default'

        # Check if site is enabled
        site = self.site_manager.get_site(site_id)
        if site and not site.get('enabled'):
            logger.warning(f"Request to disabled site: {site_id}")
            # Could return error or fall back to default

        # Inject site into request context
        g.site_id = site_id
        g.site = site

        logger.debug(f"Routed request to site '{site_id}' (domain: {domain})")

    def _get_domain(self) -> str:
        """
        Extract domain from request.

        Supports:
        - Full domain: example.com
        - Subdomain: site1.example.com
        - Localhost: localhost:5000

        Returns:
            Domain name without port
        """
        host = request.host.split(':')[0]  # Remove port
        return host.lower()

    @staticmethod
    def get_current_site_id() -> str:
        """Get current request's site ID."""
        return g.get('site_id', 'default')

    @staticmethod
    def get_current_site() -> Optional[dict]:
        """Get current request's site metadata."""
        return g.get('site')


class SubdomainRouter(SiteRouter):
    """
    Routes based on subdomain.

    Maps subdomain to site:
    - site1.example.com -> site1
    - site2.example.com -> site2
    - example.com -> default

    Configure with DOMAIN_MAP:
    DOMAIN_MAP = {
        'example.com': {
            'site1': 'site-1',  # subdomain -> site_id
            'site2': 'site-2'
        }
    }
    """

    def __init__(self, domain_map: Optional[dict] = None):
        """
        Initialize subdomain router.

        Args:
            domain_map: Mapping of domains to subdomain->site mappings
        """
        super().__init__()
        self.domain_map = domain_map or {}

    def route_to_site(self):
        """Route based on subdomain."""
        if not self.site_manager:
            g.site_id = 'default'
            return

        subdomain, domain = self._get_subdomain_and_domain()
        site_id = self._map_subdomain_to_site(subdomain, domain)

        if not site_id:
            site_id = 'default'

        site = self.site_manager.get_site(site_id)
        if site and not site.get('enabled'):
            site_id = 'default'

        g.site_id = site_id
        g.site = self.site_manager.get_site(site_id)

        logger.debug(f"Routed request to site '{site_id}' (subdomain: {subdomain}, domain: {domain})")

    def _get_subdomain_and_domain(self) -> tuple[str, str]:
        """Extract subdomain and domain from request."""
        host = request.host.split(':')[0].lower()
        parts = host.split('.')

        if len(parts) <= 2:
            # No subdomain (e.g., example.com or localhost)
            return '', host

        # Extract subdomain and domain
        subdomain = parts[0]
        domain = '.'.join(parts[1:])

        return subdomain, domain

    def _map_subdomain_to_site(self, subdomain: str, domain: str) -> Optional[str]:
        """Map subdomain+domain to site ID."""
        if not subdomain:
            # No subdomain, use domain mapping
            return self.site_manager.get_site_by_domain(domain)

        # Check domain map
        if domain in self.domain_map:
            return self.domain_map[domain].get(subdomain)

        return None
