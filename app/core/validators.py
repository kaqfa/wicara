"""
WICARA Core Module: Validators
Handles all validation logic for configuration, fields, and uploads.
"""

import os


# ============================================================================
# Field Validation
# ============================================================================

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
# Configuration Schema Validation
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
