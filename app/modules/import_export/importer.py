"""
Import Engine for WICARA CMS (MIG-03).

Handles:
- ZIP validation and security checks
- Conflict resolution strategies (merge, replace, skip)
- Import rollback capability
- Data validation and error reporting
- Partial import support
"""

import os
import json
import zipfile
import shutil
import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Callable

from app.config import WICARA_VERSION


class ImportError(Exception):
    """Custom exception for import operations."""
    pass


class ImportConflictResolver:
    """Handles import conflicts with different resolution strategies."""

    STRATEGY_MERGE = 'merge'        # Merge pages, keep existing if duplicates
    STRATEGY_REPLACE = 'replace'    # Replace everything
    STRATEGY_SKIP = 'skip'          # Skip conflicting items

    def __init__(self, strategy: str = STRATEGY_MERGE):
        """Initialize conflict resolver."""
        self.strategy = strategy
        self.conflicts = []

    def resolve_page_conflict(
        self,
        existing_page: Dict,
        imported_page: Dict
    ) -> Optional[Dict]:
        """
        Resolve page conflicts based on strategy.

        Returns:
            Resolved page or None if should skip
        """
        if self.strategy == self.STRATEGY_MERGE:
            # Merge strategy: keep existing, record conflict
            self.conflicts.append({
                'type': 'page_duplicate',
                'url': existing_page.get('url'),
                'action': 'skipped_existing_kept'
            })
            return None

        elif self.strategy == self.STRATEGY_REPLACE:
            # Replace strategy: use imported version
            self.conflicts.append({
                'type': 'page_duplicate',
                'url': imported_page.get('url'),
                'action': 'replaced'
            })
            return imported_page

        else:  # STRATEGY_SKIP
            # Skip strategy: don't import
            self.conflicts.append({
                'type': 'page_duplicate',
                'url': imported_page.get('url'),
                'action': 'skipped'
            })
            return None

    def resolve_setting_conflict(
        self,
        key: str,
        existing_value,
        imported_value
    ) -> Tuple[bool, any]:
        """
        Resolve global setting conflicts.

        Returns:
            Tuple of (should_update, value_to_use)
        """
        if self.strategy == self.STRATEGY_MERGE:
            return False, existing_value

        elif self.strategy == self.STRATEGY_REPLACE:
            return True, imported_value

        else:  # STRATEGY_SKIP
            return False, existing_value


class Importer:
    """Handles importing WICARA CMS packages from ZIP files."""

    def __init__(
        self,
        config_path: str = 'config.json',
        app_root: str = '.',
        backup_enabled: bool = True,
        site_manager=None
    ):
        """
        Initialize importer.

        Args:
            config_path: Path to config.json file
            app_root: Root directory of the application
            backup_enabled: Whether to create backup before import
            site_manager: Optional SiteManager instance for ECS path resolution
        """
        self.site_manager = site_manager

        # Use SiteManager for path resolution if available, otherwise use provided paths
        if site_manager:
            self.config_path = site_manager.get_config_path()
            self.app_root = app_root  # Still needed for relative path calculations
        else:
            self.config_path = config_path
            self.app_root = app_root

        self.backup_enabled = backup_enabled
        self.backup_path = None
        self.import_stats = {
            'pages_imported': 0,
            'templates_imported': 0,
            'images_imported': 0,
            'settings_updated': False,
            'conflicts_found': 0,
            'imported_at': None
        }

    def import_package(
        self,
        zip_path: str,
        conflict_strategy: str = ImportConflictResolver.STRATEGY_MERGE,
        import_templates: bool = True,
        import_images: bool = True,
        preview_only: bool = False,
        progress_callback: Optional[Callable] = None
    ) -> Tuple[bool, str, Dict]:
        """
        Import WICARA package from ZIP.

        Args:
            zip_path: Path to ZIP file
            conflict_strategy: How to handle conflicts
            import_templates: Whether to import templates
            import_images: Whether to import images
            preview_only: If True, only validate without importing
            progress_callback: Callback for progress updates

        Returns:
            Tuple of (success, message, stats)
        """
        try:
            # Validate ZIP file
            valid, msg = self._validate_zip(zip_path)
            if not valid:
                return False, f"ZIP validation failed: {msg}", {}

            if progress_callback:
                progress_callback(10, "ZIP validated...")

            # Create backup if enabled
            if not preview_only and self.backup_enabled:
                self._create_backup()
                if progress_callback:
                    progress_callback(15, "Backup created...")

            # Load current config
            current_config = self._load_config()
            if not current_config:
                raise ImportError("Failed to load current configuration")

            # Load imported config
            imported_config = self._load_config_from_zip(zip_path)
            if not imported_config:
                raise ImportError("Failed to load config from package")

            if progress_callback:
                progress_callback(25, "Configurations loaded...")

            # Check version compatibility
            valid, msg = self._check_compatibility(zip_path)
            if not valid:
                if not preview_only:
                    self._rollback_backup()
                return False, f"Compatibility check failed: {msg}", {}

            # Preview mode: return what would be imported
            if preview_only:
                preview = self._generate_import_preview(
                    current_config,
                    imported_config,
                    conflict_strategy
                )
                return True, "Preview generated successfully", preview

            # Initialize conflict resolver
            resolver = ImportConflictResolver(conflict_strategy)

            # Merge configurations
            merged_config = self._merge_configs(
                current_config,
                imported_config,
                resolver
            )

            if progress_callback:
                progress_callback(50, "Configurations merged...")

            # Import templates
            if import_templates:
                self._import_templates(zip_path)
                if progress_callback:
                    progress_callback(75, "Templates imported...")

            # Import images
            if import_images:
                self._import_images(zip_path, imported_config)
                if progress_callback:
                    progress_callback(90, "Images imported...")

            # Save merged config
            if not self._save_config(merged_config):
                raise ImportError("Failed to save merged configuration")

            # Update import stats
            self.import_stats['conflicts_found'] = len(resolver.conflicts)
            self.import_stats['imported_at'] = datetime.datetime.now().isoformat()

            if progress_callback:
                progress_callback(100, "Import completed successfully")

            return True, "Import completed successfully", self.import_stats

        except ImportError as e:
            # Rollback on error
            if not preview_only and self.backup_enabled:
                self._rollback_backup()
            return False, f"Import error: {str(e)}", {}
        except Exception as e:
            # Rollback on unexpected error
            if not preview_only and self.backup_enabled:
                self._rollback_backup()
            return False, f"Unexpected error during import: {str(e)}", {}

    def _validate_zip(self, zip_path: str) -> Tuple[bool, str]:
        """Validate ZIP file structure and contents."""
        try:
            if not os.path.exists(zip_path):
                return False, "ZIP file not found"

            if not zipfile.is_zipfile(zip_path):
                return False, "Invalid ZIP file format"

            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Check for required files
                files = zf.namelist()
                if 'config.json' not in files:
                    return False, "Missing config.json"
                if 'manifest.json' not in files:
                    return False, "Missing manifest.json"

                # Validate manifest
                try:
                    manifest_data = zf.read('manifest.json')
                    manifest = json.loads(manifest_data)
                    if not isinstance(manifest, dict):
                        return False, "Invalid manifest structure"
                except (json.JSONDecodeError, KeyError):
                    return False, "Corrupted manifest.json"

                # Validate config
                try:
                    config_data = zf.read('config.json')
                    config = json.loads(config_data)
                    if not isinstance(config, dict):
                        return False, "Invalid config structure"
                    if 'pages' not in config:
                        return False, "Config missing pages array"
                except (json.JSONDecodeError, KeyError):
                    return False, "Corrupted config.json"

            return True, "ZIP validation passed"

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def _check_compatibility(self, zip_path: str) -> Tuple[bool, str]:
        """Check version and schema compatibility."""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                manifest_data = zf.read('manifest.json')
                manifest = json.loads(manifest_data)

                # Get version info
                export_version = manifest.get('version', '1.0.0')
                compatibility = manifest.get('compatibility', {})

                # Check version compatibility
                min_version = compatibility.get('min_version', '1.0.0')
                max_version = compatibility.get('max_version', WICARA_VERSION)

                # Simple version comparison (could be enhanced)
                if WICARA_VERSION < min_version:
                    return False, f"WICARA version {WICARA_VERSION} is too old"

                return True, "Compatibility check passed"

        except Exception as e:
            return False, f"Compatibility check error: {str(e)}"

    def _load_config(self) -> Optional[Dict]:
        """Load current config.json."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            raise ImportError(f"Failed to load current config: {str(e)}")

    def _load_config_from_zip(self, zip_path: str) -> Optional[Dict]:
        """Load config.json from ZIP file."""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                config_data = zf.read('config.json')
                return json.loads(config_data)
        except (json.JSONDecodeError, KeyError, IOError) as e:
            raise ImportError(f"Failed to load config from ZIP: {str(e)}")

    def _merge_configs(
        self,
        current: Dict,
        imported: Dict,
        resolver: ImportConflictResolver
    ) -> Dict:
        """
        Merge imported config with current config.

        Returns:
            Merged configuration
        """
        merged = current.copy()

        # Merge global settings
        settings_to_merge = ['sitename', 'description', 'keywords', 'footer']
        for setting in settings_to_merge:
            if setting in imported:
                should_update, value = resolver.resolve_setting_conflict(
                    setting,
                    current.get(setting),
                    imported.get(setting)
                )
                if should_update:
                    merged[setting] = value
                    self.import_stats['settings_updated'] = True

        # Merge pages
        imported_pages = imported.get('pages', [])
        current_pages = current.get('pages', [])

        for imported_page in imported_pages:
            imported_url = imported_page.get('url')

            # Check for existing page with same URL
            existing_page = next(
                (p for p in current_pages if p.get('url') == imported_url),
                None
            )

            if existing_page:
                # Resolve conflict
                resolved = resolver.resolve_page_conflict(
                    existing_page,
                    imported_page
                )
                if resolved:
                    # Replace existing page
                    merged['pages'] = [
                        resolved if p.get('url') == imported_url else p
                        for p in merged['pages']
                    ]
                    self.import_stats['pages_imported'] += 1
            else:
                # Add new page
                merged['pages'].append(imported_page)
                self.import_stats['pages_imported'] += 1

        return merged

    def _import_templates(self, zip_path: str):
        """Import templates from ZIP."""
        try:
            # Use SiteManager for path resolution if available
            if self.site_manager:
                templates_dir = self.site_manager.get_templates_dir()
            else:
                templates_dir = os.path.join(self.app_root, 'templates')

            with zipfile.ZipFile(zip_path, 'r') as zf:

                for file_info in zf.infolist():
                    if file_info.filename.startswith('templates/') and file_info.filename.endswith('.html'):
                        # Extract template
                        target_path = os.path.join(self.app_root, file_info.filename)
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)

                        with open(target_path, 'wb') as f:
                            f.write(zf.read(file_info.filename))

                        self.import_stats['templates_imported'] += 1

        except Exception as e:
            raise ImportError(f"Failed to import templates: {str(e)}")

    def _import_images(self, zip_path: str, imported_config: Dict):
        """Import images from ZIP."""
        try:
            # Use SiteManager for path resolution if available
            if self.site_manager:
                uploads_dir = self.site_manager.get_uploads_dir()
            else:
                uploads_dir = os.path.join(self.app_root, 'static', 'images', 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)

            with zipfile.ZipFile(zip_path, 'r') as zf:
                for file_info in zf.infolist():
                    if file_info.filename.startswith('static/images/uploads/'):
                        # Extract image
                        target_path = os.path.join(self.app_root, file_info.filename)
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)

                        with open(target_path, 'wb') as f:
                            f.write(zf.read(file_info.filename))

                        self.import_stats['images_imported'] += 1

        except Exception as e:
            raise ImportError(f"Failed to import images: {str(e)}")

    def _save_config(self, config: Dict) -> bool:
        """Save merged configuration."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            raise ImportError(f"Failed to save config: {str(e)}")

    def _create_backup(self):
        """Create backup of current configuration and files."""
        try:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = f'backups/import_backup_{timestamp}'
            os.makedirs(backup_dir, exist_ok=True)

            # Backup config
            if os.path.exists(self.config_path):
                shutil.copy2(
                    self.config_path,
                    os.path.join(backup_dir, 'config.json')
                )

            # Backup templates - use SiteManager if available
            if self.site_manager:
                templates_src = self.site_manager.get_templates_dir()
            else:
                templates_src = os.path.join(self.app_root, 'templates')

            if os.path.exists(templates_src):
                shutil.copytree(
                    templates_src,
                    os.path.join(backup_dir, 'templates'),
                    dirs_exist_ok=True
                )

            # Backup images - use SiteManager if available
            if self.site_manager:
                images_src = self.site_manager.get_uploads_dir()
            else:
                images_src = os.path.join(self.app_root, 'static', 'images', 'uploads')

            if os.path.exists(images_src):
                shutil.copytree(
                    images_src,
                    os.path.join(backup_dir, 'images'),
                    dirs_exist_ok=True
                )

            self.backup_path = backup_dir

        except Exception as e:
            raise ImportError(f"Failed to create backup: {str(e)}")

    def _rollback_backup(self):
        """Restore from backup."""
        if not self.backup_path or not os.path.exists(self.backup_path):
            return

        try:
            # Restore config
            backup_config = os.path.join(self.backup_path, 'config.json')
            if os.path.exists(backup_config):
                shutil.copy2(backup_config, self.config_path)

            # Restore templates - use SiteManager if available
            backup_templates = os.path.join(self.backup_path, 'templates')
            if os.path.exists(backup_templates):
                if self.site_manager:
                    templates_dest = self.site_manager.get_templates_dir()
                else:
                    templates_dest = os.path.join(self.app_root, 'templates')

                if os.path.exists(templates_dest):
                    shutil.rmtree(templates_dest)
                shutil.copytree(backup_templates, templates_dest)

            # Restore images - use SiteManager if available
            backup_images = os.path.join(self.backup_path, 'images')
            if os.path.exists(backup_images):
                if self.site_manager:
                    images_dest = self.site_manager.get_uploads_dir()
                else:
                    images_dest = os.path.join(self.app_root, 'static', 'images', 'uploads')

                if os.path.exists(images_dest):
                    shutil.rmtree(images_dest)
                shutil.copytree(backup_images, images_dest)

        except Exception as e:
            pass  # Log but don't raise

    def _generate_import_preview(
        self,
        current_config: Dict,
        imported_config: Dict,
        conflict_strategy: str
    ) -> Dict:
        """Generate preview of what would be imported."""
        preview = {
            'pages_to_import': 0,
            'pages_to_update': 0,
            'templates_to_import': 0,
            'images_to_import': 0,
            'conflicts': [],
            'settings_changes': {}
        }

        # Check pages
        for imported_page in imported_config.get('pages', []):
            url = imported_page.get('url')
            exists = any(p.get('url') == url for p in current_config.get('pages', []))

            if exists:
                preview['pages_to_update'] += 1
                preview['conflicts'].append({
                    'type': 'page_exists',
                    'url': url,
                    'title': imported_page.get('title')
                })
            else:
                preview['pages_to_import'] += 1

        return preview
