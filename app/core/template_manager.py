"""
WICARA Core Module: Template Manager
Handles template rendering and data conversion for Jinja2.

ECS-06: Template Loading
-----------------------
Template loading is handled by Flask's Jinja2 environment with a ChoiceLoader
configured in the application factory (app/__init__.py):

Legacy Mode (LEGACY_MODE=true):
    - Templates are loaded from the root 'templates/' directory
    - Single template directory for backward compatibility

Sites Mode (LEGACY_MODE=false):
    - Templates are loaded using Jinja2 ChoiceLoader with two sources:
      1. Site-specific templates: sites/{site_id}/templates/ (priority 1)
      2. Engine templates: templates/ (priority 2, fallback)
    - Allows site-specific template overrides
    - Falls back to engine templates for admin and system templates
    - Supports multi-site deployments with shared engine

This module focuses on template context preparation and rendering,
while template resolution is managed by Flask's Jinja2 environment.
"""

from flask import render_template
import os


def convert_keys_to_underscore(data):
    """
    Recursively convert dictionary keys with hyphens to underscores for Jinja2 compatibility.

    The Jinja2 templating engine cannot use hyphenated variable names directly.
    This function converts all hyphens to underscores in dictionary keys,
    allowing config.json to use standard hyphenated naming while templates
    use underscore notation.

    Args:
        data: Dictionary, list, or primitive value to convert

    Returns:
        Converted data with underscores instead of hyphens in keys

    Example:
        Input: {'hero-title': 'Hello', 'nested-obj': {'sub-key': 'value'}}
        Output: {'hero_title': 'Hello', 'nested_obj': {'sub_key': 'value'}}
    """
    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            # Convert hyphens to underscores in keys
            new_key = key.replace('-', '_')
            # Recursively convert nested dictionaries
            new_dict[new_key] = convert_keys_to_underscore(value)
        return new_dict
    elif isinstance(data, list):
        # Recursively process list items
        return [convert_keys_to_underscore(item) for item in data]
    else:
        # Return primitive values as-is
        return data


def prepare_template_context(config, page_data=None):
    """
    Prepare context dictionary for template rendering.

    Combines global configuration with page-specific data and converts
    all keys to underscore notation for Jinja2 compatibility.

    Args:
        config: Global configuration dictionary
        page_data: Page-specific configuration (optional)

    Returns:
        Dictionary with prepared context for template rendering
    """
    # Convert all config keys with hyphens to underscores for Jinja2
    config_underscore = convert_keys_to_underscore(config)

    # Build base template context
    template_data = {
        'sitename': config_underscore.get('sitename', ''),
        'description': config_underscore.get('description', ''),
        'keywords': config_underscore.get('keywords', []),
        'footer': config_underscore.get('footer', {}).get('content', []),
        'pages': config_underscore.get('pages', [])
    }

    # Add page-specific data if provided
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

    return template_data


def render_page_template(template_name, config, page_data=None, logger=None):
    """
    Render a page template with configuration data.

    Handles template existence checking, context preparation, and error handling.

    Template Resolution (ECS-06):
        In sites mode, Flask's Jinja2 ChoiceLoader searches for templates in:
        1. Site-specific templates directory (sites/{site_id}/templates/)
        2. Engine templates directory (templates/) as fallback

        This allows sites to override default templates while maintaining
        access to shared engine templates (admin interface, error pages, etc.)

    Args:
        template_name: Name of template file to render (e.g., 'home.html')
        config: Global configuration dictionary
        page_data: Page-specific data (optional)
        logger: Logger instance for logging (optional)

    Returns:
        Tuple of (rendered_html, status_code) or error response tuple
    """
    # Prepare template context
    template_data = prepare_template_context(config, page_data)

    # Execute before_page_render hook
    try:
        from app.plugins import get_plugin_manager
        manager = get_plugin_manager()
        if manager:
            result = manager.hooks.execute('before_page_render', page_data, template_data)
            # If hook returns modified context, use it
            if result is not None and isinstance(result, dict):
                template_data = result
    except Exception as e:
        if logger:
            logger.debug(f'Plugin hook before_page_render error: {e}')

    try:
        html = render_template(template_name, **template_data)

        # Execute after_page_render hook
        try:
            from app.plugins import get_plugin_manager
            manager = get_plugin_manager()
            if manager:
                result = manager.hooks.execute('after_page_render', page_data, html)
                # If hook returns modified HTML, use it
                if result is not None and isinstance(result, str):
                    html = result
        except Exception as e:
            if logger:
                logger.debug(f'Plugin hook after_page_render error: {e}')

        return html

    except Exception as e:
        if logger:
            logger.error(f'Template rendering error for {template_name}: {e}')

        # Check if this is a template not found error
        error_msg = str(e).lower()
        if 'template' in error_msg and ('not found' in error_msg or 'does not exist' in error_msg):
            if logger:
                logger.error(f'Template not found: {template_name}')
            try:
                return render_template('404.html'), 404
            except Exception:
                # If even 404.html is missing, return plain text
                return "404 - Page Not Found", 404

        # For other errors, return 500
        try:
            return render_template('500.html'), 500
        except Exception:
            # If even 500.html is missing, return plain text
            return "500 - Internal Server Error", 500


def render_admin_page_template(template_name, **kwargs):
    """
    Render an admin page template.

    Simplifies admin template rendering with common pattern.

    Args:
        template_name: Name of admin template file
        **kwargs: Additional context variables

    Returns:
        Rendered template HTML
    """
    return render_template(f'admin/{template_name}', **kwargs)
