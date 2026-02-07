#!/usr/bin/env python
"""
WICARA CMS Application Entry Point.
Handles server startup and CLI commands for managing the CMS.
Implements ARC-04: Environment-based configuration with .env file support.
"""

import os
import sys
from pathlib import Path

from app import create_app
from app.core.site_manager import SiteManager
from app.modules.cli import (
    create_page, list_pages, delete_page, change_password, show_help,
    plugin_list, plugin_install, plugin_uninstall, plugin_enable, plugin_disable,
    plugin_info, plugin_create, plugin_validate, plugin_package,
    hook_list, hook_handlers, hook_stats
)


# ============================================================================
# Environment Configuration with .env Support
# ============================================================================

def load_env_file(env_file='.env'):
    """
    Load environment variables from .env file.

    Supports common environment file format.

    Args:
        env_file: Path to .env file

    Returns:
        Number of variables loaded
    """
    count = 0
    if not os.path.exists(env_file):
        return count

    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue

                # Parse KEY=VALUE pairs
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]

                    # Only set if not already in environment
                    if key and key not in os.environ:
                        os.environ[key] = value
                        count += 1

        return count
    except Exception as e:
        print(f'Warning: Could not load .env file: {e}')
        return count


# ============================================================================
# Application Server
# ============================================================================

def run_server():
    """Start the Flask development server with hot reload in development mode."""
    app = create_app()
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5555))
    env = os.environ.get('FLASK_ENV', 'development')
    debug = env == 'development'

    app.logger.info(f'Starting server on {host}:{port} (debug={debug}, hot_reload={debug})')
    app.run(debug=debug, host=host, port=port, use_reloader=debug)


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point for CLI."""
    # Load .env file if it exists (ARC-04)
    env_loaded = load_env_file('.env')
    if env_loaded > 0:
        print(f'Loaded {env_loaded} environment variable(s) from .env file')

    # Initialize SiteManager for CLI context (ECS-10)
    # Use environment variable LEGACY_MODE to determine mode (defaults to True for backward compatibility)
    legacy_mode = os.environ.get('LEGACY_MODE', 'true').lower() in ['true', '1', 'yes']
    sites_dir = os.environ.get('SITES_DIR', 'sites')
    default_site = os.environ.get('DEFAULT_SITE', 'default')

    site_manager = SiteManager(
        sites_dir=sites_dir,
        default_site=default_site,
        legacy_mode=legacy_mode
    )

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
            success = create_page(title, template, url, menu_title, site_manager=site_manager)
            sys.exit(0 if success else 1)

        elif command == 'list-pages':
            list_pages(site_manager=site_manager)

        elif command == 'delete-page':
            if len(sys.argv) < 3:
                print('Error: Missing URL argument')
                print('Usage: python run.py delete-page <url>')
                sys.exit(1)
            url = sys.argv[2]
            success = delete_page(url, site_manager=site_manager)
            sys.exit(0 if success else 1)

        elif command == 'change-password':
            new_password = sys.argv[2] if len(sys.argv) > 2 else None
            success = change_password(new_password, site_manager=site_manager)
            sys.exit(0 if success else 1)

        elif command == 'help':
            show_help()

        elif command == 'run':
            run_server()

        # Plugin Management Commands
        elif command == 'plugin-list':
            plugin_list()

        elif command == 'plugin-install':
            if len(sys.argv) < 3:
                print('Error: Missing source argument')
                print('Usage: python run.py plugin-install <source>')
                print('  source: Path to ZIP file or plugin directory')
                sys.exit(1)
            source = sys.argv[2]
            success = plugin_install(source)
            sys.exit(0 if success else 1)

        elif command == 'plugin-uninstall':
            if len(sys.argv) < 3:
                print('Error: Missing plugin name argument')
                print('Usage: python run.py plugin-uninstall <name> [--force]')
                sys.exit(1)
            plugin_name = sys.argv[2]
            force = '--force' in sys.argv or '-f' in sys.argv
            success = plugin_uninstall(plugin_name, force)
            sys.exit(0 if success else 1)

        elif command == 'plugin-enable':
            if len(sys.argv) < 3:
                print('Error: Missing plugin name argument')
                print('Usage: python run.py plugin-enable <name>')
                sys.exit(1)
            plugin_name = sys.argv[2]
            success = plugin_enable(plugin_name)
            sys.exit(0 if success else 1)

        elif command == 'plugin-disable':
            if len(sys.argv) < 3:
                print('Error: Missing plugin name argument')
                print('Usage: python run.py plugin-disable <name>')
                sys.exit(1)
            plugin_name = sys.argv[2]
            success = plugin_disable(plugin_name)
            sys.exit(0 if success else 1)

        elif command == 'plugin-info':
            if len(sys.argv) < 3:
                print('Error: Missing plugin name argument')
                print('Usage: python run.py plugin-info <name>')
                sys.exit(1)
            plugin_name = sys.argv[2]
            success = plugin_info(plugin_name)
            sys.exit(0 if success else 1)

        # Plugin Development Commands
        elif command == 'plugin-create':
            success = plugin_create()
            sys.exit(0 if success else 1)

        elif command == 'plugin-validate':
            if len(sys.argv) < 3:
                print('Error: Missing plugin name argument')
                print('Usage: python run.py plugin-validate <name>')
                sys.exit(1)
            plugin_name = sys.argv[2]
            success = plugin_validate(plugin_name)
            sys.exit(0 if success else 1)

        elif command == 'plugin-package':
            if len(sys.argv) < 3:
                print('Error: Missing plugin name argument')
                print('Usage: python run.py plugin-package <name>')
                sys.exit(1)
            plugin_name = sys.argv[2]
            success = plugin_package(plugin_name)
            sys.exit(0 if success else 1)

        # Hook Inspection Commands
        elif command == 'hook-list':
            hook_list()

        elif command == 'hook-handlers':
            if len(sys.argv) < 3:
                print('Error: Missing hook name argument')
                print('Usage: python run.py hook-handlers <hook-name>')
                sys.exit(1)
            hook_name = sys.argv[2]
            success = hook_handlers(hook_name)
            sys.exit(0 if success else 1)

        elif command == 'hook-stats':
            hook_stats()

        elif command == 'migrate':
            # Import migration script
            try:
                sys.path.insert(0, str(Path(__file__).parent))
                from scripts.migrate_to_sites import migrate_to_sites
                success = migrate_to_sites()
                sys.exit(0 if success else 1)
            except ImportError as e:
                print(f'Error: Could not import migration script: {e}')
                print('Make sure scripts/migrate_to_sites.py exists')
                sys.exit(1)

        else:
            print(f'Error: Unknown command "{command}"')
            print('Run "python run.py help" for available commands')
            sys.exit(1)
    else:
        # Default: run the web server
        run_server()


if __name__ == '__main__':
    main()
