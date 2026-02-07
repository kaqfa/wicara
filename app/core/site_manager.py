"""
Site Manager - ECS-01

Simplified site manager for Engine-Content Separation (ECS).
Provides path abstraction layer supporting both legacy and sites mode.

This is a lightweight implementation focused on path resolution and basic site
management. Can be upgraded to full multisite support later.
"""

import os
import json
import shutil
from pathlib import Path
from typing import Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)


class SiteManager:
    """
    Manages site paths and basic site operations.

    Supports two modes:
    1. Legacy Mode (LEGACY_MODE=true):
       - Uses root paths: config.json, templates/, static/
       - Backward compatible with existing installations

    2. Sites Mode (LEGACY_MODE=false):
       - Uses sites directory: sites/{site_id}/config.json, etc.
       - Separates engine from content
       - Multi-site ready

    Directory Structure (Sites Mode):
    sites/
        default/                    # Default site
            config.json
            config.json.backup
            templates/              # Site templates
            static/                 # Site static files
                images/
                    uploads/        # User uploads
        site2/                      # Additional sites (future)
            ...
    """

    def __init__(self, sites_dir: str = 'sites', default_site: str = 'default',
                 legacy_mode: bool = False):
        """
        Initialize site manager.

        Args:
            sites_dir: Base directory for all sites (default: 'sites')
            default_site: Default site identifier (default: 'default')
            legacy_mode: Use legacy root paths if True (default: False)
        """
        self.sites_dir = sites_dir
        self.default_site = default_site
        self.legacy_mode = legacy_mode

        # Legacy mode paths
        self._legacy_config = 'config.json'
        self._legacy_templates = 'templates'
        self._legacy_static = 'static'
        self._legacy_uploads = os.path.join('static', 'images', 'uploads')

        logger.info(f"SiteManager initialized: legacy_mode={legacy_mode}, "
                   f"sites_dir={sites_dir}, default_site={default_site}")

    def get_config_path(self, site_id: Optional[str] = None) -> str:
        """
        Get path to site's config.json file.

        Args:
            site_id: Site identifier (uses default_site if None)

        Returns:
            Absolute or relative path to config.json

        Examples:
            Legacy mode: 'config.json'
            Sites mode: 'sites/default/config.json'
        """
        if self.legacy_mode:
            return self._legacy_config

        site_id = site_id or self.default_site
        return os.path.join(self.sites_dir, site_id, 'config.json')

    def get_templates_dir(self, site_id: Optional[str] = None) -> str:
        """
        Get path to site's templates directory.

        Args:
            site_id: Site identifier (uses default_site if None)

        Returns:
            Path to templates directory

        Examples:
            Legacy mode: 'templates'
            Sites mode: 'sites/default/templates'
        """
        if self.legacy_mode:
            return self._legacy_templates

        site_id = site_id or self.default_site
        return os.path.join(self.sites_dir, site_id, 'templates')

    def get_static_dir(self, site_id: Optional[str] = None) -> str:
        """
        Get path to site's static files directory.

        Args:
            site_id: Site identifier (uses default_site if None)

        Returns:
            Path to static directory

        Examples:
            Legacy mode: 'static'
            Sites mode: 'sites/default/static'
        """
        if self.legacy_mode:
            return self._legacy_static

        site_id = site_id or self.default_site
        return os.path.join(self.sites_dir, site_id, 'static')

    def get_uploads_dir(self, site_id: Optional[str] = None) -> str:
        """
        Get path to site's uploads directory.

        Args:
            site_id: Site identifier (uses default_site if None)

        Returns:
            Path to uploads directory

        Examples:
            Legacy mode: 'static/images/uploads'
            Sites mode: 'sites/default/static/images/uploads'
        """
        if self.legacy_mode:
            return self._legacy_uploads

        site_id = site_id or self.default_site
        return os.path.join(self.sites_dir, site_id, 'static', 'images', 'uploads')

    def site_exists(self, site_id: str) -> bool:
        """
        Check if site exists.

        Args:
            site_id: Site identifier to check

        Returns:
            True if site directory and config.json exist

        Note:
            In legacy mode, always returns True for default_site
        """
        if self.legacy_mode and site_id == self.default_site:
            return os.path.exists(self._legacy_config)

        if self.legacy_mode:
            return False

        site_path = os.path.join(self.sites_dir, site_id)
        config_path = os.path.join(site_path, 'config.json')

        return os.path.isdir(site_path) and os.path.isfile(config_path)

    def get_all_sites(self) -> List[str]:
        """
        Get list of all site identifiers.

        Returns:
            List of site IDs

        Note:
            In legacy mode, returns [default_site]
        """
        if self.legacy_mode:
            return [self.default_site]

        if not os.path.exists(self.sites_dir):
            return []

        sites = []
        try:
            for entry in os.listdir(self.sites_dir):
                site_path = os.path.join(self.sites_dir, entry)
                config_path = os.path.join(site_path, 'config.json')

                if os.path.isdir(site_path) and os.path.isfile(config_path):
                    sites.append(entry)
        except Exception as e:
            logger.error(f"Error listing sites: {e}")

        return sorted(sites)

    def create_site(self, site_id: str, template_site: Optional[str] = None) -> Tuple[bool, str]:
        """
        Create a new site with directory structure.

        Args:
            site_id: Identifier for new site
            template_site: Optional site ID to copy templates from

        Returns:
            Tuple of (success: bool, message: str)

        Note:
            Not available in legacy mode
        """
        if self.legacy_mode:
            return False, "Cannot create sites in legacy mode"

        if self.site_exists(site_id):
            return False, f"Site '{site_id}' already exists"

        try:
            # Create site directory structure
            site_path = os.path.join(self.sites_dir, site_id)

            success = self.ensure_site_structure(site_id)
            if not success:
                return False, f"Failed to create site structure for '{site_id}'"

            # Create default config.json
            config_path = os.path.join(site_path, 'config.json')
            default_config = self._get_default_config(site_id)

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)

            # Copy templates from template site if provided
            if template_site and self.site_exists(template_site):
                source_templates = self.get_templates_dir(template_site)
                dest_templates = self.get_templates_dir(site_id)

                if os.path.exists(source_templates):
                    try:
                        for item in os.listdir(source_templates):
                            src = os.path.join(source_templates, item)
                            dst = os.path.join(dest_templates, item)

                            if os.path.isfile(src):
                                shutil.copy2(src, dst)
                            elif os.path.isdir(src):
                                shutil.copytree(src, dst, dirs_exist_ok=True)

                        logger.info(f"Copied templates from '{template_site}' to '{site_id}'")
                    except Exception as e:
                        logger.warning(f"Failed to copy templates: {e}")

            logger.info(f"Created site: {site_id}")
            return True, f"Site '{site_id}' created successfully"

        except Exception as e:
            logger.error(f"Failed to create site '{site_id}': {e}")
            return False, f"Error creating site: {str(e)}"

    def ensure_site_structure(self, site_id: Optional[str] = None) -> bool:
        """
        Ensure site directory structure exists, creating if needed.

        Creates:
        - Site root directory
        - templates/ directory
        - static/ directory
        - static/images/uploads/ directory

        Args:
            site_id: Site identifier (uses default_site if None)

        Returns:
            True if structure exists or was created successfully

        Note:
            In legacy mode, creates root directories
        """
        try:
            if self.legacy_mode:
                # Create legacy directories
                Path(self._legacy_templates).mkdir(parents=True, exist_ok=True)
                Path(self._legacy_static).mkdir(parents=True, exist_ok=True)
                Path(self._legacy_uploads).mkdir(parents=True, exist_ok=True)
                return True

            site_id = site_id or self.default_site
            site_path = os.path.join(self.sites_dir, site_id)

            # Create all required directories
            directories = [
                site_path,
                os.path.join(site_path, 'templates'),
                os.path.join(site_path, 'static'),
                os.path.join(site_path, 'static', 'images'),
                os.path.join(site_path, 'static', 'images', 'uploads'),
            ]

            for directory in directories:
                Path(directory).mkdir(parents=True, exist_ok=True)

            logger.debug(f"Ensured site structure for: {site_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to ensure site structure: {e}")
            return False

    def _get_default_config(self, site_id: str) -> dict:
        """
        Get default configuration for a new site.

        Args:
            site_id: Site identifier

        Returns:
            Default configuration dictionary
        """
        return {
            'admin-password': 'admin123',  # Should be changed immediately
            'sitename': site_id.replace('-', ' ').replace('_', ' ').title(),
            'description': f'Website for {site_id}',
            'keywords': [],
            'pages': [
                {
                    'title': 'Home',
                    'template': 'home.html',
                    'url': '/',
                    'menu-title': 'Home',
                    'seo-description': f'Welcome to {site_id}',
                    'seo-keywords': [],
                    'fields': [
                        {
                            'name': 'hero-title',
                            'type': 'text',
                            'label': 'Hero Title',
                            'value': 'Welcome to Your Website'
                        },
                        {
                            'name': 'hero-description',
                            'type': 'textarea',
                            'label': 'Hero Description',
                            'value': 'Start building your website with Wicara CMS'
                        }
                    ]
                }
            ],
            'footer': {
                'content': [
                    f'© 2026 {site_id}. All rights reserved.'
                ]
            }
        }

    def __repr__(self) -> str:
        """String representation of SiteManager."""
        mode = "legacy" if self.legacy_mode else "sites"
        return f"<SiteManager mode={mode} default={self.default_site}>"
