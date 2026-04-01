# Plugin CLI Quick Reference

Fast lookup for Wicara plugin CLI commands.

## Plugin Management

| Command | Description | Example |
|---------|-------------|---------|
| `plugin-list` | List all plugins | `python run.py plugin-list` |
| `plugin-install <source>` | Install from ZIP/dir | `python run.py plugin-install my-plugin.zip` |
| `plugin-uninstall <name>` | Uninstall plugin | `python run.py plugin-uninstall my-plugin` |
| `plugin-enable <name>` | Enable plugin | `python run.py plugin-enable my-plugin` |
| `plugin-disable <name>` | Disable plugin | `python run.py plugin-disable my-plugin` |
| `plugin-info <name>` | Show plugin details | `python run.py plugin-info my-plugin` |

## Plugin Development

| Command | Description | Example |
|---------|-------------|---------|
| `plugin-create` | Interactive creation wizard | `python run.py plugin-create` |
| `plugin-validate <name>` | Validate plugin | `python run.py plugin-validate my-plugin` |
| `plugin-package <name>` | Create ZIP package | `python run.py plugin-package my-plugin` |

## Hook Inspection

| Command | Description | Example |
|---------|-------------|---------|
| `hook-list` | List all hooks | `python run.py hook-list` |
| `hook-handlers <name>` | Show hook handlers | `python run.py hook-handlers before_page_render` |
| `hook-stats` | Execution statistics | `python run.py hook-stats` |

## Common Workflows

### Create New Plugin
```bash
python run.py plugin-create
# Follow wizard
python run.py plugin-validate my-plugin
python run.py plugin-package my-plugin
```

### Install Plugin
```bash
python run.py plugin-install plugin.zip
# Restart app
python run.py plugin-list
python run.py plugin-enable plugin-name
```

### Debug Hooks
```bash
python run.py hook-list
python run.py hook-handlers hook-name
python run.py hook-stats
```

## Plugin Types

1. **base** - Basic plugin with hooks
2. **field** - Custom field type
3. **admin** - Admin page extension
4. **filter** - Content filter
5. **cli** - CLI command
6. **cache** - Cache backend
7. **event** - Event listener

## Status Indicators

- `●` **ENABLED** - Plugin is active
- `○` **DISABLED** - Plugin is loaded but inactive
- `×` **NOT LOADED** - Plugin is installed but not loaded

---

For detailed documentation, see `/docs/PLUGIN_CLI_GUIDE.md`
