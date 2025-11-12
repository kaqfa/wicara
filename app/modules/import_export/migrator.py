"""
Data Migration Module for WICARA CMS (MIG-04).

Handles:
- Version compatibility checking
- Schema migration utilities
- Data transformation tools
- Migration validation and error reporting
"""

import json
from typing import Dict, List, Tuple, Optional
from distutils.version import LooseVersion


class MigrationError(Exception):
    """Custom exception for migration operations."""
    pass


class VersionMigrator:
    """Handles version-based migrations and schema transformations."""

    # Schema versions
    SCHEMA_1_0 = '1.0'
    CURRENT_SCHEMA = SCHEMA_1_0

    # Version mapping for migrations
    MIGRATIONS = {
        '1.0.0': 'schema_1_0',
    }

    def __init__(self, from_version: str = '1.0.0', to_version: str = '1.0.0'):
        """
        Initialize migrator.

        Args:
            from_version: Source version
            to_version: Target version
        """
        self.from_version = from_version
        self.to_version = to_version
        self.migration_log = []

    def migrate_config(self, config: Dict, target_version: Optional[str] = None) -> Tuple[bool, Dict, List[str]]:
        """
        Migrate configuration to target version.

        Args:
            config: Configuration to migrate
            target_version: Target version (defaults to current)

        Returns:
            Tuple of (success, migrated_config, messages)
        """
        try:
            target = target_version or self.to_version
            messages = []

            # Determine migration path
            current_version = self.from_version
            migrated_config = config.copy()

            # Check version compatibility
            valid, msg = self.check_compatibility(current_version, target)
            if not valid:
                return False, config, [msg]

            messages.append(f"Starting migration from {current_version} to {target}")

            # Apply migrations
            if LooseVersion(current_version) == LooseVersion('1.0.0'):
                if LooseVersion(target) >= LooseVersion('1.0.0'):
                    # Schema 1.0 is baseline, no migration needed
                    messages.append("Config is already in latest schema")
                    return True, migrated_config, messages

            return True, migrated_config, messages

        except Exception as e:
            return False, config, [f"Migration error: {str(e)}"]

    def validate_schema(self, config: Dict) -> Tuple[bool, List[str]]:
        """
        Validate configuration schema.

        Returns:
            Tuple of (valid, error_list)
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
                    page_errors = self._validate_page(page, i, urls)
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

        return len(errors) == 0, errors

    def check_compatibility(
        self,
        source_version: str,
        target_version: str
    ) -> Tuple[bool, str]:
        """
        Check if migration between versions is supported.

        Returns:
            Tuple of (compatible, message)
        """
        try:
            # All versions are compatible with 1.0.0
            source_v = LooseVersion(source_version)
            target_v = LooseVersion(target_version)

            # Check version bounds
            min_version = LooseVersion('1.0.0')
            max_version = LooseVersion('2.0.0')

            if source_v < min_version:
                return False, f"Source version {source_version} is not supported (minimum: 1.0.0)"

            if source_v > max_version:
                return False, f"Source version {source_version} is too new"

            if target_v < min_version:
                return False, f"Target version {target_version} is not supported"

            if target_v > max_version:
                return False, f"Target version {target_version} is too new"

            return True, f"Migration from {source_version} to {target_version} is supported"

        except Exception as e:
            return False, f"Version comparison error: {str(e)}"

    def transform_field_type(
        self,
        field: Dict,
        old_type: str,
        new_type: str
    ) -> Tuple[bool, Dict]:
        """
        Transform field type with data conversion.

        Args:
            field: Field to transform
            old_type: Current field type
            new_type: Target field type

        Returns:
            Tuple of (success, transformed_field)
        """
        try:
            transformed = field.copy()
            value = field.get('value', '')

            # Validate transformation is possible
            allowed_transforms = {
                ('text', 'textarea'): True,
                ('textarea', 'text'): True,
                ('text', 'image'): False,
                ('image', 'text'): False,
            }

            key = (old_type, new_type)
            if key not in allowed_transforms:
                if old_type == new_type:
                    return True, transformed
                return False, field

            if not allowed_transforms[key]:
                return False, field

            transformed['type'] = new_type

            # Apply type-specific transformations
            if old_type == 'textarea' and new_type == 'text':
                # Truncate textarea to text size (255 chars)
                if value and len(value) > 255:
                    transformed['value'] = value[:255].rstrip()

            return True, transformed

        except Exception as e:
            return False, field

    def get_migration_plan(
        self,
        from_version: str,
        to_version: str
    ) -> Dict:
        """
        Generate migration plan between versions.

        Returns:
            Migration plan with steps and requirements
        """
        try:
            from_v = LooseVersion(from_version)
            to_v = LooseVersion(to_version)

            plan = {
                'from_version': from_version,
                'to_version': to_version,
                'steps': [],
                'breaking_changes': [],
                'data_losses': [],
                'estimated_duration': 'quick'
            }

            # Currently all versions are compatible
            if from_v == to_v:
                plan['steps'].append('No migration needed - versions are identical')
            elif from_v < to_v:
                plan['steps'].append(f'Upgrade from {from_version} to {to_version}')
                plan['steps'].append('Schema validation')
                plan['steps'].append('Field validation')
            else:
                plan['steps'].append(f'Downgrade from {from_version} to {to_version}')
                plan['breaking_changes'].append('Downgrade may lose recent features')

            return plan

        except Exception as e:
            return {
                'error': str(e),
                'from_version': from_version,
                'to_version': to_version
            }

    def validate_data_migration(
        self,
        source_config: Dict,
        target_config: Dict
    ) -> Tuple[bool, List[str]]:
        """
        Validate that data migration was successful.

        Returns:
            Tuple of (successful, issues)
        """
        issues = []

        # Check page count
        source_pages = len(source_config.get('pages', []))
        target_pages = len(target_config.get('pages', []))

        if source_pages != target_pages:
            issues.append(
                f"Page count mismatch: {source_pages} source, {target_pages} target"
            )

        # Check page URLs
        source_urls = {p.get('url') for p in source_config.get('pages', [])}
        target_urls = {p.get('url') for p in target_config.get('pages', [])}

        if source_urls != target_urls:
            missing = source_urls - target_urls
            extra = target_urls - source_urls
            if missing:
                issues.append(f"Missing pages: {missing}")
            if extra:
                issues.append(f"Extra pages: {extra}")

        # Validate schema
        valid, schema_errors = self.validate_schema(target_config)
        if not valid:
            issues.extend(schema_errors)

        return len(issues) == 0, issues

    # =========================================================================
    # Private Methods
    # =========================================================================

    @staticmethod
    def _validate_page(page: Dict, index: int, existing_urls: set) -> List[str]:
        """Validate individual page."""
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
                errors.append(f"{prefix}: URL '{url}' is already used")
            else:
                existing_urls.add(url)

        # Validate fields
        if 'fields' in page:
            fields = page['fields']
            if not isinstance(fields, list):
                errors.append(f"{prefix}: Fields must be an array")
            else:
                field_names = set()
                for i, field in enumerate(fields):
                    field_errors = VersionMigrator._validate_field(
                        field,
                        index,
                        i,
                        field_names
                    )
                    errors.extend(field_errors)

        return errors

    @staticmethod
    def _validate_field(field: Dict, page_index: int, field_index: int, existing_names: set) -> List[str]:
        """Validate individual field."""
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
                errors.append(f"{prefix}: Field name '{name}' is duplicated")
            else:
                existing_names.add(name)

        # Validate type
        if 'type' in field:
            field_type = field['type']
            valid_types = ['text', 'textarea', 'image']
            if field_type not in valid_types:
                errors.append(f"{prefix}: Invalid type '{field_type}'")

        # Validate label
        if 'label' in field:
            label = field['label']
            if not isinstance(label, str) or not label.strip():
                errors.append(f"{prefix}: Label must be a non-empty string")

        return errors
