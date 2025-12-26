"""
Hook System - PLG-02

Event-driven plugin system with priority-based hook execution.
Allows plugins to extend functionality at defined extension points.
"""

from typing import Dict, List, Callable, Any, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# CORE HOOKS - Extension points in Wicara
# ============================================================================

CORE_HOOKS = {
    # Page Rendering Hooks
    'before_page_render': {
        'description': 'Before page is rendered to HTML',
        'args': ['page_data', 'context'],
        'returns': 'modified context dict'
    },
    'after_page_render': {
        'description': 'After page is rendered to HTML',
        'args': ['page_data', 'html'],
        'returns': 'modified html string'
    },

    # Configuration Hooks
    'before_config_load': {
        'description': 'Before config.json is loaded',
        'args': ['config_path'],
        'returns': 'modified config dict'
    },
    'after_config_load': {
        'description': 'After config.json is loaded',
        'args': ['config'],
        'returns': 'modified config dict'
    },
    'before_config_save': {
        'description': 'Before config.json is saved',
        'args': ['config'],
        'returns': 'modified config dict'
    },
    'after_config_save': {
        'description': 'After config.json is saved',
        'args': ['config'],
        'returns': None
    },

    # Cache Hooks
    'before_cache_clear': {
        'description': 'Before cache is cleared',
        'args': ['cache_type'],
        'returns': 'modified cache_type or None to skip'
    },
    'after_cache_clear': {
        'description': 'After cache is cleared',
        'args': ['cache_type'],
        'returns': None
    },

    # Import/Export Hooks
    'before_export': {
        'description': 'Before site export',
        'args': ['export_mode', 'config'],
        'returns': 'modified config dict'
    },
    'after_export': {
        'description': 'After site export',
        'args': ['export_path', 'manifest'],
        'returns': None
    },
    'before_import': {
        'description': 'Before site import',
        'args': ['import_path', 'import_data'],
        'returns': 'modified import_data dict'
    },
    'after_import': {
        'description': 'After site import',
        'args': ['import_data', 'config'],
        'returns': None
    },

    # Admin Hooks
    'register_admin_menu': {
        'description': 'Register custom admin menu items',
        'args': [],
        'returns': 'list of menu items'
    },
    'admin_dashboard_stats': {
        'description': 'Provide custom stats for admin dashboard',
        'args': [],
        'returns': 'dict with stats'
    },

    # Field Hooks
    'register_field_types': {
        'description': 'Register custom field types',
        'args': [],
        'returns': 'dict of field type definitions'
    },
    'validate_field_value': {
        'description': 'Validate custom field values',
        'args': ['field_type', 'value'],
        'returns': 'tuple (is_valid, error_message)'
    },

    # CLI Hooks
    'register_cli_commands': {
        'description': 'Register custom CLI commands',
        'args': [],
        'returns': 'list of command definitions'
    },

    # Template Hooks
    'register_template_filters': {
        'description': 'Register custom Jinja2 template filters',
        'args': [],
        'returns': 'dict of filter functions'
    },
    'register_template_globals': {
        'description': 'Register custom global template variables',
        'args': [],
        'returns': 'dict of global variables'
    },
}


# ============================================================================
# HOOK DISPATCHER - Manages hook registration and execution
# ============================================================================

class HookDispatcher:
    """
    Manages plugin hooks with priority-based execution.

    Features:
    - Register hooks with priority (higher = executes earlier)
    - Execute hooks in priority order
    - Error handling and logging
    - Hook validation
    """

    def __init__(self):
        """Initialize hook dispatcher."""
        self.hooks: Dict[str, List[tuple]] = defaultdict(list)  # hook_name -> [(priority, callback), ...]
        self.defined_hooks = set(CORE_HOOKS.keys())
        self._execution_log = []

    def register(self, hook_name: str, callback: Callable, priority: int = 10, plugin_name: str = None):
        """
        Register a hook handler.

        Args:
            hook_name: Name of the hook
            callback: Function to call when hook executes
            priority: Execution priority (higher = earlier, default: 10)
            plugin_name: Name of plugin registering hook (for logging)

        Raises:
            ValueError: If hook_name is not defined
        """
        if hook_name not in self.defined_hooks:
            raise ValueError(f"Hook '{hook_name}' is not defined. Valid hooks: {self.defined_hooks}")

        if not callable(callback):
            raise ValueError(f"Hook callback must be callable, got {type(callback)}")

        self.hooks[hook_name].append((priority, callback, plugin_name or 'unknown'))
        # Sort by priority (descending)
        self.hooks[hook_name].sort(key=lambda x: x[0], reverse=True)

        logger.debug(f"Registered hook '{hook_name}' with priority {priority} from plugin '{plugin_name or 'unknown'}'")

    def unregister(self, hook_name: str, callback: Callable):
        """Unregister a hook handler."""
        if hook_name in self.hooks:
            self.hooks[hook_name] = [
                (p, cb, name) for p, cb, name in self.hooks[hook_name]
                if cb != callback
            ]

    def execute(self, hook_name: str, *args, **kwargs) -> Any:
        """
        Execute hook handlers in priority order.

        Args:
            hook_name: Name of the hook to execute
            *args: Positional arguments to pass to handlers
            **kwargs: Keyword arguments to pass to handlers

        Returns:
            Last handler's return value (or None if no handlers)

        Raises:
            ValueError: If hook_name is not defined
        """
        if hook_name not in self.defined_hooks:
            raise ValueError(f"Hook '{hook_name}' is not defined")

        if hook_name not in self.hooks:
            return None

        result = None
        handlers = self.hooks[hook_name]

        for priority, callback, plugin_name in handlers:
            try:
                result = callback(*args, **kwargs)
                self._execution_log.append({
                    'hook': hook_name,
                    'plugin': plugin_name,
                    'priority': priority,
                    'status': 'success'
                })
            except Exception as e:
                logger.error(f"Error executing hook '{hook_name}' in plugin '{plugin_name}': {e}")
                self._execution_log.append({
                    'hook': hook_name,
                    'plugin': plugin_name,
                    'priority': priority,
                    'status': 'error',
                    'error': str(e)
                })

        return result

    def execute_multiple(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """
        Execute hook handlers and collect all results.

        Args:
            hook_name: Name of the hook to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            List of return values from all handlers
        """
        if hook_name not in self.defined_hooks:
            raise ValueError(f"Hook '{hook_name}' is not defined")

        if hook_name not in self.hooks:
            return []

        results = []
        handlers = self.hooks[hook_name]

        for priority, callback, plugin_name in handlers:
            try:
                result = callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Error executing hook '{hook_name}' in plugin '{plugin_name}': {e}")

        return results

    def get_handlers(self, hook_name: str) -> List[Dict[str, Any]]:
        """
        Get list of registered handlers for a hook.

        Args:
            hook_name: Name of the hook

        Returns:
            List of handler info dicts
        """
        if hook_name not in self.hooks:
            return []

        return [
            {
                'plugin': name,
                'priority': priority,
                'callback': callback
            }
            for priority, callback, name in self.hooks[hook_name]
        ]

    def get_execution_log(self) -> List[Dict[str, Any]]:
        """Get log of hook executions."""
        return self._execution_log

    def clear_execution_log(self):
        """Clear execution log."""
        self._execution_log = []

    def unregister_all(self, hook_name: str = None):
        """
        Clear all hooks or hooks for specific hook name.

        Args:
            hook_name: Specific hook to clear, or None to clear all
        """
        if hook_name:
            self.hooks[hook_name] = []
        else:
            self.hooks.clear()

    def get_defined_hooks(self) -> Dict[str, Dict[str, Any]]:
        """Get all defined hooks with their specifications."""
        return CORE_HOOKS

    def __repr__(self) -> str:
        total_handlers = sum(len(handlers) for handlers in self.hooks.values())
        return f"<HookDispatcher: {len(self.hooks)} active hooks, {total_handlers} handlers>"
