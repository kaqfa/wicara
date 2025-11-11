"""
Public routes for WICARA CMS.
Handles public-facing pages and content rendering.
"""

from flask import Blueprint, render_template, current_app
from app.core import load_config, render_page_template
from app.modules.public.utils import get_page_by_url

public_bp = Blueprint('public', __name__)


@public_bp.route('/')
def index():
    """
    Home page route.

    Renders the home page configured in config.json.
    """
    page = get_page_by_url('/')
    if not page:
        return render_template('404.html'), 404

    config = load_config(current_app.config['CONFIG_FILE'], logger=current_app.logger)
    if not config:
        return render_template('500.html'), 500

    return render_page_template(page['template'], config, page)


@public_bp.route('/<path:url>')
def page(url):
    """
    Dynamic page route handler.

    Renders any page configured in config.json by its URL.

    Args:
        url: Page URL path (without leading slash)
    """
    page = get_page_by_url(f'/{url}')
    if not page:
        return render_template('404.html'), 404

    config = load_config(current_app.config['CONFIG_FILE'], logger=current_app.logger)
    if not config:
        return render_template('500.html'), 500

    return render_page_template(page['template'], config, page)
