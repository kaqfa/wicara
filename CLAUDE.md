# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Wicara is a lightweight, flat-file CMS built with Flask that allows creating editable static websites without a database. All content is stored in a single `config.json` file, making it portable and easy to backup.

## Development Commands

### Running the Application
```bash
python app.py
```
The application runs on port 5555 by default.

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Changing Admin Password
```bash
python -c "
from werkzeug.security import generate_password_hash
import json
with open('config.json', 'r') as f: config = json.load(f)
config['admin-password'] = generate_password_hash('your-new-password', method='scrypt')
with open('config.json', 'w') as f: json.dump(config, f, indent=2)
"
```

## Architecture

### Core Structure
- **Single File Application**: All logic in `app.py` (Flask application)
- **Configuration-Driven**: Website structure defined in `config.json`
- **Template-Based**: Jinja2 templates with dynamic content injection
- **Flat-File CMS**: No database - all content in JSON file

### Key Components

#### Flask Routes (`app.py`)
- `/` - Home page and dynamic page routing
- `/<path:url>` - Dynamic page handler
- `/admin` - Admin dashboard (protected)
- `/admin/login` - Admin authentication
- `/admin/logout` - Admin logout
- `/admin/edit/<int:page_index>` - Page content editor
- `/admin/settings` - Site settings management
- `/admin/change-password` - Password change interface
- `/admin/cleanup` - Cleanup unused images

#### Configuration System (`config.json`)
- **Global Settings**: `sitename`, `description`, `keywords`
- **Pages Array**: Each page defines title, template, URL, and editable fields
- **Field Types**: `text`, `textarea`, `image`
- **Footer Configuration**: Footer content lines

#### Template System
- **Public Templates**: `templates/home.html`, `about.html`, `contact.html`
- **Admin Templates**: `templates/admin/*.html`
- **Key Feature**: Hyphen-to-underscore conversion (config uses hyphens, templates use underscores)

#### Static Assets
- **CSS**: `static/css/style.css` (public), `admin.css` (admin panel)
- **JavaScript**: `static/js/admin.js` (admin functionality)
- **Images**: `static/images/uploads/` (user uploads)

### Key Functions

#### Content Conversion
- `convert_keys_to_underscore()`: Converts config hyphens to underscores for Jinja2

#### Validation
- `validate_field_value()`: Validates text/textarea field input
- `validate_image_file()`: Checks file signatures, size, and extensions

#### Error Handling
- Custom 404, 500, and 413 error handlers
- Separate error pages for public and admin areas

## Important Implementation Details

### Template Variable Access
- Config.json uses hyphens (e.g., `"hero-title"`)
- Templates use underscores (e.g., `{{hero_title}}`)
- Automatic conversion handled by `convert_keys_to_underscore()`

### Field Types
- **text**: Single line input (255 char limit)
- **textarea**: Multi-line input (5000 char limit)
- **image**: File upload (5MB limit, validates file signatures)

### Security Features
- Password hashing with scrypt
- Session-based admin authentication
- File upload validation with magic number checking
- CSRF protection via Flask sessions

### File Structure
```
wicara/
├── app.py                    # Main Flask application (all logic)
├── config.json              # Website configuration and content
├── requirements.txt         # Python dependencies
├── templates/               # HTML templates
│   ├── *.html              # Public page templates
│   └── admin/              # Admin panel templates
├── static/                  # Static assets
│   ├── css/                # Stylesheets
│   ├── js/                 # JavaScript files
│   └── images/             # Image assets
│       └── uploads/        # User uploaded images
└── utils/                   # Helper utilities (currently empty)
```

## Testing and Development

### Access Points
- Public site: http://localhost:5555
- Admin panel: http://localhost:5555/admin
- Default admin password: `admin123`

### Configuration Editing
- Edit `config.json` directly for structural changes
- Use admin panel for content editing
- Restart application after config structure changes

### Adding New Pages
1. Create HTML template in `templates/`
2. Add page configuration to `config.json` pages array
3. Define fields with types: text, textarea, or image
4. Access via defined URL and edit through admin panel