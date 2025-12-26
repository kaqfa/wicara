"""
Wicara Multi-site Support - Phase 5

Enterprise-grade multi-tenant CMS capabilities.
Support for hosting multiple independent websites from single Wicara instance.

Core Components (MULTI-01 to MULTI-04):
- SiteManager: Multi-site management and orchestration (MULTI-01)
- SiteRouter: Domain-based routing middleware (MULTI-01)
- SiteContext: Per-site context management (MULTI-02)
- SiteIsolation: Security and isolation enforcement (MULTI-04)

Advanced Features (MULTI-05):
- SiteGroupManager: Hierarchical group management
- ActivityLogger: Event tracking and audit trails
- PermissionManager: Role-based access control (RBAC)
- QuotaManager: Resource quotas and usage limits
"""

from .manager import SiteManager
from .router import SiteRouter
from .context import SiteContext
from .groups import SiteGroupManager
from .activity import ActivityLogger
from .permissions import PermissionManager
from .quotas import QuotaManager

__all__ = [
    'SiteManager',
    'SiteRouter',
    'SiteContext',
    'SiteGroupManager',
    'ActivityLogger',
    'PermissionManager',
    'QuotaManager',
]

# Global manager instances
_site_manager = None
_group_manager = None
_activity_logger = None
_permission_manager = None
_quota_manager = None


def get_site_manager():
    """Get or create global site manager instance."""
    global _site_manager
    if _site_manager is None:
        _site_manager = SiteManager()
    return _site_manager


def get_group_manager(data_dir: str = None):
    """Get or create global site group manager instance."""
    global _group_manager
    if _group_manager is None:
        if data_dir is None:
            data_dir = get_site_manager().data_dir
        _group_manager = SiteGroupManager(data_dir)
    return _group_manager


def get_activity_logger(data_dir: str = None):
    """Get or create global activity logger instance."""
    global _activity_logger
    if _activity_logger is None:
        if data_dir is None:
            data_dir = get_site_manager().data_dir
        _activity_logger = ActivityLogger(data_dir)
    return _activity_logger


def get_permission_manager(data_dir: str = None):
    """Get or create global permission manager instance."""
    global _permission_manager
    if _permission_manager is None:
        if data_dir is None:
            data_dir = get_site_manager().data_dir
        _permission_manager = PermissionManager(data_dir)
    return _permission_manager


def get_quota_manager(data_dir: str = None):
    """Get or create global quota manager instance."""
    global _quota_manager
    if _quota_manager is None:
        if data_dir is None:
            data_dir = get_site_manager().data_dir
        _quota_manager = QuotaManager(data_dir)
    return _quota_manager


def init_multisite(app, sites_dir=None, enable_routing=True, enable_advanced_features=True):
    """
    Initialize multi-site system with Flask app.

    Args:
        app: Flask application
        sites_dir: Directory for site data
        enable_routing: Enable domain-based routing
        enable_advanced_features: Enable MULTI-05 features (groups, activity, permissions, quotas)

    Returns:
        Initialized SiteManager instance
    """
    manager = get_site_manager()
    manager.init_app(app, sites_dir)

    if enable_routing:
        router = SiteRouter()
        router.init_app(app, manager)

    # Initialize advanced features
    if enable_advanced_features:
        data_dir = manager.data_dir
        get_group_manager(data_dir)
        get_activity_logger(data_dir)
        get_permission_manager(data_dir)
        get_quota_manager(data_dir)

    return manager
