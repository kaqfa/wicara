"""
CLI commands for WICARA CMS.
Page management and utility commands for command-line use.
"""

import json
import os
from app.core import load_config, save_config


def create_page(title, template, url, menu_title=None):
    """
    Create a new page via CLI.

    Args:
        title: Page title
        template: Template file name
        url: Page URL
        menu_title: Menu title (optional)

    Returns:
        True if successful, False otherwise
    """
    config = load_config('config.json', validate=False)
    if not config:
        return False

    # Check if URL already exists
    for page in config.get('pages', []):
        if page.get('url') == url:
            print(f'Error: URL "{url}" already exists')
            return False

    # Create new page
    new_page = {
        'title': title,
        'template': template,
        'url': url,
        'fields': []
    }

    if menu_title:
        new_page['menu-title'] = menu_title

    config['pages'].append(new_page)

    if save_config(config, 'config.json', validate=False):
        print(f'Successfully created page: {title} ({url})')
        return True
    else:
        return False


def list_pages():
    """List all pages via CLI."""
    config = load_config('config.json', validate=False)
    if not config:
        return

    pages = config.get('pages', [])
    if not pages:
        print('No pages found')
        return

    print('\nPages:')
    print('-' * 60)
    for i, page in enumerate(pages, 1):
        title = page.get('title', 'Untitled')
        url = page.get('url', '/no-url')
        template = page.get('template', 'no-template')
        menu_title = page.get('menu-title', title)
        fields_count = len(page.get('fields', []))

        print(f'{i:2d}. {title}')
        print(f'    URL: {url}')
        print(f'    Template: {template}')
        print(f'    Menu Title: {menu_title}')
        print(f'    Fields: {fields_count}')
        print()


def delete_page(url):
    """
    Delete a page by URL via CLI.

    Args:
        url: Page URL to delete

    Returns:
        True if successful, False otherwise
    """
    config = load_config('config.json', validate=False)
    if not config:
        return False

    pages = config.get('pages', [])
    original_count = len(pages)

    # Remove page with matching URL
    config['pages'] = [page for page in pages if page.get('url') != url]

    if len(config['pages']) == original_count:
        print(f'Error: Page with URL "{url}" not found')
        return False

    if save_config(config, 'config.json', validate=False):
        print(f'Successfully deleted page: {url}')
        return True
    else:
        return False


def show_help():
    """Show CLI help."""
    print('Wicara CMS Management Commands')
    print('=' * 60)
    print('Usage: python run.py <command> [arguments]')
    print()
    print('Commands:')
    print()
    print('  create-page <title> <template> <url> [menu-title]')
    print('    Create a new page')
    print('    Example: python run.py create-page "About Us" about.html /about "About"')
    print()
    print('  list-pages')
    print('    List all pages with details')
    print('    Example: python run.py list-pages')
    print()
    print('  delete-page <url>')
    print('    Delete a page by URL')
    print('    Example: python run.py delete-page /about')
    print()
    print('  help')
    print('    Show this help message')
    print('    Example: python run.py help')
    print()
    print('  run')
    print('    Start the web server (default: port 5555)')
    print('    Example: python run.py run')
    print()
    print('Environment Variables:')
    print('  FLASK_ENV      - development, production, or testing (default: development)')
    print('  SECRET_KEY     - Secret key for session management (required in production)')
    print('  LOG_LEVEL      - DEBUG, INFO, WARNING, ERROR (default: INFO)')
    print('  LOG_FILE       - Path to log file (default: logs/wicara.log)')
    print('  HOST           - Server host (default: 0.0.0.0)')
    print('  PORT           - Server port (default: 5555)')
    print()
    print('Configuration:')
    print('  Config file: config.json')
    print('  For configuration details, see documentation at /docs')
    print()
