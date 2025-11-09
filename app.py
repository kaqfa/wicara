from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

CONFIG_FILE = 'config.json'

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

def load_config():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return create_default_config()
    except json.JSONDecodeError:
        flash('Error: Configuration file is corrupted', 'error')
        return None

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        flash(f'Error saving configuration: {str(e)}', 'error')
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
        return "Configuration error", 500
    
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
    
    return render_template(template_name, **template_data)

@app.route('/')
def index():
    page = get_page_by_url('/')
    if not page:
        return "Page not found", 404
    return render_template_with_data(page['template'], page)

@app.route('/<path:url>')
def public_page(url):
    page = get_page_by_url(f'/{url}')
    if not page:
        return "Page not found", 404
    return render_template_with_data(page['template'], page)

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    config = load_config()
    if not config:
        return "Configuration error", 500
    
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
    if not config or page_index >= len(config['pages']):
        return "Page not found", 404
    
    page = config['pages'][page_index]
    
    if request.method == 'POST':
        for field in page.get('fields', []):
            field_name = field['name']
            if field['type'] == 'image':
                if 'file' in request.files:
                    file = request.files[field_name]
                    if file and file.filename:
                        filename = f"{uuid.uuid4().hex}_{file.filename}"
                        file_path = os.path.join('static', 'images', 'uploads', filename)
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        file.save(file_path)
                        field['value'] = f"/static/images/uploads/{filename}"
            else:
                field['value'] = request.form.get(field_name, field.get('value', ''))
        
        if save_config(config):
            flash('Page updated successfully', 'success')
            return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/edit_page.html', page=page, page_index=page_index)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5555)