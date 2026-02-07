"""Test plugin for Wicara CMS - Verifies plugin system integration."""

from app.plugins.base import BasePlugin


class TestPlugin(BasePlugin):
    """Simple test plugin to verify plugin system is working."""

    def get_metadata(self):
        """Return plugin metadata."""
        return {
            'name': 'Test Plugin',
            'version': '1.0.0',
            'author': 'Wicara Team',
            'description': 'Simple test plugin to verify plugin system integration',
            'requires_wicara': '>=1.0.0'
        }

    def init(self, app):
        """Initialize plugin with Flask app."""
        app.logger.info(f"Test Plugin initialized: {self.get_metadata()['name']}")

    def get_hooks(self):
        """Register hooks for testing."""
        return {
            'after_config_load': {
                'handler': self.test_config_hook,
                'priority': 10
            },
            'after_page_render': {
                'handler': self.test_page_hook,
                'priority': 10
            },
            'register_template_filters': {
                'handler': self.register_filters,
                'priority': 10
            }
        }

    def test_config_hook(self, config):
        """Test hook for config loading."""
        if self.app:
            self.app.logger.debug(f"Test Plugin: Config loaded with {len(config.get('pages', []))} pages")
        return None  # Don't modify config

    def test_page_hook(self, page_data, html):
        """Test hook for page rendering."""
        if self.app:
            self.app.logger.debug(f"Test Plugin: Page rendered")
        return None  # Don't modify HTML

    def register_filters(self):
        """Register custom template filters."""
        return {
            'test_filter': lambda x: f"[TEST: {x}]"
        }
