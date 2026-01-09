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
from app.modules.cli import create_page, list_pages, delete_page, change_password, show_help


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

        elif command == 'change-password':
            new_password = sys.argv[2] if len(sys.argv) > 2 else None
            success = change_password(new_password)
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
