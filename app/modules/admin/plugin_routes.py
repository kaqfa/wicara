"""
Plugin management routes for admin panel.

Provides endpoints for viewing, installing, enabling/disabling, and managing plugins.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import logging

from app.modules.auth.utils import login_required
from app.plugins import get_plugin_manager
from app.plugins.installer import PluginInstaller

plugin_bp = Blueprint('plugins', __name__, url_prefix='/admin/plugins')
logger = logging.getLogger(__name__)


@plugin_bp.route('/')
@login_required
def index():
    """
    Plugin dashboard - list all plugins with status.

    Shows installed plugins, their status (enabled/disabled/error),
    and provides quick actions.
    """
    try:
        manager = get_plugin_manager()

        # Get installed plugins
        plugin_dir = manager.plugin_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'plugins', 'installed'
        )
        installer = PluginInstaller(plugin_dir)
        installed = installer.get_installed_plugins()

        # Get loaded plugins
        loaded_plugins = manager.get_all()

        # Build plugin list with status
        plugins = []
        for name, metadata in installed.items():
            plugin_instance = loaded_plugins.get(name)

            status = 'not_loaded'
            enabled = False
            error = None

            if plugin_instance:
                enabled = plugin_instance.is_enabled()
                status = 'enabled' if enabled else 'disabled'

            plugins.append({
                'name': name,
                'metadata': metadata,
                'status': status,
                'enabled': enabled,
                'loaded': plugin_instance is not None,
                'error': error
            })

        # Get statistics
        stats = manager.get_stats()

        return render_template('admin/plugins/index.html',
                             plugins=plugins,
                             stats=stats)

    except Exception as e:
        logger.error(f"Error loading plugin dashboard: {e}", exc_info=True)
        flash('Error loading plugin dashboard', 'error')
        return redirect(url_for('admin.dashboard'))


@plugin_bp.route('/<plugin_name>')
@login_required
def detail(plugin_name):
    """
    Plugin detail page.

    Shows detailed information about a specific plugin including:
    - Metadata
    - Configuration
    - Registered hooks
    - Actions (enable/disable/uninstall)
    """
    try:
        manager = get_plugin_manager()
        plugin = manager.get(plugin_name)

        if not plugin:
            flash(f"Plugin '{plugin_name}' not found or not loaded", 'error')
            return redirect(url_for('plugins.index'))

        # Get metadata
        metadata = plugin.get_metadata()

        # Get registered hooks
        hooks = plugin.get_hooks()
        hook_info = []
        for hook_name, hook_def in hooks.items():
            if isinstance(hook_def, dict):
                priority = hook_def.get('priority', 10)
            else:
                priority = 10

            hook_info.append({
                'name': hook_name,
                'priority': priority
            })

        # Get config schema if available
        config_schema = plugin.get_config_schema()

        return render_template('admin/plugins/detail.html',
                             plugin_name=plugin_name,
                             plugin=plugin,
                             metadata=metadata,
                             hooks=hook_info,
                             config_schema=config_schema,
                             enabled=plugin.is_enabled())

    except Exception as e:
        logger.error(f"Error loading plugin detail: {e}", exc_info=True)
        flash('Error loading plugin details', 'error')
        return redirect(url_for('plugins.index'))


@plugin_bp.route('/<plugin_name>/enable', methods=['POST'])
@login_required
def enable(plugin_name):
    """Enable a plugin."""
    try:
        manager = get_plugin_manager()

        if not manager.get(plugin_name):
            return jsonify({'success': False, 'error': 'Plugin not loaded'}), 404

        success = manager.enable(plugin_name)

        if success:
            logger.info(f"Plugin enabled: {plugin_name}")
            flash(f"Plugin '{plugin_name}' enabled successfully", 'success')
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to enable plugin'}), 500

    except Exception as e:
        logger.error(f"Error enabling plugin: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@plugin_bp.route('/<plugin_name>/disable', methods=['POST'])
@login_required
def disable(plugin_name):
    """Disable a plugin."""
    try:
        manager = get_plugin_manager()

        if not manager.get(plugin_name):
            return jsonify({'success': False, 'error': 'Plugin not loaded'}), 404

        success = manager.disable(plugin_name)

        if success:
            logger.info(f"Plugin disabled: {plugin_name}")
            flash(f"Plugin '{plugin_name}' disabled successfully", 'success')
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to disable plugin'}), 500

    except Exception as e:
        logger.error(f"Error disabling plugin: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@plugin_bp.route('/<plugin_name>/uninstall', methods=['POST'])
@login_required
def uninstall(plugin_name):
    """Uninstall a plugin."""
    try:
        manager = get_plugin_manager()
        plugin_dir = manager.plugin_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'plugins', 'installed'
        )
        installer = PluginInstaller(plugin_dir)

        success, error = installer.uninstall(plugin_name, manager)

        if success:
            logger.info(f"Plugin uninstalled: {plugin_name}")
            flash(f"Plugin '{plugin_name}' uninstalled successfully", 'success')
            return jsonify({'success': True})
        else:
            logger.error(f"Failed to uninstall plugin: {error}")
            return jsonify({'success': False, 'error': error}), 500

    except Exception as e:
        logger.error(f"Error uninstalling plugin: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@plugin_bp.route('/install', methods=['GET', 'POST'])
@login_required
def install():
    """
    Install plugin wizard.

    GET: Show install form
    POST: Handle plugin installation from ZIP file
    """
    if request.method == 'GET':
        return render_template('admin/plugins/install.html')

    try:
        # Check if file was uploaded
        if 'plugin_file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(url_for('plugins.install'))

        file = request.files['plugin_file']

        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('plugins.install'))

        if not file.filename.endswith('.zip'):
            flash('Only ZIP files are allowed', 'error')
            return redirect(url_for('plugins.install'))

        # Save uploaded file
        filename = secure_filename(file.filename)
        upload_dir = os.path.join(current_app.root_path, '..', 'temp_uploads')
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)

        # Install plugin
        manager = get_plugin_manager()
        plugin_dir = manager.plugin_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'plugins', 'installed'
        )
        installer = PluginInstaller(plugin_dir)

        success, error = installer.install_from_zip(filepath, manager)

        # Cleanup temp file
        try:
            os.remove(filepath)
        except:
            pass

        if success:
            logger.info(f"Plugin installed from {filename}")
            flash('Plugin installed successfully! Please reload the page to see it.', 'success')
            return redirect(url_for('plugins.index'))
        else:
            logger.error(f"Plugin installation failed: {error}")
            flash(f'Plugin installation failed: {error}', 'error')
            return redirect(url_for('plugins.install'))

    except Exception as e:
        logger.error(f"Error installing plugin: {e}", exc_info=True)
        flash(f'Error installing plugin: {str(e)}', 'error')
        return redirect(url_for('plugins.install'))


@plugin_bp.route('/hooks')
@login_required
def hooks():
    """
    View all registered hooks.

    Shows all available hooks and their registered handlers
    from loaded plugins.
    """
    try:
        manager = get_plugin_manager()

        # Get all defined hooks
        defined_hooks = manager.hooks.get_defined_hooks()

        # Build hooks info with handlers
        hooks_info = []
        for hook_name, hook_spec in defined_hooks.items():
            handlers = manager.hooks.get_handlers(hook_name)

            hooks_info.append({
                'name': hook_name,
                'description': hook_spec.get('description', ''),
                'args': hook_spec.get('args', []),
                'returns': hook_spec.get('returns', 'None'),
                'handlers': handlers,
                'handler_count': len(handlers)
            })

        # Sort by name
        hooks_info.sort(key=lambda x: x['name'])

        return render_template('admin/plugins/hooks.html',
                             hooks=hooks_info,
                             total_hooks=len(hooks_info),
                             total_handlers=sum(h['handler_count'] for h in hooks_info))

    except Exception as e:
        logger.error(f"Error loading hooks: {e}", exc_info=True)
        flash('Error loading hooks', 'error')
        return redirect(url_for('plugins.index'))


@plugin_bp.route('/api/load/<plugin_name>', methods=['POST'])
@login_required
def load_plugin(plugin_name):
    """Load a plugin dynamically."""
    try:
        manager = get_plugin_manager()

        plugin = manager.load(plugin_name)

        if plugin:
            logger.info(f"Plugin loaded: {plugin_name}")
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to load plugin'}), 500

    except Exception as e:
        logger.error(f"Error loading plugin: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
