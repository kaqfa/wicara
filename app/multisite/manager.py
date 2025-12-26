"""
Site Manager - MULTI-01

Central management for multiple websites.
Handles site CRUD operations, configuration, and orchestration.
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SiteManager:
    """
    Manages multiple websites in single Wicara instance.

    Each site has:
    - Unique identifier (site_id)
    - Domain mappings
    - Independent configuration
    - Isolated templates and uploads
    - Per-site cache
    - Per-site permissions

    Directory Structure:
    sites/
        default/                    # Default/main site
            config.json
            templates/
            config.json.backup
        site-2/
            config.json
            templates/
        site-3/
            config.json
            templates/
        .sites.json                 # Sites registry
    """

    def __init__(self):
        """Initialize site manager."""
        self.app = None
        self.sites_dir = None
        self.sites_registry: Dict[str, Dict[str, Any]] = {}
        self._default_site = 'default'

    def init_app(self, app, sites_dir: Optional[str] = None):
        """
        Initialize site manager with Flask app.

        Args:
            app: Flask application instance
            sites_dir: Path to sites directory (default: sites/)
        """
        self.app = app
        self.sites_dir = sites_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), '..', 'sites'
        )

        # Create sites directory
        Path(self.sites_dir).mkdir(parents=True, exist_ok=True)

        # Load sites registry
        self._load_registry()

        # Create default site if doesn't exist
        if not self.site_exists(self._default_site):
            self.create_site(self._default_site)

        logger.info(f"Site manager initialized with sites_dir: {self.sites_dir}")

    def create_site(self, site_id: str, config: Optional[Dict] = None,
                   template_site: Optional[str] = None) -> bool:
        """
        Create a new site.

        Args:
            site_id: Unique site identifier
            config: Initial configuration (uses default if not provided)
            template_site: Clone from existing site (for templates only)

        Returns:
            True if created successfully
        """
        if self.site_exists(site_id):
            logger.warning(f"Site '{site_id}' already exists")
            return False

        try:
            site_path = self._get_site_path(site_id)
            Path(site_path).mkdir(parents=True, exist_ok=True)

            # Create templates directory
            templates_dir = os.path.join(site_path, 'templates')
            Path(templates_dir).mkdir(exist_ok=True)

            # Copy templates from template site if provided
            if template_site and self.site_exists(template_site):
                template_source = os.path.join(
                    self._get_site_path(template_site), 'templates'
                )
                if os.path.exists(template_source):
                    for file in os.listdir(template_source):
                        src = os.path.join(template_source, file)
                        dst = os.path.join(templates_dir, file)
                        if os.path.isfile(src):
                            shutil.copy2(src, dst)

            # Create config.json
            if config is None:
                config = self._get_default_config(site_id)

            config_path = os.path.join(site_path, 'config.json')
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)

            # Register site
            self.sites_registry[site_id] = {
                'id': site_id,
                'name': config.get('sitename', site_id),
                'created_at': datetime.now().isoformat(),
                'enabled': True,
                'domains': [],  # Will be set separately
                'config': config_path
            }

            self._save_registry()

            logger.info(f"Created site: {site_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to create site '{site_id}': {e}")
            return False

    def delete_site(self, site_id: str, force: bool = False) -> bool:
        """
        Delete a site.

        Args:
            site_id: Site to delete
            force: Force deletion even if it's the default site

        Returns:
            True if deleted successfully
        """
        if not self.site_exists(site_id):
            logger.warning(f"Site '{site_id}' not found")
            return False

        if site_id == self._default_site and not force:
            logger.error("Cannot delete default site without force=True")
            return False

        try:
            site_path = self._get_site_path(site_id)
            shutil.rmtree(site_path)

            del self.sites_registry[site_id]
            self._save_registry()

            logger.info(f"Deleted site: {site_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete site '{site_id}': {e}")
            return False

    def site_exists(self, site_id: str) -> bool:
        """Check if site exists."""
        return site_id in self.sites_registry

    def get_site(self, site_id: str) -> Optional[Dict[str, Any]]:
        """Get site metadata."""
        return self.sites_registry.get(site_id)

    def get_all_sites(self) -> Dict[str, Dict[str, Any]]:
        """Get all sites."""
        return self.sites_registry.copy()

    def get_site_config_path(self, site_id: str) -> Optional[str]:
        """Get path to site's config.json."""
        if not self.site_exists(site_id):
            return None

        return os.path.join(self._get_site_path(site_id), 'config.json')

    def get_site_templates_dir(self, site_id: str) -> Optional[str]:
        """Get path to site's templates directory."""
        if not self.site_exists(site_id):
            return None

        return os.path.join(self._get_site_path(site_id), 'templates')

    def get_site_uploads_dir(self, site_id: str) -> Optional[str]:
        """Get path to site's uploads directory."""
        if not self.site_exists(site_id):
            return None

        uploads_dir = os.path.join(self._get_site_path(site_id), 'uploads')
        Path(uploads_dir).mkdir(parents=True, exist_ok=True)
        return uploads_dir

    def add_domain(self, site_id: str, domain: str) -> bool:
        """
        Map domain to site.

        Args:
            site_id: Site to map domain to
            domain: Domain name (e.g., example.com)

        Returns:
            True if mapped successfully
        """
        if not self.site_exists(site_id):
            return False

        site = self.sites_registry[site_id]
        if domain not in site['domains']:
            site['domains'].append(domain)
            self._save_registry()
            logger.info(f"Mapped domain '{domain}' to site '{site_id}'")

        return True

    def remove_domain(self, site_id: str, domain: str) -> bool:
        """Remove domain mapping from site."""
        if not self.site_exists(site_id):
            return False

        site = self.sites_registry[site_id]
        if domain in site['domains']:
            site['domains'].remove(domain)
            self._save_registry()
            logger.info(f"Unmapped domain '{domain}' from site '{site_id}'")

        return True

    def get_site_by_domain(self, domain: str) -> Optional[str]:
        """
        Get site ID for given domain.

        Args:
            domain: Domain name

        Returns:
            Site ID or None if not found
        """
        for site_id, site_info in self.sites_registry.items():
            if domain in site_info.get('domains', []):
                return site_id

        # Return default site if domain not found
        return self._default_site

    def enable_site(self, site_id: str) -> bool:
        """Enable a site."""
        if not self.site_exists(site_id):
            return False

        self.sites_registry[site_id]['enabled'] = True
        self._save_registry()
        return True

    def disable_site(self, site_id: str) -> bool:
        """Disable a site."""
        if not self.site_exists(site_id):
            return False

        if site_id == self._default_site:
            logger.error("Cannot disable default site")
            return False

        self.sites_registry[site_id]['enabled'] = False
        self._save_registry()
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get site manager statistics."""
        enabled = sum(1 for s in self.sites_registry.values() if s.get('enabled'))
        total_domains = sum(len(s.get('domains', [])) for s in self.sites_registry.values())

        return {
            'total_sites': len(self.sites_registry),
            'enabled_sites': enabled,
            'disabled_sites': len(self.sites_registry) - enabled,
            'total_domains': total_domains,
            'sites_dir': self.sites_dir,
        }

    def _get_site_path(self, site_id: str) -> str:
        """Get file system path for site."""
        return os.path.join(self.sites_dir, site_id)

    def _get_default_config(self, site_id: str) -> Dict[str, Any]:
        """Get default configuration for new site."""
        return {
            'admin-password': 'admin123',
            'sitename': site_id.replace('-', ' ').title(),
            'description': f'Website for {site_id}',
            'keywords': [],
            'pages': [
                {
                    'title': 'Home',
                    'template': 'home.html',
                    'url': '/',
                    'menu-title': 'Home',
                    'fields': []
                }
            ],
            'footer': {
                'content': ['© 2025 All rights reserved']
            }
        }

    def _load_registry(self):
        """Load sites registry from file."""
        registry_file = os.path.join(self.sites_dir, '.sites.json')

        try:
            if os.path.exists(registry_file):
                with open(registry_file, 'r') as f:
                    self.sites_registry = json.load(f)
            else:
                self.sites_registry = {}
        except Exception as e:
            logger.error(f"Failed to load sites registry: {e}")
            self.sites_registry = {}

    def _save_registry(self):
        """Save sites registry to file."""
        registry_file = os.path.join(self.sites_dir, '.sites.json')

        try:
            with open(registry_file, 'w') as f:
                json.dump(self.sites_registry, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save sites registry: {e}")

    def __repr__(self) -> str:
        enabled = sum(1 for s in self.sites_registry.values() if s.get('enabled'))
        return f"<SiteManager: {len(self.sites_registry)} sites ({enabled} enabled)>"
