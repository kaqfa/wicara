"""
Public routes for WICARA CMS.
Handles public-facing pages and content rendering.
"""

from flask import Blueprint, render_template, current_app, request
from app.core import load_config, render_page_template
from app.core.config_manager import ConfigManager
from app.modules.public.utils import get_page_by_url

public_bp = Blueprint('public', __name__)


def _render_page_content(page_url, page, config):
    """Render page content.

    Args:
        page_url: The page URL
        page: Page configuration
        config: Site configuration

    Returns:
        Rendered HTML string
    """
    return render_page_template(page['template'], config, page)


@public_bp.route('/')
def index():
    """
    Home page route.

    Renders the home page configured in config.json.
    Integrates response caching for public pages.
    """
    page = get_page_by_url('/')
    if not page:
        return render_template('404.html'), 404

    # ECS-08: Use ConfigManager with site_manager for Engine-Content Separation
    config_manager = ConfigManager(
        site_manager=getattr(current_app, 'site_manager', None),
        logger=current_app.logger
    )
    config = config_manager.load()

    if not config:
        return render_template('500.html'), 500

    # Use response caching if available
    if hasattr(current_app, 'cache_service') and current_app.cache_service:
        response_cache = current_app.cache_service.response_cache
        if response_cache:
            response = response_cache.cache_response(
                '/',
                lambda: _render_page_content('/', page, config),
                ttl=3600,
                public=True,
            )

            # Check for conditional requests (ETag/If-Modified-Since)
            conditional = response_cache.handle_conditional_request(
                '/',
                if_none_match=request.headers.get('If-None-Match'),
                if_modified_since=request.headers.get('If-Modified-Since'),
            )
            if conditional:
                return conditional

            return response

    return render_page_template(page['template'], config, page)


@public_bp.route('/<path:url>')
def page(url):
    """
    Dynamic page route handler.

    Renders any page configured in config.json by its URL.
    Integrates response caching for public pages.

    Args:
        url: Page URL path (without leading slash)
    """
    page = get_page_by_url(f'/{url}')
    if not page:
        return render_template('404.html'), 404

    # ECS-08: Use ConfigManager with site_manager for Engine-Content Separation
    config_manager = ConfigManager(
        site_manager=getattr(current_app, 'site_manager', None),
        logger=current_app.logger
    )
    config = config_manager.load()

    if not config:
        return render_template('500.html'), 500

    # Use response caching if available
    if hasattr(current_app, 'cache_service') and current_app.cache_service:
        response_cache = current_app.cache_service.response_cache
        if response_cache:
            page_url = f'/{url}'
            response = response_cache.cache_response(
                page_url,
                lambda: _render_page_content(page_url, page, config),
                ttl=3600,
                public=True,
            )

            # Check for conditional requests (ETag/If-Modified-Since)
            conditional = response_cache.handle_conditional_request(
                page_url,
                if_none_match=request.headers.get('If-None-Match'),
                if_modified_since=request.headers.get('If-Modified-Since'),
            )
            if conditional:
                return conditional

            return response

    return render_page_template(page['template'], config, page)
