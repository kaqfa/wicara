"""
Admin panel routes for WICARA CMS.
Handles dashboard, page editing, settings, and management.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.security import generate_password_hash
import os
import uuid

from app.core import (
    load_config, save_config, validate_field_value, validate_image_file,
    sanitize_filename, cleanup_unused_images, ensure_directories
)
from app.modules.auth.utils import login_required
from app.modules.admin.forms import SettingsForm, PasswordChangeForm

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
@login_required
def dashboard():
    """
    Admin dashboard route.

    Displays list of pages that can be edited.
    """
    config = load_config(current_app.config['CONFIG_FILE'], logger=current_app.logger)
    if not config:
        return render_template('admin/500.html'), 500

    return render_template('admin/dashboard.html', pages=config.get('pages', []))


@admin_bp.route('/edit/<int:page_index>', methods=['GET', 'POST'])
@login_required
def edit_page(page_index):
    """
    Edit page content route.

    GET: Display page editor
    POST: Save page changes
    """
    config = load_config(current_app.config['CONFIG_FILE'], logger=current_app.logger)
    if not config:
        return render_template('admin/500.html'), 500
    if page_index >= len(config['pages']):
        return render_template('admin/404.html'), 404

    page = config['pages'][page_index]

    if request.method == 'POST':
        validation_errors = []

        for field in page.get('fields', []):
            field_name = field['name']
            field_label = field.get('label', field_name)

            if field['type'] == 'image':
                if 'file' in request.files:
                    file = request.files[field_name]
                    if file and file.filename:
                        # Validate image file
                        validated_file, error = validate_image_file(file)
                        if error:
                            validation_errors.append(f"{field_label}: {error}")
                        else:
                            # Delete old image if exists
                            old_value = field.get('value', '')
                            if old_value and old_value.startswith('/static/images/uploads/'):
                                old_file_path = old_value[1:]  # Remove leading slash
                                if os.path.exists(old_file_path):
                                    os.remove(old_file_path)

                            # Save new image
                            safe_filename = sanitize_filename(file.filename)
                            unique_filename = f"{uuid.uuid4().hex}_{safe_filename}"
                            file_path = os.path.join('static', 'images', 'uploads', unique_filename)
                            os.makedirs(os.path.dirname(file_path), exist_ok=True)
                            file.save(file_path)
                            field['value'] = f"/static/images/uploads/{unique_filename}"
                            current_app.logger.info(f'Image uploaded: {unique_filename}')
            else:
                # Validate text/textarea fields
                new_value = request.form.get(field_name, '').strip()
                if new_value:  # Only validate if user provided a value
                    validated_value, error = validate_field_value(field['type'], new_value, field_label)
                    if error:
                        validation_errors.append(error)
                    else:
                        field['value'] = validated_value
                elif field.get('required', False):
                    validation_errors.append(f"{field_label} is required")

        if validation_errors:
            for error in validation_errors:
                flash(error, 'error')
        elif save_config(config, current_app.config['CONFIG_FILE'], logger=current_app.logger):
            flash('Page updated successfully', 'success')
            current_app.logger.info(f'Page updated: {page.get("title")}')
            return redirect(url_for('admin.dashboard'))

    return render_template('admin/edit_page.html', page=page, page_index=page_index)


@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """
    Admin settings route.

    GET: Display settings form
    POST: Save site settings
    """
    config = load_config(current_app.config['CONFIG_FILE'], logger=current_app.logger)
    if not config:
        return render_template('admin/500.html'), 500

    if request.method == 'POST':
        # Prepare form data
        form_data = {
            'sitename': request.form.get('sitename', ''),
            'description': request.form.get('description', ''),
            'keywords': request.form.get('keywords', ''),
            'footer_content': request.form.getlist('footer_content')
        }

        # Validate form
        is_valid, errors, validated_data = SettingsForm.validate(form_data)

        if not is_valid:
            for error in errors:
                flash(error, 'error')
        else:
            # Update config
            config.update(validated_data)

            # Save config
            if save_config(config, current_app.config['CONFIG_FILE'], logger=current_app.logger):
                flash('Settings updated successfully', 'success')
                current_app.logger.info('Settings updated')
                return redirect(url_for('admin.settings'))

    return render_template('admin/settings.html',
                          sitename=config.get('sitename', ''),
                          description=config.get('description', ''),
                          keywords=config.get('keywords', ''),
                          footer=config.get('footer', {}))


@admin_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """
    Change admin password route.

    GET: Display password change form
    POST: Update password
    """
    if request.method == 'POST':
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        config = load_config(current_app.config['CONFIG_FILE'], logger=current_app.logger)
        if not config:
            flash('Configuration error', 'error')
            return render_template('admin/change_password.html')

        # Validate current password
        from werkzeug.security import check_password_hash
        if not check_password_hash(config['admin-password'], current_password):
            flash('Current password is incorrect', 'error')
            return render_template('admin/change_password.html')

        # Validate new password
        is_valid, errors = PasswordChangeForm.validate(
            config['admin-password'],
            new_password,
            confirm_password
        )

        if not is_valid:
            for error in errors:
                flash(error, 'error')
        else:
            # Update password
            config['admin-password'] = generate_password_hash(new_password, method='scrypt')
            if save_config(config, current_app.config['CONFIG_FILE'], logger=current_app.logger):
                flash('Password changed successfully', 'success')
                current_app.logger.info('Admin password changed')
                return redirect(url_for('admin.dashboard'))
            else:
                flash('Error updating password', 'error')

    return render_template('admin/change_password.html')


@admin_bp.route('/cleanup', methods=['POST'])
@login_required
def cleanup():
    """
    Cleanup unused images route.

    Removes image files that are not referenced in any page configuration.
    """
    config = load_config(current_app.config['CONFIG_FILE'], logger=current_app.logger)
    if not config:
        flash('Configuration error', 'error')
        return redirect(url_for('admin.settings'))

    if cleanup_unused_images(config, logger=current_app.logger):
        flash('Unused images cleaned up successfully', 'success')
        current_app.logger.info('Image cleanup completed')
    else:
        flash('Error during image cleanup', 'error')
        current_app.logger.error('Image cleanup failed')

    return redirect(url_for('admin.settings'))


# ============================================================================
# Multi-site Management (MULTI-03)
# ============================================================================

from .site_routes import register_site_routes
from .advanced_routes import init_advanced_routes

# Register site management routes when module loads
def init_admin_routes(app):
    """Initialize admin routes with app."""
    app.register_blueprint(admin_bp)
    register_site_routes(app)
    init_advanced_routes(app)
