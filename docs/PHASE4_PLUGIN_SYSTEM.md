# Phase 4: Plugin System Implementation Guide

**Status**: 50% Complete (Core Architecture Done, Ecosystem Pending)

---

## Overview

Wicara's plugin system enables community-driven extensibility without requiring core modifications. The system is event-driven with hook-based extension points throughout the application.

### Key Benefits
- ✅ Extend functionality without modifying core code
- ✅ Community-contributed plugins
- ✅ Reduced core complexity
- ✅ Easy feature enablement/disablement
- ✅ Plugin dependency management
- ✅ Version compatibility checking

---

## Architecture

### Core Components

#### 1. **BasePlugin** (`app/plugins/base.py`)
All plugins inherit from `BasePlugin` and must implement:

```python
from app.plugins import BasePlugin

class MyPlugin(BasePlugin):
    def get_metadata(self):
        return {
            'name': 'My Plugin',
            'version': '1.0.0',
            'author': 'John Doe',
            'description': 'Does something cool'
        }

    def init(self, app):
        # Initialize with Flask app
        pass

    def get_hooks(self):
        return {
            'after_config_save': self.on_config_saved
        }

    def on_config_saved(self, config):
        # Handle hook
        pass
```

#### 2. **Hook System** (`app/plugins/hooks.py`)
Event-driven architecture with 15+ defined hooks:

```python
# Register hook with priority
manager.hooks.register(
    'before_page_render',
    my_handler,
    priority=20,  # Higher = runs earlier
    plugin_name='my-plugin'
)

# Execute hooks
result = manager.hooks.execute('before_page_render', page_data, context)

# Execute all hooks and collect results
results = manager.hooks.execute_multiple('register_field_types')
```

#### 3. **PluginManager** (`app/plugins/manager.py`)
Main orchestration system:

```python
from app.plugins import init_plugins

# Initialize in app factory
def create_app():
    app = Flask(__name__)
    manager = init_plugins(app, plugin_dir='app/plugins/installed')

    # Load all plugins
    manager.load_all()

    return app
```

#### 4. **PluginRegistry** (`app/plugins/registry.py`)
Tracks metadata and dependencies:

```python
# Register plugin
registry.register('my-plugin', metadata)

# Validate dependencies
is_ok, missing = registry.validate_dependencies('my-plugin')

# Get dependents
dependents = registry.get_dependents('my-plugin')
```

---

## Available Hooks

### Page Rendering
- `before_page_render`: Before rendering page to HTML
- `after_page_render`: After rendering page

### Configuration
- `before_config_load`: Before loading config.json
- `after_config_load`: After loading config
- `before_config_save`: Before saving config
- `after_config_save`: After saving config

### Caching
- `before_cache_clear`: Before clearing cache
- `after_cache_clear`: After clearing cache

### Import/Export
- `before_export`: Before exporting site
- `after_export`: After export complete
- `before_import`: Before importing
- `after_import`: After import complete

### Admin
- `register_admin_menu`: Register menu items
- `admin_dashboard_stats`: Provide dashboard stats

### Fields
- `register_field_types`: Register custom field types
- `validate_field_value`: Validate custom fields

### CLI
- `register_cli_commands`: Register CLI commands

### Templates
- `register_template_filters`: Register Jinja2 filters
- `register_template_globals`: Register global variables

---

## Plugin Types

### 1. **FieldTypePlugin**
Add custom field types beyond text, textarea, image:

```python
from app.plugins import FieldTypePlugin

class RichTextPlugin(FieldTypePlugin):
    def get_metadata(self):
        return {
            'name': 'Rich Text Editor',
            'version': '1.0.0',
            'author': 'Your Name',
            'description': 'Add rich text editing'
        }

    def get_field_types(self):
        return {
            'rich_text': {
                'label': 'Rich Text',
                'input_template': 'fields/rich_text.html',
                'validator': self.validate_rich_text,
                'display_template': 'fields/rich_text_display.html'
            }
        }

    def validate_rich_text(self, value):
        # Validate value
        return True, None  # (is_valid, error_message)
```

### 2. **AdminPagePlugin**
Add custom admin sections:

```python
from app.plugins import AdminPagePlugin

class AnalyticsPlugin(AdminPagePlugin):
    def register_admin_pages(self):
        return {
            'analytics': {
                'label': 'Analytics',
                'route': '/admin/analytics',
                'template': 'admin/analytics.html',
                'icon': 'chart-bar',
                'order': 5
            }
        }

    def init(self, app):
        @app.route('/admin/analytics')
        def analytics_page():
            return render_template('admin/analytics.html')
```

### 3. **TemplateFilterPlugin**
Register custom Jinja2 filters:

```python
from app.plugins import TemplateFilterPlugin

class TextFiltersPlugin(TemplateFilterPlugin):
    def get_template_filters(self):
        return {
            'capitalize_words': self.capitalize_words,
            'word_count': self.word_count,
            'markdown': self.to_markdown
        }

    def capitalize_words(self, text):
        return ' '.join(w.capitalize() for w in text.split())
```

### 4. **CLICommandPlugin**
Register CLI commands:

```python
from app.plugins import CLICommandPlugin

class BackupPlugin(CLICommandPlugin):
    def register_cli_commands(self):
        return [
            {
                'name': 'backup-full',
                'handler': self.backup_full,
                'help': 'Create full backup',
                'args': []
            }
        ]

    def backup_full(self):
        # Perform backup
        print("Backup created!")
```

### 5. **CacheBackendPlugin**
Add custom cache backends (Redis, Memcached, etc):

```python
from app.plugins import CacheBackendPlugin

class RedisPlugin(CacheBackendPlugin):
    def get_cache_backend(self):
        return {
            'name': 'redis',
            'class': RedisBackend,
            'description': 'Redis distributed cache'
        }
```

### 6. **EventPlugin**
Listen to system events:

```python
from app.plugins import EventPlugin

class NotificationPlugin(EventPlugin):
    def get_hooks(self):
        return {
            'after_config_save': {
                'handler': self.on_config_saved,
                'priority': 10
            },
            'after_import': {
                'handler': self.on_import_complete,
                'priority': 15
            }
        }
```

---

## Plugin Installation

### Directory Structure

```
app/plugins/
    installed/                  # Installed plugins
        my-plugin/
            __init__.py
            plugin.py
            plugin.json        # Manifest
            templates/         # Optional
            static/            # Optional
        rich-text-editor/
            __init__.py
            plugin.py
            plugin.json
            requirements.txt    # Optional
```

### Plugin Manifest (plugin.json)

```json
{
  "name": "My Plugin",
  "version": "1.0.0",
  "author": "John Doe",
  "description": "What this plugin does",
  "depends_on": ["other-plugin"],
  "min_version": "1.0.0",
  "max_version": "2.0.0"
}
```

### Installation Methods

```python
from app.plugins import PluginInstaller

installer = PluginInstaller('app/plugins/installed')

# Install from ZIP
success, error = installer.install_from_zip('plugin.zip', plugin_manager)

# Install from directory
success, error = installer.install_from_directory('/path/to/plugin', plugin_manager)

# Uninstall
success, error = installer.uninstall('plugin-name', plugin_manager)

# Create template
success, error = installer.create_plugin_template('my-plugin', 'John Doe')
```

---

## Plugin Development Workflow

### 1. Create Plugin Template
```bash
python -c "
from app.plugins import PluginInstaller
installer = PluginInstaller('app/plugins/installed')
installer.create_plugin_template('my-plugin', 'Your Name')
"
```

### 2. Develop Plugin
Edit `app/plugins/installed/my-plugin/plugin.py`:
```python
from app.plugins import BasePlugin

class MyPlugin(BasePlugin):
    # Implement required methods
    pass
```

### 3. Test Plugin
```python
from app.plugins import PluginManager

manager = PluginManager()
manager.init_app(app)
plugin = manager.load('my-plugin')
assert plugin is not None
```

### 4. Package & Distribute
```bash
cd app/plugins/installed
zip -r my-plugin.zip my-plugin/
# Share with users
```

---

## Integration with Wicara

### In Application Factory

```python
def create_app():
    app = Flask(__name__)

    # Initialize plugins
    plugin_manager = init_plugins(app)
    plugin_manager.load_all()

    # Plugins automatically register hooks
    # Use hooks throughout application

    return app
```

### Using Hooks in Code

```python
from app.plugins import get_plugin_manager

@app.route('/page/<path>')
def view_page(path):
    # Load and prepare page data
    page_data = load_page(path)

    # Let plugins modify before rendering
    hooks = get_plugin_manager().hooks
    context = hooks.execute('before_page_render', page_data, context)

    # Render template
    html = render_template('page.html', **context)

    # Let plugins modify output
    html = hooks.execute('after_page_render', page_data, html)

    return html
```

---

## Example Plugins

### Contact Form Plugin
```python
class ContactFormPlugin(FieldTypePlugin):
    def get_field_types(self):
        return {
            'contact_form': {
                'label': 'Contact Form',
                'input_template': 'fields/contact_form.html',
                'validator': self.validate_form,
                'display_template': 'fields/contact_form_display.html'
            }
        }
```

### Gallery Plugin
```python
class GalleryPlugin(FieldTypePlugin):
    def get_field_types(self):
        return {
            'gallery': {
                'label': 'Image Gallery',
                'input_template': 'fields/gallery.html',
                'validator': self.validate_gallery,
                'display_template': 'fields/gallery_display.html'
            }
        }
```

### Analytics Plugin
```python
class AnalyticsPlugin(AdminPagePlugin):
    def register_admin_pages(self):
        return {
            'analytics': {
                'label': 'Analytics',
                'route': '/admin/analytics'
            }
        }

    def get_hooks(self):
        return {
            'admin_dashboard_stats': self.get_stats
        }
```

---

## Best Practices

### 1. Keep Plugins Focused
- One main feature per plugin
- Don't try to do everything
- Make plugins composable

### 2. Handle Errors Gracefully
```python
def my_hook(self, data):
    try:
        # Do something
        return modified_data
    except Exception as e:
        logger.error(f"Plugin error: {e}")
        # Return original if error
        return data
```

### 3. Use Dependencies Wisely
- Document dependencies clearly
- Keep dependencies minimal
- Provide helpful error messages

### 4. Test Thoroughly
```python
# Test plugin loading
def test_plugin_loads():
    manager = PluginManager()
    manager.init_app(app)
    plugin = manager.load('my-plugin')
    assert plugin is not None

# Test hooks
def test_hooks():
    result = manager.hooks.execute('my_hook', test_data)
    assert result == expected_result
```

### 5. Follow Conventions
- Use plugin-name format (lowercase, hyphens)
- Version format: MAJOR.MINOR.PATCH
- Document all hooks used
- Include plugin.json manifest

---

## Performance Considerations

### Hook Execution
- Hooks execute in priority order
- Higher priority runs first
- Multiple handlers per hook
- Errors don't stop other handlers

### Plugin Loading
- Lazy loading recommended for performance
- Load on demand if possible
- Cache loaded plugins
- Monitor hook execution time

---

## Security Notes

### Plugin Sandboxing
- Plugins run in main Flask context (no sandboxing)
- Trust-based model - vet plugins carefully
- Monitor file operations
- Validate all inputs

### Permission System
- Future: Per-plugin permissions
- Currently: All plugins have equal access
- Plan: Role-based plugin access control

---

## Next Steps

**Remaining (PLG-05)**:
- Plugin testing framework
- Plugin templates/scaffolding
- Plugin marketplace/registry
- Plugin documentation generator
- Example plugins (rich text, gallery, analytics, contact form)

---

*Last Updated: December 2025*
*Part of Wicara v1.0.0 Advanced Features*
