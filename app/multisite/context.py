"""
Site Context - MULTI-02

Per-request site context management.
Provides access to current site's resources.
"""

from flask import g
from typing import Optional, Dict, Any
import json
import os
import logging

logger = logging.getLogger(__name__)


class SiteContext:
    """
    Manages per-request site context.

    Provides unified access to:
    - Current site ID
    - Site configuration
    - Site paths (templates, uploads)
    - Site-specific cache
    """

    def __init__(self, site_manager):
        """
        Initialize site context.

        Args:
            site_manager: SiteManager instance
        """
        self.site_manager = site_manager

    def get_current_site_id(self) -> str:
        """Get current request's site ID."""
        return g.get('site_id', 'default')

    def get_current_site(self) -> Optional[Dict[str, Any]]:
        """Get current request's site metadata."""
        return g.get('site')

    def get_config(self, site_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get site configuration.

        Args:
            site_id: Site ID (uses current if not provided)

        Returns:
            Configuration dict or None
        """
        if not site_id:
            site_id = self.get_current_site_id()

        config_path = self.site_manager.get_site_config_path(site_id)
        if not config_path or not os.path.exists(config_path):
            return None

        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config for site '{site_id}': {e}")
            return None

    def save_config(self, config: Dict[str, Any], site_id: Optional[str] = None) -> bool:
        """
        Save site configuration.

        Args:
            config: Configuration dict
            site_id: Site ID (uses current if not provided)

        Returns:
            True if saved successfully
        """
        if not site_id:
            site_id = self.get_current_site_id()

        config_path = self.site_manager.get_site_config_path(site_id)
        if not config_path:
            return False

        try:
            # Create backup
            if os.path.exists(config_path):
                backup_path = config_path + '.backup'
                with open(config_path, 'r') as src:
                    with open(backup_path, 'w') as dst:
                        dst.write(src.read())

            # Save config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)

            logger.info(f"Saved config for site '{site_id}'")
            return True

        except Exception as e:
            logger.error(f"Failed to save config for site '{site_id}': {e}")
            return False

    def get_templates_dir(self, site_id: Optional[str] = None) -> Optional[str]:
        """
        Get site's templates directory.

        Args:
            site_id: Site ID (uses current if not provided)

        Returns:
            Directory path or None
        """
        if not site_id:
            site_id = self.get_current_site_id()

        return self.site_manager.get_site_templates_dir(site_id)

    def get_uploads_dir(self, site_id: Optional[str] = None) -> Optional[str]:
        """
        Get site's uploads directory.

        Args:
            site_id: Site ID (uses current if not provided)

        Returns:
            Directory path or None
        """
        if not site_id:
            site_id = self.get_current_site_id()

        return self.site_manager.get_site_uploads_dir(site_id)

    def get_upload_url(self, filename: str, site_id: Optional[str] = None) -> str:
        """
        Get URL for uploaded file.

        Args:
            filename: Uploaded filename
            site_id: Site ID (uses current if not provided)

        Returns:
            URL path for file
        """
        if not site_id:
            site_id = self.get_current_site_id()

        if site_id == 'default':
            return f"/static/images/uploads/{filename}"

        return f"/sites/{site_id}/uploads/{filename}"

    def set_current_site(self, site_id: str):
        """
        Manually set current site (for non-HTTP contexts).

        Args:
            site_id: Site ID to set as current
        """
        g.site_id = site_id
        g.site = self.site_manager.get_site(site_id)

    def get_all_sites_config(self) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Get configuration for all sites.

        Returns:
            Dict mapping site_id to config
        """
        configs = {}
        for site_id in self.site_manager.get_all_sites():
            configs[site_id] = self.get_config(site_id)

        return configs

    @staticmethod
    def init_app(app, site_manager):
        """
        Initialize site context with Flask app.

        Args:
            app: Flask application instance
            site_manager: SiteManager instance
        """
        context = SiteContext(site_manager)
        app.site_context = context
        return context


def get_site_context() -> Optional[SiteContext]:
    """Get site context from current app."""
    from flask import current_app
    return getattr(current_app, 'site_context', None)


def get_current_site_id() -> str:
    """Get current request's site ID."""
    context = get_site_context()
    if context:
        return context.get_current_site_id()
    return g.get('site_id', 'default')


def get_current_config() -> Optional[Dict[str, Any]]:
    """Get current request's site configuration."""
    context = get_site_context()
    if context:
        return context.get_config()
    return None


def get_current_templates_dir() -> Optional[str]:
    """Get current request's templates directory."""
    context = get_site_context()
    if context:
        return context.get_templates_dir()
    return None


def get_current_uploads_dir() -> Optional[str]:
    """Get current request's uploads directory."""
    context = get_site_context()
    if context:
        return context.get_uploads_dir()
    return None
