"""
Wicara Multi-site Support - Phase 5

Enterprise-grade multi-tenant CMS capabilities.
Support for hosting multiple independent websites from single Wicara instance.

Key Components:
- SiteManager: Multi-site management and orchestration
- SiteRouter: Domain-based routing middleware
- SiteContext: Per-site context management
- SiteIsolation: Security and isolation enforcement
"""

from .manager import SiteManager
from .router import SiteRouter
from .context import SiteContext

__all__ = [
    'SiteManager',
    'SiteRouter',
    'SiteContext',
]

# Global site manager instance
_site_manager = None


def get_site_manager():
    """Get or create global site manager instance."""
    global _site_manager
    if _site_manager is None:
        _site_manager = SiteManager()
    return _site_manager


def init_multisite(app, sites_dir=None, enable_routing=True):
    """Initialize multi-site system with Flask app."""
    manager = get_site_manager()
    manager.init_app(app, sites_dir)

    if enable_routing:
        router = SiteRouter()
        router.init_app(app, manager)

    return manager
