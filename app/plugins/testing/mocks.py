"""
Plugin Testing Framework - Mock Objects

Mock objects for testing plugins in isolation.
"""

from typing import Dict, Any, Optional, List
import os
import tempfile
from unittest.mock import MagicMock


class MockFlaskApp:
    """
    Mock Flask application for plugin testing.

    Provides minimal Flask app interface without requiring actual Flask setup.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize mock Flask app.

        Args:
            config: Optional configuration dict
        """
        self.config = config or {}
        self.extensions = {}
        self.blueprints = {}
        self.logger = MockLogger()
        self.template_folder = tempfile.mkdtemp(prefix='mock_templates_')
        self.static_folder = tempfile.mkdtemp(prefix='mock_static_')
        self.jinja_env = MagicMock()
        self._registered_routes = []
        self._registered_filters = {}
        self._registered_globals = {}

    def register_blueprint(self, blueprint, **kwargs):
        """Mock blueprint registration."""
        blueprint_name = getattr(blueprint, 'name', 'unknown')
        self.blueprints[blueprint_name] = blueprint
        return True

    def route(self, rule, **options):
        """Mock route decorator."""
        def decorator(f):
            self._registered_routes.append({
                'rule': rule,
                'function': f,
                'options': options
            })
            return f
        return decorator

    def add_template_filter(self, func, name=None):
        """Mock template filter registration."""
        filter_name = name or func.__name__
        self._registered_filters[filter_name] = func

    def add_template_global(self, func, name=None):
        """Mock template global registration."""
        global_name = name or func.__name__
        self._registered_globals[global_name] = func

    def get_registered_routes(self) -> List[Dict]:
        """Get list of registered routes."""
        return self._registered_routes

    def get_registered_filters(self) -> Dict[str, callable]:
        """Get registered template filters."""
        return self._registered_filters

    def get_registered_globals(self) -> Dict[str, callable]:
        """Get registered template globals."""
        return self._registered_globals


class MockLogger:
    """Mock logger for testing."""

    def __init__(self):
        self.logs = {
            'debug': [],
            'info': [],
            'warning': [],
            'error': [],
            'critical': []
        }

    def debug(self, msg, *args, **kwargs):
        self.logs['debug'].append(msg)

    def info(self, msg, *args, **kwargs):
        self.logs['info'].append(msg)

    def warning(self, msg, *args, **kwargs):
        self.logs['warning'].append(msg)

    def error(self, msg, *args, **kwargs):
        self.logs['error'].append(msg)

    def critical(self, msg, *args, **kwargs):
        self.logs['critical'].append(msg)

    def get_logs(self, level: str = None) -> List[str]:
        """Get logs for specific level or all logs."""
        if level:
            return self.logs.get(level, [])
        return self.logs

    def clear(self):
        """Clear all logs."""
        for level in self.logs:
            self.logs[level] = []


class MockConfigManager:
    """
    Mock ConfigManager for testing plugins.

    Provides in-memory config without file I/O.
    """

    def __init__(self, initial_config: Optional[Dict[str, Any]] = None):
        """
        Initialize mock config manager.

        Args:
            initial_config: Optional initial configuration
        """
        self._config = initial_config or {
            'sitename': 'Test Site',
            'description': 'Test Description',
            'keywords': ['test'],
            'admin-password': 'test-hash',
            'pages': [],
            'footer': {'content': []}
        }
        self._save_count = 0
        self._load_count = 0

    def load_config(self) -> Dict[str, Any]:
        """Load configuration (from memory)."""
        self._load_count += 1
        return self._config.copy()

    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration (to memory)."""
        self._config = config.copy()
        self._save_count += 1
        return True

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return self._config.copy()

    def update_config(self, updates: Dict[str, Any]):
        """Update configuration with partial data."""
        self._config.update(updates)

    def get_page(self, index: int) -> Optional[Dict[str, Any]]:
        """Get page by index."""
        pages = self._config.get('pages', [])
        if 0 <= index < len(pages):
            return pages[index]
        return None

    def update_page(self, index: int, page_data: Dict[str, Any]) -> bool:
        """Update page at index."""
        pages = self._config.get('pages', [])
        if 0 <= index < len(pages):
            pages[index] = page_data
            return True
        return False

    def add_page(self, page_data: Dict[str, Any]):
        """Add new page."""
        if 'pages' not in self._config:
            self._config['pages'] = []
        self._config['pages'].append(page_data)

    def delete_page(self, index: int) -> bool:
        """Delete page at index."""
        pages = self._config.get('pages', [])
        if 0 <= index < len(pages):
            pages.pop(index)
            return True
        return False

    def get_save_count(self) -> int:
        """Get number of times save was called."""
        return self._save_count

    def get_load_count(self) -> int:
        """Get number of times load was called."""
        return self._load_count


class MockFileManager:
    """
    Mock FileManager for testing file operations.

    Stores files in memory instead of filesystem.
    """

    def __init__(self):
        """Initialize mock file manager."""
        self._files = {}  # filename -> file content
        self._upload_count = 0
        self._delete_count = 0

    def save_file(self, file_content: bytes, filename: str) -> str:
        """
        Mock file save operation.

        Args:
            file_content: File content as bytes
            filename: Desired filename

        Returns:
            Path to saved file (mock path)
        """
        self._files[filename] = file_content
        self._upload_count += 1
        return f"/uploads/{filename}"

    def delete_file(self, filename: str) -> bool:
        """
        Mock file delete operation.

        Args:
            filename: File to delete

        Returns:
            True if deleted, False if not found
        """
        if filename in self._files:
            del self._files[filename]
            self._delete_count += 1
            return True
        return False

    def file_exists(self, filename: str) -> bool:
        """Check if file exists."""
        return filename in self._files

    def get_file(self, filename: str) -> Optional[bytes]:
        """Get file content."""
        return self._files.get(filename)

    def list_files(self) -> List[str]:
        """List all stored files."""
        return list(self._files.keys())

    def get_upload_count(self) -> int:
        """Get number of uploads."""
        return self._upload_count

    def get_delete_count(self) -> int:
        """Get number of deletes."""
        return self._delete_count

    def clear(self):
        """Clear all files."""
        self._files.clear()


class MockTemplateManager:
    """
    Mock TemplateManager for testing template operations.
    """

    def __init__(self):
        """Initialize mock template manager."""
        self._templates = {}  # template_name -> template_content
        self._render_count = 0
        self._last_context = None

    def render_template(self, template_name: str, **context) -> str:
        """
        Mock template rendering.

        Args:
            template_name: Template to render
            **context: Template context

        Returns:
            Rendered HTML (mock)
        """
        self._render_count += 1
        self._last_context = context

        if template_name in self._templates:
            # Simple variable substitution
            content = self._templates[template_name]
            for key, value in context.items():
                placeholder = f"{{{{{key}}}}}"
                content = content.replace(placeholder, str(value))
            return content

        return f"<html><body>Mock template: {template_name}</body></html>"

    def add_template(self, name: str, content: str):
        """Add a mock template."""
        self._templates[name] = content

    def get_render_count(self) -> int:
        """Get number of renders."""
        return self._render_count

    def get_last_context(self) -> Optional[Dict]:
        """Get last render context."""
        return self._last_context


class MockCacheManager:
    """
    Mock CacheManager for testing caching behavior.
    """

    def __init__(self):
        """Initialize mock cache manager."""
        self._cache = {}
        self._get_count = 0
        self._set_count = 0
        self._delete_count = 0

    def get(self, key: str) -> Any:
        """Get value from cache."""
        self._get_count += 1
        return self._cache.get(key)

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        self._cache[key] = value
        self._set_count += 1
        return True

    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if key in self._cache:
            del self._cache[key]
            self._delete_count += 1
            return True
        return False

    def clear(self) -> bool:
        """Clear all cache."""
        self._cache.clear()
        return True

    def exists(self, key: str) -> bool:
        """Check if key exists."""
        return key in self._cache

    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            'get_count': self._get_count,
            'set_count': self._set_count,
            'delete_count': self._delete_count,
            'size': len(self._cache)
        }
