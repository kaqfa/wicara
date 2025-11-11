"""
Admin routes blueprint for WICARA CMS.
Handles admin panel, authentication, and content management.
"""

from flask import (
    Blueprint, render_template, request, redirect, url_for, session, flash, current_app
)
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import os
import uuid

from app.utils import (
    load_config, save_config, validate_field_value, validate_image_file,
    sanitize_filename, cleanup_unused_images, convert_keys_to_underscore
)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def login_required(f):
    """Decorator to check if user is logged in."""
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login route."""
    if request.method == 'POST':
        password = request.form.get('password')
        config = load_config(current_app.config['CONFIG_FILE'], logger=current_app.logger)

        if config and check_password_hash(config['admin-password'], password):
            session['admin_logged_in'] = True
            session['login_time'] = datetime.now().timestamp()
            flash('Login successful', 'success')
            current_app.logger.info('Admin login successful')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid password', 'error')
            current_app.logger.warning('Failed admin login attempt')

    return render_template('admin/login.html')


@admin_bp.route('/logout')
def logout():
    """Admin logout route."""
    session.clear()
    flash('Logged out successfully', 'success')
    current_app.logger.info('Admin logged out')
    return redirect(url_for('admin.login'))


@admin_bp.route('/')
@login_required
def dashboard():
    """Admin dashboard route."""
    config = load_config(current_app.config['CONFIG_FILE'], logger=current_app.logger)
    if not config:
        return render_template('admin/500.html'), 500

    return render_template('admin/dashboard.html', pages=config.get('pages', []))


@admin_bp.route('/edit/<int:page_index>', methods=['GET', 'POST'])
@login_required
def edit_page(page_index):
    """Edit page content route."""
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
                            # Remove old image if exists
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
    """Admin settings route."""
    config = load_config(current_app.config['CONFIG_FILE'], logger=current_app.logger)
    if not config:
        return render_template('admin/500.html'), 500

    if request.method == 'POST':
        validation_errors = []

        # Validate sitename
        sitename = request.form.get('sitename', '').strip()
        if not sitename:
            validation_errors.append("Site name is required")
        elif len(sitename) > 100:
            validation_errors.append("Site name must be 100 characters or less")
        else:
            config['sitename'] = sitename

        # Validate description
        description = request.form.get('description', '').strip()
        if description and len(description) > 255:
            validation_errors.append("Description must be 255 characters or less")
        else:
            config['description'] = description

        # Validate keywords
        keywords_input = request.form.get('keywords', '').strip()
        if keywords_input:
            keywords = [kw.strip() for kw in keywords_input.split(',') if kw.strip()]
            config['keywords'] = keywords
        else:
            config['keywords'] = []

        # Validate footer content
        footer_lines = request.form.getlist('footer_content')
        footer_lines = [line.strip() for line in footer_lines if line.strip()]
        config['footer'] = {'content': footer_lines}

        if validation_errors:
            for error in validation_errors:
                flash(error, 'error')
        elif save_config(config, current_app.config['CONFIG_FILE'], logger=current_app.logger):
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
    """Change admin password route."""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        validation_errors = []

        # Validate current password
        config = load_config(current_app.config['CONFIG_FILE'], logger=current_app.logger)
        if not config:
            flash('Configuration error', 'error')
            return render_template('admin/change_password.html')

        if not check_password_hash(config['admin-password'], current_password):
            validation_errors.append('Current password is incorrect')

        # Validate new password
        if not new_password:
            validation_errors.append('New password is required')
        elif len(new_password) < 8:
            validation_errors.append('New password must be at least 8 characters long')
        elif not any(c.isupper() for c in new_password):
            validation_errors.append('New password must contain at least one uppercase letter')
        elif not any(c.islower() for c in new_password):
            validation_errors.append('New password must contain at least one lowercase letter')
        elif not any(c.isdigit() for c in new_password):
            validation_errors.append('New password must contain at least one number')

        # Validate password confirmation
        if new_password != confirm_password:
            validation_errors.append('Password confirmation does not match')

        if validation_errors:
            for error in validation_errors:
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
    """Cleanup unused images route."""
    if cleanup_unused_images(current_app.config['CONFIG_FILE'], logger=current_app.logger):
        flash('Unused images cleaned up successfully', 'success')
        current_app.logger.info('Image cleanup completed')
    else:
        flash('Error during image cleanup', 'error')
        current_app.logger.error('Image cleanup failed')

    return redirect(url_for('admin.settings'))
