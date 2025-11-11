"""
WICARA Core Module: Template Manager
Handles template rendering and data conversion for Jinja2.
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

    Args:
        template_name: Name of template file to render
        config: Global configuration dictionary
        page_data: Page-specific data (optional)
        logger: Logger instance for logging (optional)

    Returns:
        Tuple of (rendered_html, status_code) or error response tuple
    """
    # Check if template exists
    template_path = os.path.join('templates', template_name)
    if not os.path.exists(template_path):
        if logger:
            logger.error(f'Template not found: {template_name}')
        return render_template('404.html'), 404

    # Prepare template context
    template_data = prepare_template_context(config, page_data)

    try:
        return render_template(template_name, **template_data)
    except Exception as e:
        if logger:
            logger.error(f'Template rendering error for {template_name}: {e}')
        return render_template('500.html'), 500


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
