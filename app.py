from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = str(os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production'))

CONFIG_FILE = 'config.json'

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    if request.path.startswith('/admin'):
        return render_template('admin/404.html'), 404
    else:
        return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    if request.path.startswith('/admin'):
        return render_template('admin/500.html'), 500
    else:
        return render_template('500.html'), 500

@app.errorhandler(413)
def too_large(error):
    flash('File too large. Maximum size is 5MB.', 'error')
    return redirect(request.referrer or url_for('admin_dashboard'))

def convert_keys_to_underscore(data):
    """Recursively convert dictionary keys with hyphens to underscores for Jinja2 compatibility"""
    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            # Convert hyphens to underscores in keys
            new_key = key.replace('-', '_')
            # Recursively convert nested dictionaries
            new_dict[new_key] = convert_keys_to_underscore(value)
        return new_dict
    elif isinstance(data, list):
        # Recursively process list items
        return [convert_keys_to_underscore(item) for item in data]
    else:
        # Return primitive values as-is
        return data

def validate_field_value(field_type, value, field_name):
    """Validate field values based on type and constraints"""
    if not value or not value.strip():
        return None, f"{field_name} cannot be empty"
    
    value = value.strip()
    
    if field_type == 'text':
        if len(value) > 255:
            return None, f"{field_name} must be 255 characters or less"
        return value, None
    
    elif field_type == 'textarea':
        if len(value) > 5000:
            return None, f"{field_name} must be 5000 characters or less"
        return value, None
    
    elif field_type == 'image':
        # Image validation handled separately
        return value, None
    
    return value, None

def validate_image_file(file):
    """Validate uploaded image file with signature check"""
    if not file or not file.filename:
        return None, "No file selected"
    
    # Check file extension
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        return None, f"File type {file_ext} not allowed. Use: {', '.join(allowed_extensions)}"
    
    # Check file size (5MB limit)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer
    
    if file_size > 5 * 1024 * 1024:  # 5MB
        return None, "File size must be less than 5MB"
    
    # Read file header for signature validation
    header = file.read(12)  # Read first 12 bytes
    file.seek(0)  # Reset file pointer
    
    # Image file signatures (magic numbers)
    image_signatures = {
        b'\xFF\xD8\xFF': 'image/jpeg',  # JPEG
        b'\x89PNG\r\n\x1A\n': 'image/png',  # PNG
        b'GIF87a': 'image/gif',  # GIF87a
        b'GIF89a': 'image/gif',  # GIF89a
        b'RIFF': 'image/webp'  # WebP (RIFF....WEBP)
    }
    
    # Check if header matches any known image signature
    is_valid_image = False
    for signature, mime_type in image_signatures.items():
        if header.startswith(signature):
            is_valid_image = True
            # For WebP, need additional check
            if mime_type == 'image/webp':
                file.seek(8)  # Skip RIFF header
                webp_header = file.read(4)
                file.seek(0)
                if webp_header != b'WEBP':
                    return None, "Invalid WebP file format"
            break
    
    if not is_valid_image:
        return None, "File does not appear to be a valid image file"
    
    return file, None

def cleanup_unused_images():
    """Remove images that are not referenced in config"""
    try:
        config = load_config()
        if not config:
            return False
        
        # Get all referenced image paths
        referenced_images = set()
        
        # Check page fields
        for page in config.get('pages', []):
            for field in page.get('fields', []):
                if field.get('type') == 'image' and field.get('value'):
                    value = field['value']
                    if value.startswith('/static/images/uploads/'):
                        referenced_images.add(value[1:])  # Remove leading slash
        
        # Get all uploaded images
        upload_dir = os.path.join('static', 'images', 'uploads')
        if not os.path.exists(upload_dir):
            return True
        
        uploaded_images = set()
        for filename in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, filename)
            if os.path.isfile(file_path):
                uploaded_images.add(os.path.join('static', 'images', 'uploads', filename))
        
        # Remove unused images
        unused_images = uploaded_images - referenced_images
        for image_path in unused_images:
            try:
                os.remove(image_path)
                app.logger.info(f'Removed unused image: {image_path}')
            except Exception as e:
                app.logger.error(f'Failed to remove {image_path}: {e}')
        
        return True
    except Exception as e:
        app.logger.error(f'Error during image cleanup: {e}')
        return False

def validate_config_schema(config):
    """Validate configuration structure against expected schema"""
    errors = []
    
    # Check required top-level keys
    required_keys = ['admin-password', 'sitename', 'pages']
    for key in required_keys:
        if key not in config:
            errors.append(f"Missing required key: {key}")
    
    # Validate sitename
    if 'sitename' in config:
        sitename = config['sitename']
        if not isinstance(sitename, str) or not sitename.strip():
            errors.append("Site name must be a non-empty string")
        elif len(sitename) > 100:
            errors.append("Site name must be 100 characters or less")
    
    # Validate description (optional)
    if 'description' in config and config['description']:
        description = config['description']
        if not isinstance(description, str):
            errors.append("Description must be a string")
        elif len(description) > 255:
            errors.append("Description must be 255 characters or less")
    
    # Validate keywords (optional)
    if 'keywords' in config and config['keywords']:
        keywords = config['keywords']
        if not isinstance(keywords, list):
            errors.append("Keywords must be an array")
        else:
            for i, keyword in enumerate(keywords):
                if not isinstance(keyword, str):
                    errors.append(f"Keyword {i+1} must be a string")
    
    # Validate pages
    if 'pages' in config:
        pages = config['pages']
        if not isinstance(pages, list):
            errors.append("Pages must be an array")
        elif len(pages) == 0:
            errors.append("At least one page is required")
        else:
            urls = set()
            for i, page in enumerate(pages):
                page_errors = validate_page_schema(page, i, urls)
                errors.extend(page_errors)
    
    # Validate footer (optional)
    if 'footer' in config and config['footer']:
        footer = config['footer']
        if not isinstance(footer, dict):
            errors.append("Footer must be an object")
        elif 'content' in footer:
            content = footer['content']
            if not isinstance(content, list):
                errors.append("Footer content must be an array")
            else:
                for i, line in enumerate(content):
                    if not isinstance(line, str):
                        errors.append(f"Footer line {i+1} must be a string")
    
    return errors

def validate_page_schema(page, index, existing_urls):
    """Validate individual page schema"""
    errors = []
    prefix = f"Page {index+1}"
    
    # Required fields
    required_fields = ['title', 'template', 'url']
    for field in required_fields:
        if field not in page:
            errors.append(f"{prefix}: Missing required field '{field}'")
    
    # Validate title
    if 'title' in page:
        title = page['title']
        if not isinstance(title, str) or not title.strip():
            errors.append(f"{prefix}: Title must be a non-empty string")
    
    # Validate template
    if 'template' in page:
        template = page['template']
        if not isinstance(template, str) or not template.strip():
            errors.append(f"{prefix}: Template must be a non-empty string")
        elif not template.endswith('.html'):
            errors.append(f"{prefix}: Template must be an HTML file")
    
    # Validate URL
    if 'url' in page:
        url = page['url']
        if not isinstance(url, str) or not url.strip():
            errors.append(f"{prefix}: URL must be a non-empty string")
        elif not url.startswith('/'):
            errors.append(f"{prefix}: URL must start with '/'")
        elif url in existing_urls:
            errors.append(f"{prefix}: URL '{url}' is already used by another page")
        else:
            existing_urls.add(url)
    
    # Validate menu-title (optional)
    if 'menu-title' in page:
        menu_title = page['menu-title']
        if not isinstance(menu_title, str):
            errors.append(f"{prefix}: Menu title must be a string")
    
    # Validate SEO fields (optional)
    for seo_field in ['seo-description', 'seo-keywords']:
        if seo_field in page:
            value = page[seo_field]
            if seo_field == 'seo-description':
                if not isinstance(value, str):
                    errors.append(f"{prefix}: SEO description must be a string")
                elif len(value) > 255:
                    errors.append(f"{prefix}: SEO description must be 255 characters or less")
            elif seo_field == 'seo-keywords':
                if not isinstance(value, list):
                    errors.append(f"{prefix}: SEO keywords must be an array")
    
    # Validate fields (optional)
    if 'fields' in page:
        fields = page['fields']
        if not isinstance(fields, list):
            errors.append(f"{prefix}: Fields must be an array")
        else:
            field_names = set()
            for i, field in enumerate(fields):
                field_errors = validate_field_schema(field, index, i, field_names)
                errors.extend(field_errors)
    
    return errors

def validate_field_schema(field, page_index, field_index, existing_names):
    """Validate individual field schema"""
    errors = []
    prefix = f"Page {page_index+1} Field {field_index+1}"
    
    # Required fields
    required_fields = ['name', 'type', 'label']
    for req_field in required_fields:
        if req_field not in field:
            errors.append(f"{prefix}: Missing required field '{req_field}'")
    
    # Validate name
    if 'name' in field:
        name = field['name']
        if not isinstance(name, str) or not name.strip():
            errors.append(f"{prefix}: Name must be a non-empty string")
        elif name in existing_names:
            errors.append(f"{prefix}: Field name '{name}' is already used in this page")
        else:
            existing_names.add(name)
    
    # Validate type
    if 'type' in field:
        field_type = field['type']
        valid_types = ['text', 'textarea', 'image']
        if field_type not in valid_types:
            errors.append(f"{prefix}: Type must be one of: {', '.join(valid_types)}")
    
    # Validate label
    if 'label' in field:
        label = field['label']
        if not isinstance(label, str) or not label.strip():
            errors.append(f"{prefix}: Label must be a non-empty string")
    
    # Validate value (optional)
    if 'value' in field:
        value = field['value']
        if not isinstance(value, str):
            errors.append(f"{prefix}: Value must be a string")
    
    return errors

def sanitize_filename(filename):
    """Sanitize filename to prevent path traversal attacks"""
    # Remove directory separators
    filename = os.path.basename(filename)
    
    # Remove dangerous characters
    dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in dangerous_chars:
        filename = filename.replace(char, '')
    
    # Ensure filename is not empty
    if not filename or filename.startswith('.'):
        return 'upload_' + str(uuid.uuid4().hex)[:8]
    
    return filename

def load_config(validate=True):
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Validate configuration schema (optional for CLI)
        if validate:
            errors = validate_config_schema(config)
            if errors:
                error_msg = 'Configuration validation failed: ' + '; '.join(errors[:3])  # Show first 3 errors
                flash(error_msg, 'error')
                app.logger.error(f'Config validation errors: {errors}')
                return None
        
        return config
    except FileNotFoundError:
        return create_default_config()
    except json.JSONDecodeError as e:
        flash('Error: Configuration file is corrupted. Please check the file format.', 'error')
        app.logger.error(f'JSON decode error: {e}')
        return None
    except PermissionError:
        flash('Error: No permission to read configuration file.', 'error')
        app.logger.error('Permission denied reading config file')
        return None
    except Exception as e:
        flash('Error: Unable to load configuration.', 'error')
        app.logger.error(f'Unexpected error loading config: {e}')
        return None

def save_config(config, validate=True):
    try:
        # Validate configuration schema before saving (optional for CLI)
        if validate:
            errors = validate_config_schema(config)
            if errors:
                error_msg = 'Configuration validation failed: ' + '; '.join(errors[:3])  # Show first 3 errors
                flash(error_msg, 'error')
                app.logger.error(f'Config validation errors: {errors}')
                return False
        
        # Create backup before saving
        backup_file = CONFIG_FILE + '.backup'
        if os.path.exists(CONFIG_FILE):
            import shutil
            shutil.copy2(CONFIG_FILE, backup_file)
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except PermissionError:
        flash('Error: No permission to save configuration file.', 'error')
        app.logger.error('Permission denied saving config file')
        return False
    except json.JSONEncodeError as e:
        flash('Error: Configuration data is invalid.', 'error')
        app.logger.error(f'JSON encode error: {e}')
        return False
    except Exception as e:
        flash('Error: Unable to save configuration.', 'error')
        app.logger.error(f'Unexpected error saving config: {e}')
        return False

def create_default_config():
    default_config = {
        "admin-password": "scrypt:32768:8:1$dLQFhTGZDuFqolmd$deb5e1b924768ba1b4a37ce9c17366950c81d7eca0bf194609bac21fdd40d64921e84c5fb514c84f4f18a647c4e2d97e64f5ffd3bf4eca2a20b5dd57edf12c91",
        "sitename": "My Website",
        "description": "A simple website built with Editable Static Web",
        "keywords": ["website", "profile", "business"],
        "pages": [
            {
                "title": "Home - My Website",
                "template": "home.html",
                "menu-title": "Home",
                "url": "/",
                "seo-description": "Welcome to my website",
                "seo-keywords": ["home", "welcome"],
                "fields": [
                    {
                        "name": "hero-title",
                        "type": "text",
                        "label": "Hero Title",
                        "value": "Welcome to Our Website"
                    },
                    {
                        "name": "hero-description",
                        "type": "textarea",
                        "label": "Hero Description",
                        "value": "We provide amazing services for your business"
                    }
                ]
            }
        ],
        "footer": {
            "content": [
                "Copyright © 2025 My Website. All rights reserved."
            ]
        }
    }
    
    if save_config(default_config):
        return default_config
    return None

def get_page_by_url(url):
    config = load_config()
    if not config:
        return None
    
    for page in config['pages']:
        if page['url'] == url:
            return page
    return None

def render_template_with_data(template_name, page_data=None):
    config = load_config()
    if not config:
        return render_template('500.html'), 500
    
    # Check if template exists
    template_path = os.path.join('templates', template_name)
    if not os.path.exists(template_path):
        app.logger.error(f'Template not found: {template_name}')
        return render_template('404.html'), 404
    
    # Convert all config keys with hyphens to underscores for Jinja2
    config_underscore = convert_keys_to_underscore(config)
    
    template_data = {
        'sitename': config_underscore.get('sitename', ''),
        'description': config_underscore.get('description', ''),
        'keywords': config_underscore.get('keywords', []),
        'footer': config_underscore.get('footer', {}).get('content', []),
        'pages': config_underscore.get('pages', [])
    }
    
    if page_data:
        # Convert page data keys as well
        page_data_underscore = convert_keys_to_underscore(page_data)
        
        # Add field values with converted names
        for field in page_data.get('fields', []):
            field_name = field['name'].replace('-', '_')
            template_data[field_name] = field.get('value', '')
        
        # Add page metadata with converted keys
        template_data.update({
            'page_title': page_data_underscore.get('title', ''),
            'seo_description': page_data_underscore.get('seo_description', ''),
            'seo_keywords': page_data_underscore.get('seo_keywords', [])
        })
    
    try:
        return render_template(template_name, **template_data)
    except Exception as e:
        app.logger.error(f'Template rendering error for {template_name}: {e}')
        return render_template('500.html'), 500

@app.route('/')
def index():
    page = get_page_by_url('/')
    if not page:
        return render_template('404.html'), 404
    return render_template_with_data(page['template'], page)

@app.route('/<path:url>')
def public_page(url):
    page = get_page_by_url(f'/{url}')
    if not page:
        return render_template('404.html'), 404
    return render_template_with_data(page['template'], page)

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    config = load_config()
    if not config:
        return render_template('admin/500.html'), 500
    
    return render_template('admin/dashboard.html', pages=config.get('pages', []))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        config = load_config()
        
        if config and check_password_hash(config['admin-password'], password):
            session['admin_logged_in'] = True
            session['login_time'] = datetime.now().timestamp()
            flash('Login successful', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid password', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin/edit/<int:page_index>', methods=['GET', 'POST'])
def edit_page(page_index):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    config = load_config()
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
        elif save_config(config):
            flash('Page updated successfully', 'success')
            return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/edit_page.html', page=page, page_index=page_index)

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    config = load_config()
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
        elif save_config(config):
            flash('Settings updated successfully', 'success')
            return redirect(url_for('admin_settings'))
    
    return render_template('admin/settings.html', 
                          sitename=config.get('sitename', ''),
                          description=config.get('description', ''),
                          keywords=config.get('keywords', ''),
                          footer=config.get('footer', {}))

@app.route('/admin/change-password', methods=['GET', 'POST'])
def change_password():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        validation_errors = []
        
        # Validate current password
        config = load_config()
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
            if save_config(config):
                flash('Password changed successfully', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Error updating password', 'error')
    
    return render_template('admin/change_password.html')

@app.route('/admin/cleanup', methods=['POST'])
def cleanup_images():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    if cleanup_unused_images():
        flash('Unused images cleaned up successfully', 'success')
    else:
        flash('Error during image cleanup', 'error')
    
    return redirect(url_for('admin_settings'))

# CLI-specific functions (without flash)
def load_config_cli():
    """Load config for CLI use (without flash)"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Skip validation for CLI to avoid issues
        return config
    except FileNotFoundError:
        print('Error: Configuration file not found')
        return None
    except json.JSONDecodeError as e:
        print(f'Error: Configuration file is corrupted - {e}')
        return None
    except Exception as e:
        print(f'Error: Unable to load configuration - {e}')
        return None

def save_config_cli(config):
    """Save config for CLI use (without flash)"""
    try:
        # Skip validation for CLI to avoid issues
        
        # Create backup before saving
        backup_file = CONFIG_FILE + '.backup'
        if os.path.exists(CONFIG_FILE):
            import shutil
            shutil.copy2(CONFIG_FILE, backup_file)
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f'Error: Unable to save configuration - {e}')
        return False

# CLI Management Commands
def create_page(title, template, url, menu_title=None):
    """Create a new page via CLI"""
    config = load_config_cli()
    if not config:
        return False
    
    # Check if URL already exists
    for page in config.get('pages', []):
        if page.get('url') == url:
            print(f'Error: URL "{url}" already exists')
            return False
    
    # Create new page
    new_page = {
        'title': title,
        'template': template,
        'url': url,
        'fields': []
    }
    
    if menu_title:
        new_page['menu-title'] = menu_title
    
    config['pages'].append(new_page)
    
    if save_config_cli(config):
        print(f'Successfully created page: {title} ({url})')
        return True
    else:
        return False

def list_pages():
    """List all pages via CLI"""
    config = load_config_cli()
    if not config:
        return
    
    pages = config.get('pages', [])
    if not pages:
        print('No pages found')
        return
    
    print('\nPages:')
    print('-' * 60)
    for i, page in enumerate(pages, 1):
        title = page.get('title', 'Untitled')
        url = page.get('url', '/no-url')
        template = page.get('template', 'no-template')
        menu_title = page.get('menu-title', title)
        print(f'{i:2d}. {title}')
        print(f'    URL: {url}')
        print(f'    Template: {template}')
        print(f'    Menu Title: {menu_title}')
        print()

def delete_page(url):
    """Delete a page by URL via CLI"""
    config = load_config_cli()
    if not config:
        return False
    
    pages = config.get('pages', [])
    original_count = len(pages)
    
    # Remove page with matching URL
    config['pages'] = [page for page in pages if page.get('url') != url]
    
    if len(config['pages']) == original_count:
        print(f'Error: Page with URL "{url}" not found')
        return False
    
    if save_config_cli(config):
        print(f'Successfully deleted page: {url}')
        return True
    else:
        return False

def show_help():
    """Show CLI help"""
    print('Wicara CMS Management Commands')
    print('=' * 40)
    print('Usage: python app.py <command> [arguments]')
    print()
    print('Commands:')
    print('  create-page <title> <template> <url> [menu-title]')
    print('    Create a new page')
    print('    Example: python app.py create-page "About Us" about.html /about "About"')
    print()
    print('  list-pages')
    print('    List all pages')
    print()
    print('  delete-page <url>')
    print('    Delete a page by URL')
    print('    Example: python app.py delete-page /about')
    print()
    print('  help')
    print('    Show this help message')
    print()
    print('  run')
    print('    Start the web server (default: port 5555)')

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'create-page':
            if len(sys.argv) < 5:
                print('Error: Missing arguments')
                print('Usage: python app.py create-page <title> <template> <url> [menu-title]')
                sys.exit(1)
            title = sys.argv[2]
            template = sys.argv[3]
            url = sys.argv[4]
            menu_title = sys.argv[5] if len(sys.argv) > 5 else None
            success = create_page(title, template, url, menu_title)
            sys.exit(0 if success else 1)
        
        elif command == 'list-pages':
            list_pages()
        
        elif command == 'delete-page':
            if len(sys.argv) < 3:
                print('Error: Missing URL argument')
                print('Usage: python app.py delete-page <url>')
                sys.exit(1)
            url = sys.argv[2]
            success = delete_page(url)
            sys.exit(0 if success else 1)
        
        elif command == 'help':
            show_help()
        
        elif command == 'run':
            app.run(debug=False, host='0.0.0.0', port=5555)
        
        else:
            print(f'Error: Unknown command "{command}"')
            print('Run "python app.py help" for available commands')
            sys.exit(1)
    else:
        # Default: run the web server
        app.run(debug=False, host='0.0.0.0', port=5555)