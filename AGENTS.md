# Wicara CMS - Agent Guidelines

## Build & Test Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server (default port 5555)
python app.py

# Run on custom port
python -c "from app import app; app.run(debug=True, host='0.0.0.0', port=8000)"

# Run production server
gunicorn -w 4 -b 0.0.0.0:8000 app:app

# No test framework - test manually by accessing routes
```

## Code Style Guidelines

### Philosophy
Keep it simple, lightweight, and minimal. This is a flat-file CMS - avoid complex abstractions.

### Structure
- Single `app.py` file for all application logic
- All content in `config.json` - never use databases
- Functions over classes, snake_case naming
- Constants in UPPER_SNAKE_CASE

### Imports
```python
# Standard library first
import json
import os
from datetime import datetime
import uuid

# Third-party libraries second
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
```

### Naming Conventions
- Functions: `snake_case` (e.g., `load_config`, `get_page_by_url`)
- Variables: `snake_case` (e.g., `page_data`, `admin_logged_in`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `CONFIG_FILE`, `SECRET_KEY`)
- Templates: `kebab-case.html` (e.g., `edit_page.html`)

### Error Handling
- Use try/except for file operations
- Flash messages for user feedback: `flash('message', 'category')`
- Graceful fallbacks with default values
- Return proper HTTP status codes (404, 500)

### Security
- Always hash passwords with `werkzeug.security`
- Use Flask sessions for authentication
- Validate file uploads (type, size)
- Escape template output automatically via Jinja2

### Templates
- Use Jinja2 with `{{variable}}` syntax
- **Hyphen to Underscore Conversion**: 
  - Config.json uses hyphens (readable): `{"seo-description": "..."}`
  - Templates use underscores (Jinja2 compatible): `{{seo_description}}`
  - Automatic conversion via `convert_keys_to_underscore()` function
- Global vars: `sitename`, `description`, `keywords`, `footer`, `pages`
- Page-specific vars from config.json fields (auto-converted)
- Responsive CSS with mobile-first approach

### Configuration
- All website data in `config.json`
- Use schema: admin-password, sitename, pages[], footer{}
- Field types: text, textarea, image
- Never hardcode content - always use config.json