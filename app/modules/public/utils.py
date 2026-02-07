"""
Public module utilities.
Helper functions for public page handling.
"""

from flask import current_app
from app.core import load_config
from app.core.config_manager import ConfigManager


def get_page_by_url(url):
    """
    Get page configuration by URL.

    Args:
        url: Page URL to search for

    Returns:
        Page configuration dictionary or None
    """
    # ECS: Use ConfigManager with site_manager for Engine-Content Separation
    config_manager = ConfigManager(
        site_manager=getattr(current_app, 'site_manager', None),
        logger=current_app.logger
    )
    config = config_manager.load()

    if not config:
        return None

    for page in config['pages']:
        if page['url'] == url:
            return page
    return None
