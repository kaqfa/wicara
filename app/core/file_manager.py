"""
WICARA Core Module: File Manager
Handles file operations, uploads, and image cleanup.
"""

import os
import shutil
import uuid


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


def save_upload_file(file, upload_folder):
    """
    Save uploaded file to upload folder with unique name.

    Args:
        file: File object to save
        upload_folder: Target upload folder path

    Returns:
        Tuple of (file_path, unique_filename)
    """
    safe_filename = sanitize_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{safe_filename}"
    file_path = os.path.join(upload_folder, unique_filename)

    # Ensure upload directory exists
    os.makedirs(upload_folder, exist_ok=True)

    file.save(file_path)
    return file_path, unique_filename


def delete_file(file_path):
    """
    Delete a file safely.

    Args:
        file_path: Path to file to delete

    Returns:
        True if successful, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception:
        return False
    return False


def delete_image(image_path):
    """
    Delete an image file.

    Args:
        image_path: Full path to image file (with /static prefix)

    Returns:
        True if successful, False otherwise
    """
    if image_path and image_path.startswith('/static/images/uploads/'):
        file_path = image_path[1:]  # Remove leading slash
        return delete_file(file_path)
    return False


def create_backup(config_file):
    """
    Create backup of configuration file.

    Args:
        config_file: Path to config file

    Returns:
        Path to backup file or None
    """
    try:
        if os.path.exists(config_file):
            backup_file = config_file + '.backup'
            shutil.copy2(config_file, backup_file)
            return backup_file
    except Exception:
        pass
    return None


def cleanup_unused_images(config, logger=None):
    """
    Remove images that are not referenced in config.

    Args:
        config: Configuration dictionary
        logger: Logger instance for logging

    Returns:
        True if successful, False otherwise
    """
    try:
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


def ensure_directories(app):
    """
    Ensure all required directories exist.

    Args:
        app: Flask application instance
    """
    # Create upload directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Create logs directory
    log_dir = os.path.dirname(app.config['LOG_FILE'])
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
