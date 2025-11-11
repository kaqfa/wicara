"""
Public routes blueprint for WICARA CMS.
Handles public-facing pages and content rendering.
"""

from flask import Blueprint, render_template, current_app
from app.utils import load_config, convert_keys_to_underscore
import os

public_bp = Blueprint('public', __name__)


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


def render_template_with_data(template_name, page_data=None):
    """
    Render template with configuration data.

    Args:
        template_name: Name of template to render
        page_data: Page configuration data

    Returns:
        Rendered template HTML or error response tuple
    """
    config = load_config(current_app.config['CONFIG_FILE'], logger=current_app.logger)
    if not config:
        return render_template('500.html'), 500

    # Check if template exists
    template_path = os.path.join('templates', template_name)
    if not os.path.exists(template_path):
        current_app.logger.error(f'Template not found: {template_name}')
        return render_template('404.html'), 404

    # Convert all config keys with hyphens to underscores for Jinja2
    config_underscore = convert_keys_to_underscore(config)

    template_data = {
        'sitename': config_underscore.get('sitename', ''),
        'description': config_underscore.get('description', ''),
        'keywords': config_underscore.get('keywords', []),
        'footer': config_underscore.get('footer', {}).get('content', []),
        'pages': config_underscore.get('pages', [])
    }

    if page_data:
        # Convert page data keys as well
        page_data_underscore = convert_keys_to_underscore(page_data)

        # Add field values with converted names
        for field in page_data.get('fields', []):
            field_name = field['name'].replace('-', '_')
            template_data[field_name] = field.get('value', '')

        # Add page metadata with converted keys
        template_data.update({
            'page_title': page_data_underscore.get('title', ''),
            'seo_description': page_data_underscore.get('seo_description', ''),
            'seo_keywords': page_data_underscore.get('seo_keywords', [])
        })

    try:
        return render_template(template_name, **template_data)
    except Exception as e:
        current_app.logger.error(f'Template rendering error for {template_name}: {e}')
        return render_template('500.html'), 500


@public_bp.route('/')
def index():
    """Home page route."""
    page = get_page_by_url('/')
    if not page:
        return render_template('404.html'), 404
    return render_template_with_data(page['template'], page)


@public_bp.route('/<path:url>')
def public_page(url):
    """Dynamic page route handler."""
    page = get_page_by_url(f'/{url}')
    if not page:
        return render_template('404.html'), 404
    return render_template_with_data(page['template'], page)
