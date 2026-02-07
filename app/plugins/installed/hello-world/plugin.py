"""
Hello World Plugin - Example plugin demonstrating the Wicara plugin system
"""

from app.plugins import BasePlugin


class HelloWorldPlugin(BasePlugin):
    """
    Simple example plugin that demonstrates:
    - Plugin metadata
    - Hook registration
    - Template filter registration
    """

    def get_metadata(self):
        return {
            'name': 'Hello World',
            'version': '1.0.0',
            'author': 'Wicara Team',
            'description': 'Example plugin demonstrating the Wicara plugin system',
            'min_version': '1.0.0'
        }

    def init(self, app):
        """Initialize plugin with Flask app."""
        app.logger.info('Hello World plugin initialized!')

    def get_hooks(self):
        """Register plugin hooks."""
        return {
            'after_page_render': {
                'handler': self.add_hello_comment,
                'priority': 10
            },
            'register_template_filters': {
                'handler': self.register_filters,
                'priority': 10
            }
        }

    def add_hello_comment(self, page_data, html):
        """
        Add a HTML comment to rendered pages.

        This hook demonstrates how plugins can modify page output.
        """
        comment = '<!-- Hello from Hello World Plugin! -->\n'
        return comment + html

    def register_filters(self):
        """
        Register custom template filters.

        Returns dict of filter functions.
        """
        return {
            'hello': lambda text: f'Hello, {text}!',
            'shout': lambda text: text.upper() + '!!!'
        }
