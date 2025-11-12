"""
Import/Export routes blueprint for WICARA CMS (MIG-05).

Handles:
- Export wizard with filtering options
- Import wizard with preview and conflict resolution
- Bulk operations support
- Import/export history and logs
"""

import os
import json
from datetime import datetime
from functools import wraps

from flask import (
    Blueprint, render_template, request, redirect, url_for, session, flash,
    current_app, send_file, jsonify
)
from werkzeug.utils import secure_filename

from app.modules.import_export import Exporter, Importer, VersionMigrator


# Create blueprint
import_export_bp = Blueprint('import_export', __name__, url_prefix='/admin/import-export')


def login_required(f):
    """Decorator to check if user is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# Export Routes
# ============================================================================

@import_export_bp.route('/export', methods=['GET', 'POST'])
@login_required
def export_page():
    """Export wizard page."""
    if request.method == 'POST':
        try:
            # Get export options
            mode = request.form.get('export_mode', Exporter.EXPORT_FULL)
            include_templates = request.form.getlist('templates')

            # Validate mode
            valid_modes = [Exporter.EXPORT_FULL, Exporter.EXPORT_PARTIAL, Exporter.EXPORT_CONTENT]
            if mode not in valid_modes:
                flash(f'Invalid export mode: {mode}', 'error')
                return redirect(url_for('import_export.export_page'))

            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"wicara_export_{timestamp}.zip"
            filepath = os.path.join(current_app.config.get('EXPORT_DIR', 'exports'), filename)

            # Create exports directory if needed
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Create exporter
            config_path = current_app.config['CONFIG_FILE']
            exporter = Exporter(config_path=config_path)

            # Perform export
            success, message, stats = exporter.export(
                filepath,
                mode=mode,
                include_templates=include_templates if include_templates else None
            )

            if not success:
                flash(f'Export failed: {message}', 'error')
                current_app.logger.error(f'Export error: {message}')
                return redirect(url_for('import_export.export_page'))

            # Log export
            current_app.logger.info(f'Export successful: {filename}, Stats: {stats}')
            flash('Export completed successfully. Your file is ready for download.', 'success')

            # Store filename in session for download
            session['export_filename'] = filename
            session['export_filepath'] = filepath

            return redirect(url_for('import_export.download_export'))

        except Exception as e:
            flash(f'Export error: {str(e)}', 'error')
            current_app.logger.error(f'Unexpected export error: {str(e)}')
            return redirect(url_for('import_export.export_page'))

    # GET request: show export wizard
    config_path = current_app.config['CONFIG_FILE']
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        pages = config.get('pages', [])
        templates = list({p.get('template') for p in pages if p.get('template')})
    except:
        pages = []
        templates = []

    return render_template(
        'admin/import_export/export.html',
        pages=pages,
        templates=templates,
        export_modes=[
            ('full', 'Full Export (All files)'),
            ('partial', 'Partial Export (Config + Templates)'),
            ('content', 'Content Only (Config only)')
        ]
    )


@import_export_bp.route('/download')
@login_required
def download_export():
    """Download exported file."""
    filepath = session.get('export_filepath')
    filename = session.get('export_filename')

    if not filepath or not filename:
        flash('No export file available', 'error')
        return redirect(url_for('import_export.export_page'))

    if not os.path.exists(filepath):
        flash('Export file not found', 'error')
        return redirect(url_for('import_export.export_page'))

    try:
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        flash(f'Download error: {str(e)}', 'error')
        current_app.logger.error(f'Download error: {str(e)}')
        return redirect(url_for('import_export.export_page'))
    finally:
        # Clear session
        session.pop('export_filename', None)
        session.pop('export_filepath', None)


# ============================================================================
# Import Routes
# ============================================================================

@import_export_bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_page():
    """Import wizard page."""
    if request.method == 'POST':
        # Check if file was provided
        if 'import_file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('import_export.import_page'))

        file = request.files['import_file']
        if not file.filename:
            flash('No file selected', 'error')
            return redirect(url_for('import_export.import_page'))

        try:
            # Save uploaded file temporarily
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
                file.save(tmp.name)
                tmp_path = tmp.name

            # Validate ZIP
            valid, msg = Exporter.validate_export_package(tmp_path)
            if not valid:
                flash(f'Invalid export package: {msg}', 'error')
                os.unlink(tmp_path)
                return redirect(url_for('import_export.import_page'))

            # Store temp file path in session for next step
            session['import_temp_file'] = tmp_path
            session['import_filename'] = secure_filename(file.filename)

            flash('File validated successfully. Review options and confirm import.', 'info')
            return redirect(url_for('import_export.import_preview'))

        except Exception as e:
            flash(f'File upload error: {str(e)}', 'error')
            current_app.logger.error(f'Import upload error: {str(e)}')
            return redirect(url_for('import_export.import_page'))

    return render_template('admin/import_export/import.html')


@import_export_bp.route('/import/preview')
@login_required
def import_preview():
    """Import preview page."""
    tmp_file = session.get('import_temp_file')
    if not tmp_file:
        flash('No import file selected', 'error')
        return redirect(url_for('import_export.import_page'))

    try:
        # Load import data for preview
        import zipfile
        with zipfile.ZipFile(tmp_file, 'r') as zf:
            config_data = zf.read('config.json')
            imported_config = json.loads(config_data)

            manifest_data = zf.read('manifest.json')
            manifest = json.loads(manifest_data)

        # Load current config for comparison
        config_path = current_app.config['CONFIG_FILE']
        with open(config_path, 'r', encoding='utf-8') as f:
            current_config = json.load(f)

        # Generate preview
        importer = Importer(config_path=config_path)
        preview = importer._generate_import_preview(
            current_config,
            imported_config,
            'merge'
        )

        return render_template(
            'admin/import_export/import_preview.html',
            manifest=manifest,
            imported_config=imported_config,
            current_config=current_config,
            preview=preview,
            conflict_strategies=[
                ('merge', 'Merge (Keep existing pages)'),
                ('replace', 'Replace (Overwrite all)'),
                ('skip', 'Skip (No conflicts)'),
            ]
        )

    except Exception as e:
        flash(f'Preview error: {str(e)}', 'error')
        current_app.logger.error(f'Import preview error: {str(e)}')
        return redirect(url_for('import_export.import_page'))


@import_export_bp.route('/import/confirm', methods=['POST'])
@login_required
def import_confirm():
    """Confirm and execute import."""
    tmp_file = session.get('import_temp_file')
    if not tmp_file:
        flash('No import file available', 'error')
        return redirect(url_for('import_export.import_page'))

    try:
        # Get import options
        conflict_strategy = request.form.get('conflict_strategy', 'merge')
        import_templates = request.form.get('import_templates') == 'on'
        import_images = request.form.get('import_images') == 'on'

        # Validate strategy
        valid_strategies = ['merge', 'replace', 'skip']
        if conflict_strategy not in valid_strategies:
            flash('Invalid conflict strategy', 'error')
            return redirect(url_for('import_export.import_preview'))

        # Create importer
        config_path = current_app.config['CONFIG_FILE']
        importer = Importer(
            config_path=config_path,
            backup_enabled=True
        )

        # Perform import
        success, message, stats = importer.import_package(
            tmp_file,
            conflict_strategy=conflict_strategy,
            import_templates=import_templates,
            import_images=import_images,
            preview_only=False
        )

        # Clean up temp file
        if os.path.exists(tmp_file):
            os.unlink(tmp_file)
        session.pop('import_temp_file', None)
        session.pop('import_filename', None)

        if not success:
            flash(f'Import failed: {message}', 'error')
            current_app.logger.error(f'Import error: {message}')
            return redirect(url_for('import_export.import_page'))

        # Log successful import
        current_app.logger.info(f'Import successful: {message}, Stats: {stats}')
        flash('Import completed successfully! Your site has been updated.', 'success')

        return redirect(url_for('admin.dashboard'))

    except Exception as e:
        # Clean up
        if os.path.exists(tmp_file):
            os.unlink(tmp_file)
        session.pop('import_temp_file', None)

        flash(f'Import error: {str(e)}', 'error')
        current_app.logger.error(f'Unexpected import error: {str(e)}')
        return redirect(url_for('import_export.import_page'))


# ============================================================================
# AJAX API Routes
# ============================================================================

@import_export_bp.route('/api/export-progress')
@login_required
def export_progress():
    """AJAX endpoint for export progress."""
    # Placeholder for real-time progress
    return jsonify({
        'status': 'completed',
        'progress': 100,
        'message': 'Export completed'
    })


@import_export_bp.route('/api/validate-package', methods=['POST'])
@login_required
def validate_package():
    """AJAX endpoint to validate package structure."""
    if 'file' not in request.files:
        return jsonify({'valid': False, 'message': 'No file provided'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'valid': False, 'message': 'No file selected'}), 400

    try:
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        valid, msg = Exporter.validate_export_package(tmp_path)
        os.unlink(tmp_path)

        return jsonify({
            'valid': valid,
            'message': msg
        })

    except Exception as e:
        return jsonify({
            'valid': False,
            'message': f'Validation error: {str(e)}'
        }), 500
