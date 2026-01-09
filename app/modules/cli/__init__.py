"""
WICARA CLI Module
Command-line interface for CMS management.
"""

from app.modules.cli.commands import (
    create_page,
    list_pages,
    delete_page,
    change_password,
    show_help
)

__all__ = [
    'create_page',
    'list_pages',
    'delete_page',
    'change_password',
    'show_help'
]
