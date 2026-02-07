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


def save_upload_file(file, upload_folder=None, site_manager=None, site_id=None):
    """
    Save uploaded file to upload folder with unique name.

    Supports both legacy mode (upload_folder parameter) and sites mode (site_manager).
    If site_manager is provided, it takes precedence over upload_folder parameter.

    Args:
        file: File object to save
        upload_folder: Target upload folder path (legacy mode, optional)
        site_manager: SiteManager instance for ECS (takes precedence, optional)
        site_id: Site identifier for multi-site support (optional, uses default if None)

    Returns:
        Tuple of (file_path, unique_filename)

    Raises:
        ValueError: If neither upload_folder nor site_manager is provided
    """
    # ECS-05: Support site_manager for multi-site uploads
    if site_manager is not None:
        upload_folder = site_manager.get_uploads_dir(site_id)
    elif upload_folder is None:
        raise ValueError("Either upload_folder or site_manager must be provided")

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


def cleanup_unused_images(config, logger=None, site_manager=None, site_id=None, upload_dir=None):
    """
    Remove images that are not referenced in config.

    Supports both legacy mode (hardcoded upload_dir) and sites mode (site_manager).
    If site_manager is provided, uses site-specific upload directory.

    Args:
        config: Configuration dictionary
        logger: Logger instance for logging
        site_manager: SiteManager instance for ECS (optional)
        site_id: Site identifier for multi-site support (optional, uses default if None)
        upload_dir: Custom upload directory (optional, for testing purposes)
                   If not provided, uses default paths

    Returns:
        True if successful, False otherwise
    """
    try:
        # ECS-05: Support site_manager for multi-site cleanup
        if site_manager is not None:
            upload_dir = site_manager.get_uploads_dir(site_id)
            # In sites mode, paths should be relative to site root
            path_prefix = '/sites/'
            if site_id is None:
                site_id = site_manager.default_site
        elif upload_dir is None:
            # Legacy mode with default path
            upload_dir = os.path.join('static', 'images', 'uploads')
            path_prefix = '/static/images/uploads/'
        else:
            # Custom upload_dir provided (for testing)
            path_prefix = '/static/images/uploads/'

        # Get all referenced image paths
        referenced_images = set()

        # Check page fields and extract filenames (not full paths)
        referenced_filenames = set()

        for page in config.get('pages', []):
            for field in page.get('fields', []):
                if field.get('type') == 'image' and field.get('value'):
                    value = field['value']

                    # Extract just the filename from various path formats
                    if value.startswith(f'/sites/') and '/static/images/uploads/' in value:
                        # Sites mode path: /sites/{site_id}/static/images/uploads/filename
                        filename = value.split('/static/images/uploads/')[-1]
                        referenced_filenames.add(filename)
                    elif value.startswith('/static/images/uploads/'):
                        # Legacy mode path: /static/images/uploads/filename
                        filename = value.split('/static/images/uploads/')[-1]
                        referenced_filenames.add(filename)

        # Get all uploaded images
        if not os.path.exists(upload_dir):
            if logger:
                logger.debug(f'Upload directory does not exist: {upload_dir}')
            return True

        # Compare filenames, not full paths
        uploaded_files = []
        for filename in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, filename)
            if os.path.isfile(file_path):
                uploaded_files.append((filename, file_path))

        # Remove unused images by comparing filenames
        removed_count = 0

        # Debug logging
        if logger:
            logger.debug(f'Referenced filenames: {referenced_filenames}')
            logger.debug(f'Uploaded files: {[f[0] for f in uploaded_files]}')

        for filename, file_path in uploaded_files:
            if filename not in referenced_filenames:
                # This file is not referenced in the config
                try:
                    os.remove(file_path)
                    removed_count += 1
                    if logger:
                        logger.info(f'Removed unused image: {file_path}')
                except Exception as e:
                    if logger:
                        logger.error(f'Failed to remove {file_path}: {e}')

        if logger and removed_count > 0:
            logger.info(f'Cleaned up {removed_count} unused image(s)')

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
