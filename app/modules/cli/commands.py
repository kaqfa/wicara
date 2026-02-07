"""
CLI commands for WICARA CMS.
Page management and utility commands for command-line use.
"""

import json
import os
import getpass
from werkzeug.security import generate_password_hash
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


def change_password(new_password=None):
    """
    Change admin password via CLI.

    Uses the same validation logic as the admin panel change password form.

    Args:
        new_password: New password (optional). If not provided, prompts securely.

    Returns:
        True if successful, False otherwise
    """
    config = load_config('config.json', validate=False)
    if not config:
        return False

    # Get password securely if not provided
    if new_password is None:
        new_password = getpass.getpass('Enter new admin password: ')
        confirm_password = getpass.getpass('Confirm new admin password: ')
    else:
        confirm_password = new_password

    # Validate password (same logic as PasswordChangeForm in admin/forms.py)
    errors = []

    if not new_password:
        errors.append('New password is required')
    else:
        if len(new_password) < 8:
            errors.append('New password must be at least 8 characters long')
        if not any(c.isupper() for c in new_password):
            errors.append('New password must contain at least one uppercase letter')
        if not any(c.islower() for c in new_password):
            errors.append('New password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in new_password):
            errors.append('New password must contain at least one number')

    # Validate password confirmation
    if new_password != confirm_password:
        errors.append('Password confirmation does not match')

    # Show errors if any
    if errors:
        print('Error: Password validation failed')
        for error in errors:
            print(f'  - {error}')
        return False

    # Hash password with scrypt (same method as admin)
    hashed_password = generate_password_hash(new_password, method='scrypt')
    config['admin-password'] = hashed_password

    if save_config(config, 'config.json', validate=False):
        print('Successfully changed admin password')
        return True
    else:
        print('Error: Failed to save password')
        return False


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
    print('=' * 80)
    print('Usage: python run.py <command> [arguments]')
    print()
    print('Page Management Commands:')
    print('-' * 80)
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
    print('Plugin Management Commands:')
    print('-' * 80)
    print('  plugin-list')
    print('    List all installed plugins with status')
    print('    Example: python run.py plugin-list')
    print()
    print('  plugin-install <source>')
    print('    Install plugin from ZIP file or directory')
    print('    Example: python run.py plugin-install my-plugin.zip')
    print('    Example: python run.py plugin-install /path/to/plugin-dir')
    print()
    print('  plugin-uninstall <name> [--force]')
    print('    Uninstall a plugin')
    print('    Example: python run.py plugin-uninstall my-plugin')
    print('    Example: python run.py plugin-uninstall my-plugin --force')
    print()
    print('  plugin-enable <name>')
    print('    Enable a plugin')
    print('    Example: python run.py plugin-enable my-plugin')
    print()
    print('  plugin-disable <name>')
    print('    Disable a plugin')
    print('    Example: python run.py plugin-disable my-plugin')
    print()
    print('  plugin-info <name>')
    print('    Show detailed plugin information')
    print('    Example: python run.py plugin-info my-plugin')
    print()
    print('Plugin Development Commands:')
    print('-' * 80)
    print('  plugin-create')
    print('    Interactive wizard for creating a new plugin')
    print('    Example: python run.py plugin-create')
    print()
    print('  plugin-validate <name>')
    print('    Validate plugin structure and code')
    print('    Example: python run.py plugin-validate my-plugin')
    print()
    print('  plugin-package <name>')
    print('    Create ZIP package for distribution')
    print('    Example: python run.py plugin-package my-plugin')
    print()
    print('Hook Inspection Commands:')
    print('-' * 80)
    print('  hook-list')
    print('    List all available hooks in Wicara')
    print('    Example: python run.py hook-list')
    print()
    print('  hook-handlers <hook-name>')
    print('    Show registered handlers for a specific hook')
    print('    Example: python run.py hook-handlers before_page_render')
    print()
    print('  hook-stats')
    print('    Show hook execution statistics')
    print('    Example: python run.py hook-stats')
    print()
    print('System Commands:')
    print('-' * 80)
    print('  change-password [password]')
    print('    Change admin password')
    print('    Example: python run.py change-password')
    print('    Example: python run.py change-password "newpassword123"')
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
    print('-' * 80)
    print('  FLASK_ENV      - development, production, or testing (default: development)')
    print('  SECRET_KEY     - Secret key for session management (required in production)')
    print('  LOG_LEVEL      - DEBUG, INFO, WARNING, ERROR (default: INFO)')
    print('  LOG_FILE       - Path to log file (default: logs/wicara.log)')
    print('  HOST           - Server host (default: 0.0.0.0)')
    print('  PORT           - Server port (default: 5555)')
    print()
    print('Configuration:')
    print('-' * 80)
    print('  Config file: config.json')
    print('  Plugin directory: app/plugins/installed/')
    print('  For configuration details, see documentation at /docs')
    print()
