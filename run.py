#!/usr/bin/env python
"""
WICARA CMS Application Entry Point.
Handles server startup and CLI commands for managing the CMS.
"""

import os
import sys
import json
from pathlib import Path

from app import create_app
from app.utils import load_config, save_config


# ============================================================================
# CLI Management Commands
# ============================================================================

def load_config_cli(config_file='config.json'):
    """
    Load config for CLI use (without Flask context).

    Args:
        config_file: Path to config.json file

    Returns:
        Configuration dictionary or None
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print('Error: Configuration file not found')
        return None
    except json.JSONDecodeError as e:
        print(f'Error: Configuration file is corrupted - {e}')
        return None
    except Exception as e:
        print(f'Error: Unable to load configuration - {e}')
        return None


def save_config_cli(config, config_file='config.json'):
    """
    Save config for CLI use (without Flask context).

    Args:
        config: Configuration dictionary to save
        config_file: Path to config.json file

    Returns:
        True if successful, False otherwise
    """
    try:
        import shutil
        # Create backup before saving
        backup_file = config_file + '.backup'
        if os.path.exists(config_file):
            shutil.copy2(config_file, backup_file)

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f'Error: Unable to save configuration - {e}')
        return False


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
    config = load_config_cli()
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

    if save_config_cli(config):
        print(f'Successfully created page: {title} ({url})')
        return True
    else:
        return False


def list_pages():
    """List all pages via CLI."""
    config = load_config_cli()
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
        print(f'{i:2d}. {title}')
        print(f'    URL: {url}')
        print(f'    Template: {template}')
        print(f'    Menu Title: {menu_title}')
        print()


def delete_page(url):
    """
    Delete a page by URL via CLI.

    Args:
        url: Page URL to delete

    Returns:
        True if successful, False otherwise
    """
    config = load_config_cli()
    if not config:
        return False

    pages = config.get('pages', [])
    original_count = len(pages)

    # Remove page with matching URL
    config['pages'] = [page for page in pages if page.get('url') != url]

    if len(config['pages']) == original_count:
        print(f'Error: Page with URL "{url}" not found')
        return False

    if save_config_cli(config):
        print(f'Successfully deleted page: {url}')
        return True
    else:
        return False


def show_help():
    """Show CLI help."""
    print('Wicara CMS Management Commands')
    print('=' * 40)
    print('Usage: python run.py <command> [arguments]')
    print()
    print('Commands:')
    print('  create-page <title> <template> <url> [menu-title]')
    print('    Create a new page')
    print('    Example: python run.py create-page "About Us" about.html /about "About"')
    print()
    print('  list-pages')
    print('    List all pages')
    print()
    print('  delete-page <url>')
    print('    Delete a page by URL')
    print('    Example: python run.py delete-page /about')
    print()
    print('  help')
    print('    Show this help message')
    print()
    print('  run')
    print('    Start the web server (default: port 5555)')
    print()
    print('Environment Variables:')
    print('  FLASK_ENV: development, production, or testing (default: development)')
    print('  SECRET_KEY: Secret key for session management (required in production)')
    print('  LOG_LEVEL: DEBUG, INFO, WARNING, ERROR (default: INFO)')
    print('  LOG_FILE: Path to log file (default: logs/wicara.log)')


def run_server():
    """Start the Flask development server."""
    app = create_app()
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5555))
    debug = os.environ.get('FLASK_ENV') == 'development'

    app.logger.info(f'Starting server on {host}:{port}')
    app.run(debug=debug, host=host, port=port, use_reloader=debug)


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point for CLI."""
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'create-page':
            if len(sys.argv) < 5:
                print('Error: Missing arguments')
                print('Usage: python run.py create-page <title> <template> <url> [menu-title]')
                sys.exit(1)
            title = sys.argv[2]
            template = sys.argv[3]
            url = sys.argv[4]
            menu_title = sys.argv[5] if len(sys.argv) > 5 else None
            success = create_page(title, template, url, menu_title)
            sys.exit(0 if success else 1)

        elif command == 'list-pages':
            list_pages()

        elif command == 'delete-page':
            if len(sys.argv) < 3:
                print('Error: Missing URL argument')
                print('Usage: python run.py delete-page <url>')
                sys.exit(1)
            url = sys.argv[2]
            success = delete_page(url)
            sys.exit(0 if success else 1)

        elif command == 'help':
            show_help()

        elif command == 'run':
            run_server()

        else:
            print(f'Error: Unknown command "{command}"')
            print('Run "python run.py help" for available commands')
            sys.exit(1)
    else:
        # Default: run the web server
        run_server()


if __name__ == '__main__':
    main()
