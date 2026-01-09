# WICARA CMS - Developer Documentation

## Table of Contents
- [Template Creation Guide](#template-creation-guide)
- [Field Type Reference](#field-type-reference)
- [API Documentation](#api-documentation)
- [Contribution Guidelines](#contribution-guidelines)
- [CLI Reference](#cli-reference)
- [Configuration Schema](#configuration-schema)
- [Code Architecture](#code-architecture)

---

## Template Creation Guide

### Template Engine

WICARA CMS uses **Jinja2** templating engine with the following features:

- **Template Inheritance**: Base template with blocks
- **Auto-escaping**: XSS protection by default
- **Filters**: Built-in and custom filters
- **Variables**: Dynamic content from config.json
- **Control Structures**: Loops, conditionals, includes

### Template Structure

#### Basic Template
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{{ page_title }} - {{ sitename }}</title>
    <meta name="description" content="{{ page_description }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <h1>{{ page_title }}</h1>
    <p>{{ page_content }}</p>
</body>
</html>
```

#### Template with Base Inheritance
```html
{% extends "base.html" %}

{% block title %}{{ page_title }} - {{ sitename }}{% endblock %}

{% block content %}
<div class="container">
    <h1>{{ page_title }}</h1>
    <p>{{ page_content }}</p>
</div>
{% endblock %}
```

### Available Variables

#### Global Variables (Available in all templates)
```jinja2
{{ sitename }}        # Website name from config
{{ description }}     # Website description
{{ keywords }}        # Keywords array
{{ pages }}          # All pages array
{{ footer }}         # Footer content array
```

#### Page-specific Variables
```jinja2
{{ page_title }}      # Current page title
{{ page_content }}    # Page content
{{ seo_description }} # SEO meta description
{{ seo_keywords }}    # SEO keywords
```

#### Dynamic Field Variables
Fields defined in config.json are available as variables with underscores:
```jinja2
{{ hero_title }}        # From "hero-title" in config
{{ page_content }}      # From "page-content" in config
{{ background_image }}  # From "background-image" in config
```

### Template Features

#### 1. Template Inheritance
**Base Template (`base.html`):**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    {% block head %}
    <title>{% block title %}{{ sitename }}{% endblock %}</title>
    {% endblock %}
</head>
<body>
    {% block nav %}{% endblock %}
    {% block content %}{% endblock %}
    {% block footer %}{% endblock %}
</body>
</html>
```

**Child Template:**
```html
{% extends "base.html" %}

{% block title %}About Us - {{ sitename }}{% endblock %}

{% block content %}
<h1>About Us</h1>
<p>{{ about_content }}</p>
{% endblock %}
```

#### 2. Conditional Rendering
```jinja2
{% if hero_image %}
<img src="{{ hero_image }}" alt="{{ hero_title }}">
{% endif %}

{% if features %}
<div class="features">
    {% for feature in features %}
    <div class="feature">{{ feature.title }}</div>
    {% endfor %}
</div>
{% endif %}
```

#### 3. Looping
```jinja2
{% for page in pages %}
{% if page.url != '/' %}
<a href="{{ page.url }}">{{ page.menu_title }}</a>
{% endif %}
{% endfor %}

{% for item in feature_list %}
<li>
    <h3>{{ item.title }}</h3>
    <p>{{ item.description }}</p>
</li>
{% endfor %}
```

#### 4. Including Templates
```jinja2
{% include 'header.html' %}
{% include 'navigation.html' %}
{% include 'footer.html' %}
```

#### 5. Macros (Reusable Functions)
```jinja2
{% macro feature_card(title, description, icon) %}
<div class="feature-card">
    <i class="{{ icon }}"></i>
    <h3>{{ title }}</h3>
    <p>{{ description }}</p>
</div>
{% endmacro %}

{{ feature_card("Fast", "Lightning speed", "bi-lightning") }}
{{ feature_card("Secure", "Built-in security", "bi-shield") }}
```

### Bootstrap Integration

WICARA includes Bootstrap 5.3 via CDN. Use Bootstrap classes:

```jinja2
<div class="container">
    <div class="row">
        <div class="col-md-8">
            <h1>{{ page_title }}</h1>
            <p>{{ page_content }}</p>
        </div>
        <div class="col-md-4">
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">{{ sidebar_title }}</h5>
                    <p class="card-text">{{ sidebar_content }}</p>
                </div>
            </div>
        </div>
    </div>
</div>
```

### CSS Customization

#### Custom CSS Variables
```css
:root {
  --django-green: #092e20;
  --django-green-light: #44bb78;
  --django-accent: #ffc107;
}
```

#### Utility Classes
```css
.text-primary { color: var(--django-green) !important; }
.bg-primary { background-color: var(--django-green) !important; }
.hero-section { background: linear-gradient(135deg, var(--django-green), var(--django-green-light)); }
```

### Best Practices

#### 1. SEO Optimization
```html
<head>
    <title>{{ page_title }} - {{ sitename }}</title>
    <meta name="description" content="{{ seo_description }}">
    <meta name="keywords" content="{{ seo_keywords|join(', ') }}">
    <meta property="og:title" content="{{ page_title }}">
    <meta property="og:description" content="{{ seo_description }}">
</head>
```

#### 2. Responsive Design
```html
<div class="container">
    <div class="row">
        <div class="col-lg-8 col-md-6">
            <!-- Main content -->
        </div>
        <div class="col-lg-4 col-md-6">
            <!-- Sidebar -->
        </div>
    </div>
</div>
```

#### 3. Error Handling
```jinja2
{% if page_title %}
    <h1>{{ page_title }}</h1>
{% else %}
    <h1>Untitled Page</h1>
{% endif %}
```

#### 4. Performance
- Use CDN for external resources
- Optimize images before upload
- Minify CSS and JavaScript
- Use appropriate image formats

---

## Field Type Reference

### Overview

Fields are defined in `config.json` and determine the type of content input available in the admin panel.

### Field Types

#### 1. Text Field
```json
{
  "name": "hero-title",
  "type": "text",
  "label": "Hero Title",
  "value": "Welcome to Our Website",
  "required": true,
  "placeholder": "Enter hero title"
}
```

**Properties:**
- `name`: Field identifier (kebab-case)
- `type`: Always `"text"`
- `label`: Human-readable label
- `value`: Default content
- `required`: Optional, validation
- `placeholder`: Optional, input hint

**Validation:**
- Maximum length: 255 characters
- Required field validation (if specified)
- HTML sanitization

**Template Usage:**
```jinja2
{{ hero_title }}
```

#### 2. Textarea Field
```json
{
  "name": "page-content",
  "type": "textarea",
  "label": "Page Content",
  "value": "Default content here",
  "required": true,
  "rows": 8
}
```

**Properties:**
- `name`: Field identifier
- `type`: Always `"textarea"`
- `label`: Human-readable label
- `value`: Default content
- `required`: Optional validation
- `rows`: Optional, height in rows

**Validation:**
- Maximum length: 5000 characters
- Required field validation
- HTML sanitization
- Auto-resizing interface

**Template Usage:**
```jinja2
<div class="content">
    {{ page_content|safe }}
</div>
```

#### 3. Image Field
```json
{
  "name": "hero-image",
  "type": "image",
  "label": "Hero Background Image",
  "value": "/static/images/default-hero.jpg"
}
```

**Properties:**
- `name`: Field identifier
- `type`: Always `"image"`
- `label`: Human-readable label
- `value`: Default image path

**Validation:**
- File types: JPG, JPEG, PNG, GIF, WebP
- Maximum size: 5MB
- Magic number verification
- Secure filename generation

**Template Usage:**
```jinja2
{% if hero_image %}
<img src="{{ hero_image }}" alt="Hero image" class="img-fluid">
{% endif %}
```

### Advanced Field Configuration

#### Required Fields
```json
{
  "name": "contact-email",
  "type": "text",
  "label": "Contact Email",
  "value": "",
  "required": true
}
```

#### Multiple Fields
```json
"fields": [
  {
    "name": "service-1-title",
    "type": "text",
    "label": "Service 1 Title",
    "value": "Web Design"
  },
  {
    "name": "service-1-description",
    "type": "textarea",
    "label": "Service 1 Description",
    "value": "Professional web design services"
  },
  {
    "name": "service-1-image",
    "type": "image",
    "label": "Service 1 Image",
    "value": "/static/images/service1.jpg"
  }
]
```

### Field Naming Conventions

#### Use Kebab-Case in Config
```json
{
  "name": "hero-title",           // ✅ Correct
  "name": "heroTitle",           // ❌ Avoid
  "name": "page_content",        // ❌ Avoid
  "name": "background-image-url" // ✅ Correct
}
```

#### Access with Underscores in Templates
```jinja2
{{ hero_title }}              // ✅ Correct
{{ heroTitle }}              // ❌ Won't work
{{ page_content }}           // ✅ Auto-converted
{{ background_image_url }}   // ✅ Auto-converted
```

### Validation Rules

#### Text Fields
- Length: 0-255 characters
- Required: If specified, cannot be empty
- Sanitization: HTML tags removed

#### Textarea Fields
- Length: 0-5000 characters
- Required: If specified, cannot be empty
- Sanitization: Limited HTML allowed (when using `|safe` filter)

#### Image Fields
- Types: JPG, JPEG, PNG, GIF, WebP
- Size: Maximum 5MB
- Validation: Magic number verification
- Storage: `/static/images/uploads/`

---

## API Documentation

### Core Functions

#### Configuration Management

##### `load_config()`
```python
def load_config():
    """Load configuration from config.json with validation"""
    pass
```

**Returns:**
- `dict`: Validated configuration dictionary

**Raises:**
- `FileNotFoundError`: Config file missing
- `json.JSONDecodeError`: Invalid JSON format
- `ValueError`: Schema validation failed

**Example:**
```python
config = load_config()
print(config['sitename'])
```

##### `save_config(config)`
```python
def save_config(config):
    """Save configuration to config.json with backup"""
    pass
```

**Parameters:**
- `config` (dict): Configuration dictionary

**Returns:**
- `bool`: Success status

**Example:**
```python
config = load_config()
config['sitename'] = 'New Name'
save_config(config)
```

#### Template Rendering

##### `render_template_with_data(template, page_config=None)`
```python
def render_template_with_data(template, page_config=None):
    """Render template with global and page-specific data"""
    pass
```

**Parameters:**
- `template` (str): Template filename
- `page_config` (dict, optional): Page-specific configuration

**Returns:**
- `str`: Rendered HTML content

**Example:**
```python
html = render_template_with_data('home.html', page_config)
```

#### Validation Functions

##### `validate_config_schema(config)`
```python
def validate_config_schema(config):
    """Validate configuration against schema"""
    pass
```

**Parameters:**
- `config` (dict): Configuration to validate

**Returns:**
- `tuple`: (is_valid, error_messages)

**Example:**
```python
is_valid, errors = validate_config_schema(config)
if not is_valid:
    print("Validation errors:", errors)
```

##### `validate_field_value(field_type, value, field_name)`
```python
def validate_field_value(field_type, value, field_name):
    """Validate field value based on type and constraints"""
    pass
```

**Parameters:**
- `field_type` (str): Field type ('text', 'textarea', 'image')
- `value` (str): Field value to validate
- `field_name` (str): Field name for error messages

**Returns:**
- `tuple`: (validated_value, error_message)

**Example:**
```python
valid_value, error = validate_field_value('text', 'Hello World', 'title')
if error:
    print("Validation failed:", error)
```

#### File Upload Functions

##### `validate_image_file(file)`
```python
def validate_image_file(file):
    """Validate uploaded image file with signature check"""
    pass
```

**Parameters:**
- `file`: Werkzeug FileStorage object

**Returns:**
- `tuple`: (filename, error_message)

**Example:**
```python
filename, error = validate_image_file(request.files['image'])
if error:
    flash(error, 'error')
else:
    # Process valid file
    pass
```

##### `cleanup_unused_images()`
```python
def cleanup_unused_images():
    """Remove unused images from uploads directory"""
    pass
```

**Returns:**
- `tuple`: (removed_count, cleaned_files)

**Example:**
```python
removed_count, files = cleanup_unused_images()
print(f"Removed {removed_count} unused images")
```

### CLI Functions

#### `create_page(title, template, url, menu_title=None)`
```python
def create_page(title, template, url, menu_title=None):
    """Create new page in configuration"""
    pass
```

**Parameters:**
- `title` (str): Page title
- `template` (str): Template filename
- `url` (str): Page URL
- `menu_title` (str, optional): Menu display name

**Returns:**
- `bool`: Success status

**Example:**
```python
success = create_page("About", "about.html", "/about", "About Us")
```

#### `list_pages()`
```python
def list_pages():
    """Display all configured pages"""
    pass
```

**Example:**
```python
list_pages()
```

#### `delete_page(url)`
```python
def delete_page(url):
    """Delete page by URL"""
    pass
```

**Parameters:**
- `url` (str): Page URL to delete

**Returns:**
- `bool`: Success status

**Example:**
```python
success = delete_page("/old-page")
```

### Flask Routes

#### Public Routes

##### `@app.route('/')`
- **Method**: GET
- **Function**: `index()`
- **Purpose**: Home page rendering
- **Template**: Determined by page configuration

##### `@app.route('/<path:url>')`
- **Method**: GET
- **Function**: `public_page(url)`
- **Purpose**: Dynamic page routing
- **Parameters**: `url` - Page path

#### Admin Routes

##### `@app.route('/admin')`
- **Method**: GET
- **Function**: `admin_dashboard()`
- **Purpose**: Admin dashboard
- **Authentication**: Required

##### `@app.route('/admin/login', methods=['GET', 'POST'])`
- **Methods**: GET, POST
- **Function**: `admin_login()`
- **Purpose**: Admin authentication

##### `@app.route('/admin/logout')`
- **Method**: GET
- **Function**: `admin_logout()`
- **Purpose**: Session termination

##### `@app.route('/admin/edit/<int:page_index>', methods=['GET', 'POST'])`
- **Methods**: GET, POST
- **Function**: `edit_page(page_index)`
- **Purpose**: Page content editing
- **Parameters**: `page_index` - Page configuration index

##### `@app.route('/admin/settings', methods=['GET', 'POST'])`
- **Methods**: GET, POST
- **Function**: `admin_settings()`
- **Purpose**: Global settings management

##### `@app.route('/admin/change-password', methods=['GET', 'POST'])`
- **Methods**: GET, POST
- **Function**: `change_password()`
- **Purpose**: Password management

### Error Handling

#### Custom Error Handlers

##### `@app.errorhandler(404)`
```python
def not_found_error(error):
    """Handle 404 errors with appropriate template"""
    pass
```

##### `@app.errorhandler(500)`
```python
def internal_error(error):
    """Handle 500 errors with appropriate template"""
    pass
```

##### `@app.errorhandler(413)`
```python
def too_large(error):
    """Handle file too large errors"""
    pass
```

### Utility Functions

#### `convert_keys_to_underscore(data)`
```python
def convert_keys_to_underscore(data):
    """Convert dictionary keys with hyphens to underscores for Jinja2"""
    pass
```

**Purpose:** Convert config.json keys (kebab-case) to template variables (underscore_case)

**Example:**
```python
config = {"hero-title": "Welcome"}
template_data = convert_keys_to_underscore(config)
# template_data["hero_title"] = "Welcome"
```

#### `sanitize_filename(filename)`
```python
def sanitize_filename(filename):
    """Generate secure filename for uploaded files"""
    pass
```

**Purpose:** Create safe filenames for uploaded images

**Example:**
```python
safe_name = sanitize_filename("user file.jpg")
# Returns: "user_file_abc123.jpg"
```

---

## Contribution Guidelines

### Getting Started

#### Prerequisites
- Python 3.8+
- Git
- Basic knowledge of Flask and Jinja2

#### Setup Development Environment

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/wicara.git
   cd wicara
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Development Server**
   ```bash
   python app.py
   ```

### Development Workflow

#### 1. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
```

#### 2. Make Changes
- Follow coding standards
- Add tests if applicable
- Update documentation

#### 3. Test Your Changes
- Run application locally
- Test admin panel functionality
- Verify templates render correctly
- Test CLI commands

#### 4. Commit Changes
```bash
git add .
git commit -m "feat: add your feature description"
```

#### 5. Push and Create Pull Request
```bash
git push origin feature/your-feature-name
# Create pull request on GitHub
```

### Coding Standards

#### Python Code Style
- Follow PEP 8 guidelines
- Use 4 spaces for indentation
- Line length maximum 79 characters
- Use descriptive variable names

#### Function Documentation
```python
def example_function(param1, param2):
    """Brief description of the function.
    
    Args:
        param1 (str): Description of parameter 1
        param2 (int): Description of parameter 2
        
    Returns:
        bool: Description of return value
        
    Raises:
        ValueError: Description of when this error occurs
    """
    pass
```

#### Error Handling
```python
def risky_operation():
    try:
        # Risky code
        result = do_something()
        return result
    except SpecificException as e:
        # Log error
        app.logger.error(f"Operation failed: {e}")
        # Handle gracefully
        return None
    except Exception as e:
        # Catch-all for unexpected errors
        app.logger.error(f"Unexpected error: {e}")
        raise
```

#### Configuration Validation
```python
def validate_config(config):
    """Validate configuration structure and content."""
    if not isinstance(config, dict):
        raise ValueError("Config must be a dictionary")
    
    required_keys = ['admin-password', 'sitename', 'pages']
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required key: {key}")
    
    return True
```

### Security Guidelines

#### Input Validation
```python
def validate_user_input(input_data, field_type):
    """Validate and sanitize user input."""
    if field_type == 'text':
        if len(input_data) > 255:
            raise ValueError("Text too long")
        # Sanitize HTML
        from bleach import clean
        return clean(input_data)
    # Add other field types...
```

#### File Upload Security
```python
def secure_file_upload(file):
    """Handle file upload with security checks."""
    # Check file type
    if not allowed_file_type(file.filename):
        raise ValueError("File type not allowed")
    
    # Check file size
    if file.content_length > MAX_FILE_SIZE:
        raise ValueError("File too large")
    
    # Generate secure filename
    filename = secure_filename(file.filename)
    return filename
```

#### Password Security
```python
from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password):
    """Generate secure password hash."""
    return generate_password_hash(password, method='scrypt')

def verify_password(hashed_password, input_password):
    """Verify password against hash."""
    return check_password_hash(hashed_password, input_password)
```

### Testing

#### Unit Tests
```python
import unittest
from app import validate_config_schema

class TestConfigValidation(unittest.TestCase):
    def test_valid_config(self):
        config = {
            'admin-password': 'hashed_password',
            'sitename': 'Test Site',
            'pages': []
        }
        is_valid, errors = validate_config_schema(config)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_invalid_config(self):
        config = {}  # Empty config
        is_valid, errors = validate_config_schema(config)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
```

#### Integration Tests
```python
def test_admin_login():
    """Test admin login functionality."""
    with app.test_client() as client:
        response = client.post('/admin/login', data={
            'password': 'admin123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect
        # Follow redirect and check dashboard
        response = client.get('/admin')
        self.assertEqual(response.status_code, 200)
```

#### Run Tests
```bash
python -m pytest tests/
```

### Documentation

#### Update README.md
- Add new features
- Update installation instructions
- Include usage examples

#### Update API Documentation
- Document new functions
- Update parameter descriptions
- Add usage examples

#### Update Configuration Schema
- Document new configuration options
- Provide examples
- Include validation rules

### Pull Request Guidelines

#### PR Requirements
1. **Clear Title**: Descriptive of changes
2. **Detailed Description**: Explain what and why
3. **Testing**: Mention how you tested
4. **Documentation**: Update relevant docs
5. **No Merge Conflicts**: Resolve before submitting

#### PR Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

### Release Process

#### Version Bumping
1. Update version in `app.py`
2. Update CHANGELOG.md
3. Create Git tag

#### Release Checklist
- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version number updated
- [ ] Security review completed

### Community Guidelines

#### Code of Conduct
- Be respectful and inclusive
- Provide constructive feedback
- Help others learn and grow
- Follow professional standards

#### Getting Help
- Read documentation first
- Search existing issues
- Ask questions in discussions
- Provide clear problem descriptions

---

## CLI Reference

### Available Commands

#### `help`
Display help information about all available commands.

```bash
python app.py help
```

**Output:**
```
WICARA CMS - Management Commands

Usage: python app.py <command> [options]

Available commands:
  help                 Show this help message
  create-page          Create a new page
  list-pages           List all configured pages
  delete-page          Delete a page by URL
  run                  Start the web server
```

#### `create-page`
Create a new page in the configuration.

```bash
python app.py create-page <title> <template> <url> [menu-title]
```

**Parameters:**
- `title` (required): Page title
- `template` (required): Template filename
- `url` (required): Page URL path
- `menu-title` (optional): Menu display name

**Examples:**
```bash
# Create about page
python app.py create-page "About Us" "about.html" "/about"

# Create service page with custom menu title
python app.py create-page "Web Development" "services.html" "/web-dev" "Services"

# Create contact page
python app.py create-page "Contact" "contact.html" "/contact" "Get in Touch"
```

**Output:**
```
✅ Page "About Us" created successfully!
📄 Template: about.html
🔗 URL: /about
📋 Menu: About
```

#### `list-pages`
Display all configured pages with their details.

```bash
python app.py list-pages
```

**Output:**
```
📋 WICARA CMS - Page List

[1] Home Page
   URL: /
   Template: home.html
   Menu: Home
   Fields: 8

[2] About Us
   URL: /about
   Template: about.html
   Menu: About
   Fields: 5

[3] Contact
   URL: /contact
   Template: contact.html
   Menu: Contact
   Fields: 4

Total pages: 3
```

#### `delete-page`
Delete a page by its URL.

```bash
python app.py delete-page <url>
```

**Parameters:**
- `url` (required): Page URL to delete

**Examples:**
```bash
# Delete contact page
python app.py delete-page "/contact"

# Delete old services page
python app.py delete-page "/old-services"
```

**Output:**
```
⚠️  Are you sure you want to delete page "/contact"?
This action cannot be undone.

Type 'yes' to confirm: yes

🗑️  Page "/contact" deleted successfully!
   Removed: contact.html
   Cleaned up: 2 unused images
```

#### `run`
Start the WICARA CMS web server.

```bash
python app.py run
```

**Output:**
```
🚀 Starting WICARA CMS...
📍 Server: http://0.0.0.0:5555
🔧 Debug mode: False
📁 Config: /path/to/config.json
🗂️  Templates: /path/to/templates/
🖼️  Uploads: /path/to/static/images/uploads/
✅ Server ready!
```

### Advanced Usage

#### Creating Pages with Custom Fields
```bash
# First create the page
python app.py create-page "Services" "services.html" "/services"

# Then edit config.json to add custom fields
# The CLI will validate the JSON structure
```

#### Batch Operations
```bash
# Create multiple pages
for page in about contact services; do
    python app.py create-page "$page" "${page}.html" "/$page"
done

# List pages to verify
python app.py list-pages
```

#### Error Handling
```bash
# Try to create page with existing URL
python app.py create-page "Home2" "home.html" "/"

# Output:
# ❌ Error: Page with URL "/" already exists
#    Use 'list-pages' to see existing pages
```

### Configuration Management

#### Manual Config Editing
After using CLI commands, you can manually edit `config.json` for advanced configurations:

```bash
# Edit with nano
nano config.json

# Edit with vim
vim config.json

# Validate configuration
python -c "
import app
config = app.load_config()
is_valid, errors = app.validate_config_schema(config)
if is_valid:
    print('✅ Configuration is valid')
else:
    print('❌ Configuration errors:')
    for error in errors:
        print(f'  - {error}')
"
```

#### Backup and Restore
```bash
# Backup configuration
cp config.json config.backup.$(date +%Y%m%d)

# Restore from backup
cp config.backup.20251110 config.json

# Test restored config
python app.py list-pages
```

---

*Last Updated: November 10, 2025*
*Version: 1.0*