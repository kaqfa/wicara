# Wicara Plugins

This directory contains installed plugins for the Wicara CMS.

## Plugin Structure

Each plugin must be a Python package with the following structure:

```
plugin-name/
├── __init__.py          # Package initialization
├── plugin.py            # Main plugin class
├── plugin.json          # Plugin manifest (metadata)
├── templates/           # Optional: Plugin templates
├── static/              # Optional: Plugin static files
└── README.md            # Optional: Plugin documentation
```

## Plugin Manifest (plugin.json)

Each plugin must have a `plugin.json` file with the following required fields:

```json
{
  "name": "Plugin Name",
  "version": "1.0.0",
  "author": "Author Name",
  "description": "Plugin description",
  "min_version": "1.0.0"
}
```

Optional fields:
- `max_version`: Maximum Wicara version supported
- `depends_on`: List of plugin dependencies

## Plugin Class

Your main plugin class must inherit from `BasePlugin` and implement these methods:

```python
from app.plugins import BasePlugin

class MyPlugin(BasePlugin):
    def get_metadata(self):
        """Return plugin metadata dict."""
        return {
            'name': 'My Plugin',
            'version': '1.0.0',
            'author': 'John Doe',
            'description': 'My custom plugin'
        }

    def init(self, app):
        """Initialize plugin with Flask app."""
        pass

    def get_hooks(self):
        """Register plugin hooks."""
        return {}
```

## Available Hooks

### Page Hooks
- `before_page_render` - Before page is rendered to HTML
- `after_page_render` - After page is rendered to HTML

### Config Hooks
- `before_config_load` - Before config.json is loaded
- `after_config_load` - After config.json is loaded
- `before_config_save` - Before config.json is saved
- `after_config_save` - After config.json is saved

### Cache Hooks
- `before_cache_clear` - Before cache is cleared
- `after_cache_clear` - After cache is cleared

### Admin Hooks
- `register_admin_menu` - Register custom admin menu items
- `admin_dashboard_stats` - Provide custom stats for admin dashboard

### Field Hooks
- `register_field_types` - Register custom field types
- `validate_field_value` - Validate custom field values

### Template Hooks
- `register_template_filters` - Register custom Jinja2 template filters
- `register_template_globals` - Register custom global template variables

## Example Plugin

See the `hello-world` plugin for a complete example.

## Installing Plugins

### Via Admin UI
1. Go to Admin > Plugins
2. Click "Install Plugin"
3. Upload a plugin ZIP file
4. The plugin will be automatically extracted and installed

### Via CLI (coming soon)
```bash
python run.py plugin-install /path/to/plugin.zip
```

## Managing Plugins

Use the Admin UI at `/admin/plugins/` to:
- View all installed plugins
- Enable/disable plugins
- View plugin details
- Uninstall plugins
- View registered hooks

## Creating Plugins

Use the plugin installer to create a new plugin template:

```python
from app.plugins.installer import PluginInstaller

installer = PluginInstaller('/path/to/plugins')
success, error = installer.create_plugin_template('my-plugin', 'Author Name')
```

## Security Notes

- Plugins run in the same Python environment as Wicara
- Only install plugins from trusted sources
- Review plugin code before installation
- Plugins can access the Flask app and all its resources

## Documentation

For more information, see:
- `/docs/specs/PLUGIN_ECOSYSTEM_DESIGN.md` - Plugin system design
- Example plugins in this directory
