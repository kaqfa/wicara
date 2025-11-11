"""
Utility functions for WICARA CMS.
Includes configuration management, validation, and helper functions.
"""

import json
import os
import shutil
import uuid
from pathlib import Path


def convert_keys_to_underscore(data):
    """
    Recursively convert dictionary keys with hyphens to underscores for Jinja2 compatibility.

    Args:
        data: Dictionary, list, or primitive value to convert

    Returns:
        Converted data with underscores instead of hyphens in keys
    """
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


def sanitize_filename(filename):
    """
    Sanitize filename to prevent path traversal attacks.

    Args:
        filename: Original filename to sanitize

    Returns:
        Safe sanitized filename
    """
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


def validate_field_value(field_type, value, field_name):
    """
    Validate field values based on type and constraints.

    Args:
        field_type: Type of field ('text', 'textarea', 'image')
        value: Value to validate
        field_name: Name of field for error messages

    Returns:
        Tuple of (validated_value, error_message)
    """
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
    """
    Validate uploaded image file with signature check.

    Args:
        file: File object to validate

    Returns:
        Tuple of (validated_file, error_message)
    """
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


# ============================================================================
# Configuration Management Functions
# ============================================================================

def load_config(config_file='config.json', validate=True, logger=None):
    """
    Load configuration from JSON file.

    Args:
        config_file: Path to config.json file
        validate: Whether to validate configuration schema
        logger: Logger instance for logging

    Returns:
        Configuration dictionary or None if error
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Validate configuration schema (optional for CLI)
        if validate:
            errors = validate_config_schema(config)
            if errors:
                error_msg = 'Configuration validation failed: ' + '; '.join(errors[:3])
                if logger:
                    logger.error(f'Config validation errors: {errors}')
                return None

        return config
    except FileNotFoundError:
        if logger:
            logger.warning(f'Config file not found: {config_file}, creating default')
        return create_default_config(config_file, logger)
    except json.JSONDecodeError as e:
        if logger:
            logger.error(f'JSON decode error: {e}')
        return None
    except PermissionError:
        if logger:
            logger.error('Permission denied reading config file')
        return None
    except Exception as e:
        if logger:
            logger.error(f'Unexpected error loading config: {e}')
        return None


def save_config(config, config_file='config.json', validate=True, logger=None):
    """
    Save configuration to JSON file with backup.

    Args:
        config: Configuration dictionary to save
        config_file: Path to config.json file
        validate: Whether to validate before saving
        logger: Logger instance for logging

    Returns:
        True if successful, False otherwise
    """
    try:
        # Validate configuration schema before saving (optional for CLI)
        if validate:
            errors = validate_config_schema(config)
            if errors:
                error_msg = 'Configuration validation failed: ' + '; '.join(errors[:3])
                if logger:
                    logger.error(f'Config validation errors: {errors}')
                return False

        # Create backup before saving
        backup_file = config_file + '.backup'
        if os.path.exists(config_file):
            shutil.copy2(config_file, backup_file)

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except PermissionError:
        if logger:
            logger.error('Permission denied saving config file')
        return False
    except json.JSONEncodeError as e:
        if logger:
            logger.error(f'JSON encode error: {e}')
        return False
    except Exception as e:
        if logger:
            logger.error(f'Unexpected error saving config: {e}')
        return False


def create_default_config(config_file='config.json', logger=None):
    """
    Create default configuration file.

    Args:
        config_file: Path to config.json file
        logger: Logger instance for logging

    Returns:
        Default configuration dictionary
    """
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

    if save_config(default_config, config_file, validate=False, logger=logger):
        return default_config
    return None


def cleanup_unused_images(config_file='config.json', logger=None):
    """
    Remove images that are not referenced in config.

    Args:
        config_file: Path to config.json file
        logger: Logger instance for logging

    Returns:
        True if successful, False otherwise
    """
    try:
        config = load_config(config_file, validate=False, logger=logger)
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
                if logger:
                    logger.info(f'Removed unused image: {image_path}')
            except Exception as e:
                if logger:
                    logger.error(f'Failed to remove {image_path}: {e}')

        return True
    except Exception as e:
        if logger:
            logger.error(f'Error during image cleanup: {e}')
        return False


# ============================================================================
# Configuration Schema Validation Functions
# ============================================================================

def validate_config_schema(config):
    """
    Validate configuration structure against expected schema.

    Args:
        config: Configuration dictionary to validate

    Returns:
        List of validation error messages
    """
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
    """
    Validate individual page schema.

    Args:
        page: Page configuration to validate
        index: Page index for error messages
        existing_urls: Set of URLs already used

    Returns:
        List of validation error messages
    """
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
    """
    Validate individual field schema.

    Args:
        field: Field configuration to validate
        page_index: Page index for error messages
        field_index: Field index for error messages
        existing_names: Set of field names already used in page

    Returns:
        List of validation error messages
    """
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
