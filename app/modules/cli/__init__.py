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

from app.modules.cli.plugin_commands import (
    plugin_list,
    plugin_install,
    plugin_uninstall,
    plugin_enable,
    plugin_disable,
    plugin_info,
    plugin_create,
    plugin_validate,
    plugin_package,
    hook_list,
    hook_handlers,
    hook_stats
)

__all__ = [
    'create_page',
    'list_pages',
    'delete_page',
    'change_password',
    'show_help',
    # Plugin management
    'plugin_list',
    'plugin_install',
    'plugin_uninstall',
    'plugin_enable',
    'plugin_disable',
    'plugin_info',
    # Plugin development
    'plugin_create',
    'plugin_validate',
    'plugin_package',
    # Hook inspection
    'hook_list',
    'hook_handlers',
    'hook_stats'
]
