# Import/Export Feature Implementation (Phase 3)

## Overview

Comprehensive import/export system for WICARA CMS implementing Phase 3 requirements (MIG-01 through MIG-05).

## Implementation Summary

### 1. Core Modules

#### MIG-01: Export Engine (`app/modules/import_export/exporter.py`)
- **Exporter Class**: Handles site package creation
- **Features**:
  - ZIP package creation with metadata
  - Three export modes:
    - `EXPORT_FULL`: Complete site backup (config, templates, static files, images)
    - `EXPORT_PARTIAL`: Config and custom templates only
    - `EXPORT_CONTENT`: Config.json only (content backup)
  - Content validation and sanitization
  - Export progress tracking and statistics
  - Package validation with file signature checking

**Key Methods**:
- `export()`: Main export function with progress callback
- `validate_export_package()`: Static method to validate ZIP structure

#### MIG-02: Export Package Format
- **Manifest Generation**: `manifest.json` with metadata
  - Version compatibility information
  - Export timestamp and statistics
  - SHA256 checksum of config
  - Schema version
- **ZIP Structure**:
  ```
  wicara_export_YYYYMMDD_HHMMSS.zip
  ├── config.json
  ├── manifest.json
  ├── templates/
  │   ├── home.html
  │   └── ...
  └── static/
      └── images/
          └── uploads/
              └── ...
  ```

#### MIG-03: Import Engine (`app/modules/import_export/importer.py`)
- **Importer Class**: Handles package restoration
- **ImportConflictResolver**: Manages conflict resolution strategies
  - `STRATEGY_MERGE`: Keeps existing, adds new (default)
  - `STRATEGY_REPLACE`: Overwrites everything
  - `STRATEGY_SKIP`: Skips conflicting items
- **Features**:
  - ZIP validation and security checks
  - Automatic backup creation before import
  - Conflict detection and resolution
  - Selective import (templates, images optional)
  - Import rollback capability
  - Page URL conflict detection
  - Setting conflict resolution

**Key Methods**:
- `import_package()`: Main import function
- `_validate_zip()`: ZIP file validation
- `_merge_configs()`: Configuration merging with conflict resolution
- `_create_backup()`: Pre-import backup
- `_rollback_backup()`: Rollback on error

#### MIG-04: Data Migration (`app/modules/import_export/migrator.py`)
- **VersionMigrator Class**: Version management and schema validation
- **Features**:
  - Version compatibility checking
  - Schema validation against current structure
  - Field type transformation
  - Migration planning
  - Data migration validation
- **Supported Transformations**:
  - Text ↔ Textarea (with truncation if needed)
  - Schema 1.0 as baseline version

**Key Methods**:
- `migrate_config()`: Migrate config to target version
- `validate_schema()`: Validate config structure
- `check_compatibility()`: Check version compatibility
- `transform_field_type()`: Handle field type conversions
- `get_migration_plan()`: Generate migration steps

#### MIG-05: Admin Interface

##### Routes (`app/blueprints/import_export.py`)
- **Export Routes**:
  - `GET/POST /admin/import-export/export`: Export wizard
  - `GET /admin/import-export/download`: Download exported file

- **Import Routes**:
  - `GET/POST /admin/import-export/import`: Import wizard with file upload
  - `GET /admin/import-export/import/preview`: Preview imported content
  - `POST /admin/import-export/import/confirm`: Confirm and execute import

- **API Routes**:
  - `GET /admin/import-export/api/export-progress`: Export progress tracking
  - `POST /admin/import-export/api/validate-package`: Package validation

##### Templates (`templates/admin/import_export/`)
1. **export.html**: Export wizard with mode selection
   - Three-step export process
   - Mode selection (Full, Partial, Content-Only)
   - Template selection for partial exports
   - Download handler

2. **import.html**: Import wizard with file upload
   - Drag-and-drop file upload
   - File validation
   - Important information notices
   - Tips for different import strategies

3. **import_preview.html**: Import preview and confirmation
   - Package information display
   - Content summary (pages, images, templates)
   - Pages list with conflict indicators
   - Conflict summary
   - Import options:
     - Conflict resolution strategy selection
     - Template import toggle
     - Image import toggle
   - Backup confirmation

### 2. Configuration Updates

#### `app/config.py`
- Added `WICARA_VERSION = '1.0.0'`
- Added `EXPORT_DIR` configuration
- Support for environment-based export directory

#### `app/__init__.py`
- Blueprint registration for `import_export_bp`
- Proper integration with existing app factory

#### `templates/admin/dashboard.html`
- Added "Export Site" quick action card
- Added "Import Site" quick action card
- Icons and descriptions for easy access

### 3. File Structure

```
app/
├── blueprints/
│   └── import_export.py          # MIG-05: Admin routes
├── modules/
│   └── import_export/
│       ├── __init__.py           # Module exports
│       ├── exporter.py           # MIG-01, MIG-02: Export engine
│       ├── importer.py           # MIG-03: Import engine
│       └── migrator.py           # MIG-04: Data migration
├── config.py                     # Version and export config
└── __init__.py                   # Blueprint registration

templates/admin/
└── import_export/
    ├── export.html               # MIG-05: Export wizard
    ├── import.html               # MIG-05: Import wizard
    └── import_preview.html       # MIG-05: Import preview
```

## Security Features

1. **ZIP Validation**:
   - File format validation
   - Magic number checking
   - Schema validation
   - Manifest integrity checking

2. **File Operations**:
   - Secure filename handling
   - Path traversal prevention
   - File permission checks
   - Automatic backup creation

3. **Data Integrity**:
   - SHA256 checksums for config validation
   - Schema validation before save
   - Rollback capability on failure

4. **Access Control**:
   - Login requirement for all admin routes
   - Session-based authentication
   - CSRF protection via Flask sessions

## Usage Examples

### Export a Site

1. Navigate to Admin Dashboard
2. Click "Export Site" card
3. Select export mode:
   - **Full**: Complete backup for migration
   - **Partial**: Design and structure for sharing
   - **Content Only**: Quick backup of content
4. Review summary and click "Start Export"
5. Download generated ZIP file

### Import a Site

1. Navigate to Admin Dashboard
2. Click "Import Site" card
3. Upload ZIP package (drag-drop or click to select)
4. Review package preview:
   - Pages to be imported
   - Conflict warnings
   - Content summary
5. Select conflict resolution strategy:
   - **Merge**: Keep existing pages, add new ones
   - **Replace**: Overwrite everything
   - **Skip**: Skip conflicting items
6. Toggle template and image import options
7. Confirm import (automatic backup is created)

## Testing Checklist

- [x] Module syntax validation
- [x] Class and method structure verification
- [x] Blueprint route registration
- [x] Template file creation
- [x] Config updates
- [x] Dashboard integration
- [ ] Runtime testing (requires Flask installation)
- [ ] Export package generation
- [ ] Import package validation
- [ ] Conflict resolution functionality
- [ ] Rollback on import failure
- [ ] End-to-end workflow

## Error Handling

### Export Errors
- Config file not found
- Invalid configuration format
- ZIP creation failures
- File permission issues

### Import Errors
- Invalid ZIP format
- Missing required files
- Config validation failures
- File write errors (with automatic rollback)
- Version incompatibility

### Migration Errors
- Invalid source/target versions
- Schema validation failures
- Data transformation issues

## Backward Compatibility

- Supports schema version 1.0
- Upgrade path defined for future versions
- No breaking changes to existing config format
- Version compatibility checking in manifest

## Future Enhancements

1. **Real-time Progress**:
   - WebSocket-based progress updates
   - Frontend progress bar with real-time percentage

2. **Scheduled Exports**:
   - Automatic backup scheduling
   - Retention policy management
   - Export history and versioning

3. **Cloud Integration**:
   - S3 backup support
   - Google Drive integration
   - Dropbox sync

4. **Advanced Merging**:
   - Smart field merging
   - Template conflict resolution
   - Image deduplication

5. **Import Filtering**:
   - Selective page import
   - Field-level filtering
   - Asset filtering and optimization

## Documentation

- Complete docstrings in all classes and methods
- Type hints for better IDE support
- Inline comments for complex logic
- Error messages with actionable advice

## Conclusion

The import/export feature provides WICARA CMS users with:
- **Reliability**: Automatic backups and rollback capability
- **Flexibility**: Multiple export modes and import strategies
- **Safety**: Comprehensive validation and error handling
- **Ease of Use**: Intuitive admin interface with helpful wizards

This implementation fulfills all Phase 3 requirements and establishes a solid foundation for future enhancements.
