"""
Public module utilities.
Helper functions for public page handling.
"""

from flask import current_app
from app.core import load_config


def get_page_by_url(url):
    """
    Get page configuration by URL.

    Args:
        url: Page URL to search for

    Returns:
        Page configuration dictionary or None
    """
    config = load_config(current_app.config['CONFIG_FILE'], logger=current_app.logger)
    if not config:
        return None

    for page in config['pages']:
        if page['url'] == url:
            return page
    return None
