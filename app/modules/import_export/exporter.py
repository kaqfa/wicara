"""
Export Engine for WICARA CMS (MIG-01, MIG-02).

Handles:
- ZIP package creation with complete site backup
- Manifest generation with metadata and checksums
- Content validation and sanitization
- Export filtering options (full, partial, content-only)
- Export progress tracking and reporting
"""

import os
import json
import zipfile
import hashlib
import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import shutil

from app.config import WICARA_VERSION


class ExportError(Exception):
    """Custom exception for export operations."""
    pass


class Exporter:
    """Handles exporting WICARA CMS packages as ZIP files."""

    # Export modes
    EXPORT_FULL = 'full'           # All config, templates, and static files
    EXPORT_PARTIAL = 'partial'     # Config and custom templates only
    EXPORT_CONTENT = 'content'     # Only config.json (content-only)

    def __init__(self, config_path: str = 'config.json', app_root: str = '.'):
        """
        Initialize exporter.

        Args:
            config_path: Path to config.json file
            app_root: Root directory of the application
        """
        self.config_path = config_path
        self.app_root = app_root
        self.export_stats = {
            'config_size': 0,
            'templates_count': 0,
            'images_count': 0,
            'total_size': 0,
            'created_at': None
        }

    def export(
        self,
        output_path: str,
        mode: str = EXPORT_FULL,
        include_templates: Optional[List[str]] = None,
        progress_callback=None
    ) -> Tuple[bool, str, Dict]:
        """
        Export WICARA site as ZIP package.

        Args:
            output_path: Output ZIP file path
            mode: Export mode (full, partial, content)
            include_templates: List of specific templates to include (for partial export)
            progress_callback: Callback function for progress updates

        Returns:
            Tuple of (success, message, stats)
        """
        try:
            # Validate config exists
            if not os.path.exists(self.config_path):
                raise ExportError(f"Config file not found: {self.config_path}")

            # Load and validate configuration
            config = self._load_config()
            if not config:
                raise ExportError("Invalid or empty configuration")

            # Validate config schema before export
            validation_errors = self._validate_config(config)
            if validation_errors:
                raise ExportError(f"Config validation failed: {validation_errors[0]}")

            # Create ZIP file
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                if progress_callback:
                    progress_callback(10, "Starting export...")

                # 1. Add config.json
                self._add_config_to_zip(zip_file, config)
                if progress_callback:
                    progress_callback(30, "Config added...")

                # 2. Add templates based on mode
                if mode in [self.EXPORT_FULL, self.EXPORT_PARTIAL]:
                    self._add_templates_to_zip(
                        zip_file,
                        config,
                        mode=mode,
                        include_list=include_templates
                    )
                    if progress_callback:
                        progress_callback(60, "Templates added...")

                # 3. Add images/static files based on mode
                if mode == self.EXPORT_FULL:
                    self._add_static_to_zip(zip_file, config)
                    if progress_callback:
                        progress_callback(80, "Static files added...")

                # 4. Generate and add manifest
                manifest = self._create_manifest(config, mode)
                manifest_json = json.dumps(manifest, indent=2, ensure_ascii=False)
                zip_file.writestr('manifest.json', manifest_json)

                if progress_callback:
                    progress_callback(95, "Manifest created...")

            # Update export stats
            self.export_stats['created_at'] = datetime.datetime.now().isoformat()
            self.export_stats['total_size'] = os.path.getsize(output_path)

            if progress_callback:
                progress_callback(100, "Export completed successfully")

            return True, f"Export successful: {output_path}", self.export_stats

        except ExportError as e:
            return False, f"Export error: {str(e)}", {}
        except Exception as e:
            return False, f"Unexpected error during export: {str(e)}", {}

    def _load_config(self) -> Optional[Dict]:
        """Load and parse config.json."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.export_stats['config_size'] = os.path.getsize(self.config_path)
                return config
        except (json.JSONDecodeError, IOError) as e:
            raise ExportError(f"Failed to load config: {str(e)}")

    def _validate_config(self, config: Dict) -> List[str]:
        """
        Validate configuration structure.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check required keys
        required_keys = ['admin-password', 'sitename', 'pages']
        for key in required_keys:
            if key not in config:
                errors.append(f"Missing required key: {key}")

        # Validate pages array
        if 'pages' in config:
            if not isinstance(config['pages'], list):
                errors.append("Pages must be an array")
            elif len(config['pages']) == 0:
                errors.append("At least one page is required")

        return errors

    def _add_config_to_zip(self, zip_file: zipfile.ZipFile, config: Dict):
        """Add config.json to ZIP."""
        config_json = json.dumps(config, indent=2, ensure_ascii=False)
        zip_file.writestr('config.json', config_json)

    def _add_templates_to_zip(
        self,
        zip_file: zipfile.ZipFile,
        config: Dict,
        mode: str = EXPORT_FULL,
        include_list: Optional[List[str]] = None
    ):
        """Add templates to ZIP based on export mode."""
        templates_dir = os.path.join(self.app_root, 'templates')

        if not os.path.exists(templates_dir):
            return

        count = 0

        # For partial export, collect template names from config
        if mode == self.EXPORT_PARTIAL:
            template_names = set()
            for page in config.get('pages', []):
                template = page.get('template')
                if template:
                    template_names.add(template)

            # Add specific templates from include_list if provided
            if include_list:
                template_names.update(include_list)
        else:
            template_names = None  # Include all

        # Add templates to ZIP
        for root, dirs, files in os.walk(templates_dir):
            for file in files:
                if not file.endswith('.html'):
                    continue

                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, self.app_root)

                # For partial export, check if template should be included
                if mode == self.EXPORT_PARTIAL and template_names:
                    template_name = os.path.basename(file)
                    if template_name not in template_names:
                        continue

                if os.path.isfile(file_path):
                    zip_file.write(file_path, arcname)
                    count += 1

        self.export_stats['templates_count'] = count

    def _add_static_to_zip(self, zip_file: zipfile.ZipFile, config: Dict):
        """Add static files (CSS, JS, images) to ZIP."""
        static_dir = os.path.join(self.app_root, 'static')

        if not os.path.exists(static_dir):
            return

        image_count = 0

        # Collect all referenced images
        referenced_images = set()
        for page in config.get('pages', []):
            for field in page.get('fields', []):
                if field.get('type') == 'image' and field.get('value'):
                    value = field['value']
                    if value.startswith('/static/images/uploads/'):
                        # Store relative path
                        rel_path = value[1:]  # Remove leading slash
                        referenced_images.add(rel_path)

        # Add all files in static directory
        for root, dirs, files in os.walk(static_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, self.app_root)

                # For images, only include referenced ones (not unused)
                if 'images/uploads' in file_path:
                    rel_path = arcname.replace('\\', '/')
                    if rel_path in referenced_images:
                        zip_file.write(file_path, arcname)
                        image_count += 1
                else:
                    # Always include CSS and JS
                    zip_file.write(file_path, arcname)

        self.export_stats['images_count'] = image_count

    def _create_manifest(self, config: Dict, mode: str) -> Dict:
        """
        Create export manifest with metadata and checksums.

        Returns:
            Manifest dictionary
        """
        manifest = {
            'version': WICARA_VERSION,
            'export_mode': mode,
            'exported_at': datetime.datetime.now().isoformat(),
            'site_name': config.get('sitename', 'Unknown'),
            'pages_count': len(config.get('pages', [])),
            'checksum': self._calculate_config_checksum(config),
            'compatibility': {
                'min_version': '1.0.0',
                'max_version': WICARA_VERSION,
                'schema_version': '1.0'
            },
            'export_stats': {
                'config_size': self.export_stats['config_size'],
                'templates_count': self.export_stats['templates_count'],
                'images_count': self.export_stats['images_count']
            }
        }

        return manifest

    @staticmethod
    def _calculate_config_checksum(config: Dict) -> str:
        """Calculate SHA256 checksum of config."""
        config_str = json.dumps(config, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(config_str.encode('utf-8')).hexdigest()

    @staticmethod
    def validate_export_package(zip_path: str) -> Tuple[bool, str]:
        """
        Validate export package structure.

        Returns:
            Tuple of (valid, message)
        """
        try:
            if not os.path.exists(zip_path):
                return False, "ZIP file not found"

            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                # Check for required files
                files = zip_file.namelist()
                if 'config.json' not in files:
                    return False, "Missing config.json in package"
                if 'manifest.json' not in files:
                    return False, "Missing manifest.json in package"

                # Validate manifest
                try:
                    manifest_data = zip_file.read('manifest.json')
                    manifest = json.loads(manifest_data)

                    # Check manifest structure
                    required_keys = ['version', 'export_mode', 'exported_at']
                    for key in required_keys:
                        if key not in manifest:
                            return False, f"Invalid manifest: missing '{key}'"

                except json.JSONDecodeError:
                    return False, "Invalid manifest.json format"

                # Validate config
                try:
                    config_data = zip_file.read('config.json')
                    config = json.loads(config_data)

                    if 'sitename' not in config or 'pages' not in config:
                        return False, "Invalid config.json structure"

                except json.JSONDecodeError:
                    return False, "Invalid config.json format"

            return True, "Export package is valid"

        except zipfile.BadZipFile:
            return False, "Invalid ZIP file"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
