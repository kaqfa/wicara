# Plugin CLI Commands Guide

Comprehensive guide to using Wicara's plugin management CLI commands.

## Table of Contents

- [Plugin Management Commands](#plugin-management-commands)
- [Plugin Development Commands](#plugin-development-commands)
- [Hook Inspection Commands](#hook-inspection-commands)
- [Examples and Workflows](#examples-and-workflows)

---

## Plugin Management Commands

### plugin-list

List all installed plugins with their status.

```bash
python run.py plugin-list
```

**Output:**
- Plugin name and version
- Author information
- Current status (ENABLED, DISABLED, or NOT LOADED)
- Description
- Package name

**Example Output:**
```
Installed Plugins:
================================================================================

● ENABLED  Rich Text Editor v1.0.0
  Author: Wicara Team
  Description: Add TinyMCE rich text editing to content fields
  Package: rich-text-editor

○ DISABLED  Contact Form v2.1.0
  Author: John Doe
  Description: Add contact forms to pages
  Package: contact-form

================================================================================
Total: 2 plugin(s) installed
Loaded: 1 plugin(s) (1 enabled)
```

---

### plugin-install

Install a plugin from a ZIP file or directory.

```bash
# Install from ZIP file
python run.py plugin-install /path/to/plugin.zip

# Install from directory
python run.py plugin-install /path/to/plugin-directory
```

**Requirements:**
- ZIP files must contain a single plugin directory in the root
- Plugin directory must contain `__init__.py`
- Plugin must have a valid `plugin.json` manifest

**Success:**
```
Installing plugin from: my-plugin.zip
✓ Plugin installed successfully

Next steps:
  1. Run "python run.py plugin-list" to verify installation
  2. Restart the application to load the plugin
```

**Errors:**
- `ZIP file not found` - Path to ZIP doesn't exist
- `Plugin already installed` - Plugin with same name exists
- `ZIP should contain single plugin directory` - Invalid ZIP structure
- `Plugin must contain __init__.py` - Missing required file

---

### plugin-uninstall

Uninstall a plugin from the system.

```bash
# With confirmation prompt
python run.py plugin-uninstall my-plugin

# Skip confirmation
python run.py plugin-uninstall my-plugin --force
```

**Safety Features:**
- Shows plugin details before uninstalling
- Warns if other plugins depend on this plugin
- Asks for confirmation (unless --force flag is used)
- Automatically unloads plugin if currently loaded

**Example:**
```
Plugin to uninstall:
  Name: My Plugin
  Version: 1.0.0
  Author: John Doe

⚠ Warning: The following plugins depend on this plugin:
  - dependent-plugin-1

Are you sure you want to uninstall this plugin? [y/N]: y
✓ Plugin uninstalled successfully
```

---

### plugin-enable

Enable a disabled plugin.

```bash
python run.py plugin-enable my-plugin
```

**Behavior:**
- Loads the plugin if not already loaded
- Enables the plugin for hook execution
- Validates dependencies before enabling

**Example:**
```
Loading plugin: my-plugin
✓ Plugin "my-plugin" enabled successfully
```

---

### plugin-disable

Disable an enabled plugin.

```bash
python run.py plugin-disable my-plugin
```

**Behavior:**
- Keeps plugin loaded but prevents hook execution
- Does not affect plugin files
- Can be re-enabled without restarting application

**Example:**
```
✓ Plugin "my-plugin" disabled successfully
```

---

### plugin-info

Show detailed information about a plugin.

```bash
python run.py plugin-info my-plugin
```

**Output:**
- Basic metadata (name, version, author, status)
- Description
- Dependencies
- Version requirements
- Registered hooks (if loaded)
- File statistics

**Example:**
```
================================================================================
Plugin: My Awesome Plugin
================================================================================
Version: 1.0.0
Author: John Doe
Status: ENABLED

Description:
  This plugin adds awesome functionality to Wicara CMS

Dependencies:
  - base-plugin

Version Requirements:
  Minimum Wicara version: 1.0.0

Hooks Registered: 2
  - before_page_render (priority: 10)
  - after_config_save (priority: 15)

Files:
  Total files: 12
  Size: 45.3 KB
  Location: /path/to/app/plugins/installed/my-plugin

================================================================================
```

---

## Plugin Development Commands

### plugin-create

Interactive wizard for creating a new plugin.

```bash
python run.py plugin-create
```

**Wizard Steps:**

1. **Plugin Name:** Lowercase with hyphens (e.g., `my-awesome-plugin`)
2. **Author Name:** Your name or organization
3. **Description:** Brief description of plugin functionality
4. **Plugin Type:** Choose from 7 types:
   - `base` - Basic plugin (hooks only)
   - `field` - Custom field type
   - `admin` - Admin page extension
   - `filter` - Content filter
   - `cli` - CLI command
   - `cache` - Cache backend
   - `event` - Event listener
5. **Templates:** Include templates directory?
6. **Static Files:** Include static files directory?
7. **Tests:** Include test files?

**Generated Structure:**
```
my-plugin/
├── __init__.py           # Plugin package initialization
├── plugin.py             # Main plugin class (customized by type)
├── plugin.json           # Plugin manifest
├── README.md             # Documentation
├── templates/            # (optional) Template files
│   └── example.html
├── static/               # (optional) Static assets
│   ├── css/
│   └── js/
└── tests/                # (optional) Test files
    └── test_my_plugin.py
```

**Example Session:**
```
=== Plugin Creation Wizard ===

Plugin name (lowercase with hyphens, e.g., my-plugin): analytics-dashboard
Author name: John Doe
Plugin description: Add analytics dashboard to admin panel
Plugin type:
  1. base       - Basic plugin (hooks only)
  2. field      - Custom field type
  3. admin      - Admin page extension
  4. filter     - Content filter
  5. cli        - CLI command
  6. cache      - Cache backend
  7. event      - Event listener
Select plugin type [1]: 3
Include templates directory? [y/N]: y
Include static files directory? [y/N]: y
Include test files? [Y/n]: y

Creating plugin...
✓ Plugin created successfully!

Location: app/plugins/installed/analytics-dashboard

Next steps:
  1. Edit app/plugins/installed/analytics-dashboard/plugin.py to implement your plugin
  2. Run tests: python run.py plugin-validate analytics-dashboard
  3. Package plugin: python run.py plugin-package analytics-dashboard
```

---

### plugin-validate

Validate plugin structure, code, and compatibility.

```bash
python run.py plugin-validate my-plugin
```

**Validation Checks:**
1. Required files exist (`__init__.py`, `plugin.py`)
2. Manifest file (`plugin.json`) is valid JSON
3. Manifest contains required fields
4. Plugin loads successfully
5. Metadata is valid
6. Hooks are recognized
7. Test directory exists

**Example Output:**
```
Validating plugin: my-plugin

Checking required files...
  ✓ __init__.py
  ✓ plugin.py
  ✓ plugin.json

Attempting to load plugin...
  ✓ Plugin loaded successfully

Plugin metadata:
  Name: My Plugin
  Version: 1.0.0
  Author: John Doe

Registered hooks: 2
  ✓ before_page_render
  ✓ after_config_save

Running tests...
  ℹ Tests directory found (manual test run recommended)

================================================================================

✓ Validation passed!

⚠ 1 warning(s):
  - Consider adding more documentation

================================================================================
```

---

### plugin-package

Create a distributable ZIP package of a plugin.

```bash
python run.py plugin-package my-plugin
```

**Behavior:**
- Creates a `dist/` directory if it doesn't exist
- Packages plugin as `plugin-name-version.zip`
- Excludes `__pycache__` and `.pyc` files
- Maintains proper directory structure for installation

**Example:**
```
Packaging plugin: my-plugin
Version: 1.0.0
  Added: my-plugin/__init__.py
  Added: my-plugin/plugin.py
  Added: my-plugin/plugin.json
  Added: my-plugin/README.md
  Added: my-plugin/templates/example.html

✓ Package created successfully!
Location: dist/my-plugin-1.0.0.zip
Size: 12.5 KB
```

---

## Hook Inspection Commands

### hook-list

List all available hooks in Wicara with descriptions.

```bash
python run.py hook-list
```

**Output:**
- Hooks grouped by category
- Description of each hook
- Arguments passed to hook handlers
- Expected return value

**Example Output:**
```
Available Hooks in Wicara:
================================================================================

Page Rendering

  before_page_render
    Description: Before page is rendered to HTML
    Arguments: page_data, context
    Returns: modified context dict

  after_page_render
    Description: After page is rendered to HTML
    Arguments: page_data, html
    Returns: modified html string

Configuration

  before_config_load
    Description: Before config.json is loaded
    Arguments: config_path
    Returns: modified config dict

  after_config_save
    Description: After config.json is saved
    Arguments: config
    Returns: None

...

================================================================================
Total: 15 hooks available
```

---

### hook-handlers

Show which plugins have registered handlers for a specific hook.

```bash
python run.py hook-handlers before_page_render
```

**Output:**
- Hook description and specification
- List of registered handlers
- Execution order (by priority)
- Plugin names

**Example:**
```
================================================================================
Hook: before_page_render
================================================================================
Description: Before page is rendered to HTML
Arguments: page_data, context
Returns: modified context dict

Registered Handlers: (2)

Execution order (by priority):

  1. analytics-plugin
     Priority: 20

  2. seo-optimizer
     Priority: 10

================================================================================
```

**No Handlers:**
```
No handlers registered for this hook
```

---

### hook-stats

Show statistics about hook execution.

```bash
python run.py hook-stats
```

**Output:**
- Total hook executions
- Success rate
- Error count
- Statistics by hook
- Statistics by plugin

**Example:**
```
Hook Execution Statistics:
================================================================================

Total Executions: 245
Success Rate: 98.4%
Errors: 4

By Hook:
  before_page_render: 89 executions (89 success, 0 errors)
  after_page_render: 89 executions (87 success, 2 errors)
  before_config_save: 12 executions (12 success, 0 errors)
  after_config_save: 12 executions (12 success, 0 errors)
  ...

By Plugin:
  analytics-plugin: 120 executions (118 success, 2 errors)
  seo-optimizer: 89 executions (89 success, 0 errors)
  contact-form: 36 executions (34 success, 2 errors)

================================================================================
```

---

## Examples and Workflows

### Complete Plugin Development Workflow

```bash
# 1. Create a new plugin
python run.py plugin-create
# Follow the interactive wizard

# 2. Implement your plugin
# Edit app/plugins/installed/my-plugin/plugin.py

# 3. Validate the plugin
python run.py plugin-validate my-plugin

# 4. Test the plugin
# Restart the application
python run.py

# 5. Check plugin status
python run.py plugin-list

# 6. View plugin details
python run.py plugin-info my-plugin

# 7. Package for distribution
python run.py plugin-package my-plugin
```

### Installing and Managing Third-Party Plugins

```bash
# 1. Install plugin
python run.py plugin-install /path/to/plugin.zip

# 2. Restart application to load
python run.py

# 3. Verify installation
python run.py plugin-list

# 4. Check plugin details
python run.py plugin-info plugin-name

# 5. Enable if disabled
python run.py plugin-enable plugin-name

# 6. Test functionality
# Use the plugin features in the application

# 7. Disable if needed
python run.py plugin-disable plugin-name

# 8. Uninstall if necessary
python run.py plugin-uninstall plugin-name
```

### Debugging Plugin Hooks

```bash
# 1. List all available hooks
python run.py hook-list

# 2. Check which plugins handle a specific hook
python run.py hook-handlers before_page_render

# 3. View execution statistics
python run.py hook-stats

# 4. Validate plugin implementation
python run.py plugin-validate my-plugin

# 5. Check plugin details for hook registration
python run.py plugin-info my-plugin
```

### Maintaining Plugins

```bash
# List all plugins and their status
python run.py plugin-list

# Check for dependency issues
python run.py plugin-info plugin-with-dependencies

# Validate all plugins after Wicara update
for plugin in $(ls app/plugins/installed/); do
  python run.py plugin-validate $plugin
done

# Re-package updated plugin
python run.py plugin-package my-plugin
```

---

## Best Practices

### Plugin Naming
- Use lowercase letters with hyphens
- Be descriptive but concise
- Examples: `rich-text-editor`, `google-analytics`, `contact-form`

### Version Numbering
- Follow semantic versioning (MAJOR.MINOR.PATCH)
- Increment MAJOR for breaking changes
- Increment MINOR for new features
- Increment PATCH for bug fixes

### Testing
- Always include test files in your plugin
- Run `plugin-validate` before packaging
- Test with minimum required Wicara version

### Dependencies
- Minimize dependencies when possible
- Document all dependencies in README
- Test with dependencies disabled to ensure graceful degradation

### Distribution
- Include comprehensive README.md
- Add license information
- Package with `plugin-package` command
- Test installation from ZIP before distribution

---

## Troubleshooting

### Plugin Won't Load

```bash
# 1. Validate plugin structure
python run.py plugin-validate my-plugin

# 2. Check for syntax errors
python -m py_compile app/plugins/installed/my-plugin/plugin.py

# 3. Review error logs
tail -f logs/wicara.log
```

### Hook Not Executing

```bash
# 1. Verify hook name is correct
python run.py hook-list

# 2. Check handler registration
python run.py hook-handlers hook-name

# 3. Verify plugin is enabled
python run.py plugin-list

# 4. Check execution logs
python run.py hook-stats
```

### Installation Fails

```bash
# 1. Check ZIP structure
unzip -l plugin.zip

# 2. Verify manifest
unzip -p plugin.zip plugin-name/plugin.json | python -m json.tool

# 3. Check for name conflicts
python run.py plugin-list
```

---

## Additional Resources

- **Plugin Development Guide:** `/docs/PLUGIN_DEVELOPER_GUIDE.md`
- **Plugin System Architecture:** `/docs/specs/PLUGIN_ECOSYSTEM_DESIGN.md`
- **Hook Reference:** Run `python run.py hook-list`
- **Example Plugins:** `/app/plugins/installed/`

---

**Version:** 1.0.0
**Last Updated:** 2026-02-07
**Maintainer:** Wicara Development Team
