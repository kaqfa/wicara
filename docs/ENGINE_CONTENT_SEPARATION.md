# Engine-Content Separation Plan for Wicara CMS

## Problem Statement

Saat ini engine (app/, admin templates, admin static) dan content (user templates, config.json, user uploads) tercampur dalam satu direktori, sehingga:
- Update engine bisa mempengaruhi content
- Sulit mengelola static files user bersamaan dengan templates
- Tidak bisa mengembangkan engine dan content secara paralel
- Sulit untuk multi-site support di masa depan

## Proposed Solution

Pisahkan engine dan content ke direktori terpisah dengan path yang konfigurabel.

### Target Directory Structure

```
wicara/
├── app/                         # Engine code (unchanged)
│   ├── modules/                 # Admin, auth, public, import_export
│   ├── core/                    # ConfigManager, FileManager, TemplateManager
│   ├── cache/
│   └── templates/               # ADMIN TEMPLATES ONLY (move from root templates/admin/)
│       └── admin/
│           ├── base.html
│           ├── dashboard.html
│           └── ...
│
├── static/                      # ENGINE STATIC FILES ONLY
│   ├── css/
│   │   └── admin.css
│   └── js/
│       └── admin.js
│
├── content/                     # DEFAULT CONTENT DIRECTORY (NEW)
│   ├── config.json              # Move from root
│   ├── config.json.backup       # Move from root
│   ├── templates/               # USER TEMPLATES ONLY (move from root templates/)
│   │   ├── base.html
│   │   ├── home.html
│   │   ├── about.html
│   │   └── ...
│   └── static/                  # USER STATIC FILES (NEW - move from root static/)
│       ├── css/
│       │   └── style.css
│       ├── js/
│       └── images/
│           └── uploads/         # Move from static/images/uploads
│
├── sites/                       # Multi-site directories (NEW - structure ready)
│   ├── site1/
│   │   ├── config.json
│   │   ├── templates/
│   │   └── static/
│   └── site2/
│       ├── config.json
│       ├── templates/
│       └── static/
│
├── run.py
└── .env                         # New environment variables
```

## Implementation Steps

### Step 1: Create ContentManager Module
**File**: `app/core/content_manager.py` (new)

Manages content directory paths and configuration:
- `get_config_path(site_id)` - Get config file path for site
- `get_templates_dir(site_id)` - Get templates directory
- `get_static_dir(site_id)` - Get static files directory
- `get_uploads_dir(site_id)` - Get uploads directory
- `site_exists(site_id)` - Check if site exists
- `get_all_sites()` - Get all available sites

### Step 2: Update Configuration
**File**: `app/config.py` (modify)

Add new environment variables:
- `CONTENT_DIR=content` - Default content directory
- `SITES_DIR=sites` - Multi-sites directory
- `LEGACY_MODE=false` - Backward compatibility flag

Update properties:
- `CONFIG_FILE` - Dynamic path based on content dir
- `UPLOAD_FOLDER` - Dynamic path based on content dir

### Step 3: Update Application Factory
**File**: `app/__init__.py` (modify)

Changes:
- Initialize `ContentManager` and attach to app
- Configure Jinja2 with ChoiceLoader for engine (app/templates) + content (content/templates) templates
- Add `/content/static/<path:filename>` route for user static files
- Keep engine static at `/static/` (Flask default)
- Support legacy mode for backward compatibility

### Step 4: Update Core Modules

**ConfigManager** (`app/core/config_manager.py`):
- Accept `content_manager` parameter for dynamic path resolution
- Use `content_manager.get_config_path()` instead of hardcoded path

**TemplateManager** (`app/core/template_manager.py`):
- Template rendering automatically uses Jinja2 ChoiceLoader
- No changes needed - Flask handles template resolution

**FileManager** (`app/core/file_manager.py`):
- Use `content_manager.get_uploads_dir()` for upload folder
- Update `cleanup_unused_images()` to use content-aware paths

### Step 5: Update Routes

**Public Routes** (`app/modules/public/routes.py`):
- Use `current_app.content_manager.get_config_path()` for config loading

**Admin Routes** (`app/modules/admin/routes.py`):
- Use `current_app.content_manager` for all path resolutions
- Update upload handling to use content-aware upload directory

### Step 6: Update Import/Export
**File**: `app/modules/import_export/exporter.py` (modify)

- Use content-aware paths for export operations
- Include content directory in export packages

### Step 7: Create Migration Script
**File**: `scripts/migrate_to_content.py` (new)

Automated migration script:
1. Create `content/` directory structure
2. Move user templates from `templates/` (non-admin) to `content/templates/`
3. Move admin templates from `templates/admin/` to `app/templates/admin/`
4. Move user static files (css/style.css, js/) to `content/static/`
5. Keep admin static files (admin.css, admin.js) in `static/`
6. Move uploads from `static/images/uploads` to `content/static/images/uploads`
7. Move `config.json` to `content/`
8. Update `.env` with new configuration
9. Clean up empty `templates/` directory if needed

### Step 8: Update CLI Commands
**File**: `app/modules/cli/commands.py` (modify)

- Update existing commands to use content-aware paths
- Add new command: `python run.py create-site <site_id> <site_name>`
- Add migration command: `python run.py migrate`

### Step 9: Update Entry Point
**File**: `run.py` (modify)

- Add support for new CLI commands
- Load environment variables before creating app
- Display content directory info on startup

### Step 10: Update Environment Variables
**File**: `.env.example` (modify)

Add new variables:
```bash
# Content Configuration
CONTENT_DIR=content              # Default site content directory
SITES_DIR=sites                  # Multi-sites directory (optional)

# Migration (temporary)
LEGACY_MODE=false               # Enable backward compatibility mode
```

## Migration Strategy

### Phase 1: Preparation (No Breaking Changes)
1. Add new environment variables
2. Create ContentManager class
3. Add LEGACY_MODE flag (default: true)
4. Document upcoming changes

### Phase 2: Gradual Migration (Backward Compatible)
1. Set `LEGACY_MODE=true` in `.env`
2. Run migration script to create new structure
3. Test with `LEGACY_MODE=false` to verify
4. Allow users to migrate at their own pace

### Phase 3: Full Transition
1. Update documentation
2. Set `LEGACY_MODE=false` as default
3. Deprecate legacy mode after 2-3 releases

### Rollback Plan
If issues occur:
1. Set `LEGACY_MODE=true` in `.env`
2. Restore from backup: `cp content/config.json.backup config.json`
3. Manual rollback if needed

## Critical Files to Modify

1. **`app/__init__.py`** - Application factory, initialize ContentManager
2. **`app/config.py`** - Add content configuration variables
3. **`app/core/content_manager.py`** - NEW: Content path management
4. **`app/core/config_manager.py`** - Use ContentManager for paths
5. **`app/core/file_manager.py`** - Use ContentManager for upload paths
6. **`app/modules/admin/routes.py`** - Update all path references
7. **`app/modules/public/routes.py`** - Update config loading
8. **`run.py`** - Add migration command
9. **`.env.example`** - Add new environment variables
10. **`scripts/migrate_to_content.py`** - NEW: Migration script

## Verification Plan

### Testing Checklist
- [ ] Legacy mode (`LEGACY_MODE=true`) works with existing structure
- [ ] New mode (`LEGACY_MODE=false`) works with migrated structure
- [ ] Template rendering works in both modes (admin from app/templates, user from content/templates)
- [ ] File uploads work correctly to content/static/images/uploads
- [ ] Admin panel can edit pages and settings
- [ ] Import/export functions work
- [ ] CLI commands work with content-aware paths
- [ ] Engine static files served at `/static/` (admin.css, admin.js)
- [ ] User static files served at `/content/static/` (style.css, user uploads)
- [ ] Sites directory structure is created but routing not yet implemented

### Manual Testing Commands
```bash
# Test legacy mode
echo "LEGACY_MODE=true" >> .env
python run.py

# Test new mode after migration
echo "LEGACY_MODE=false" >> .env
python run.py

# Test migration
python run.py migrate

# Test site creation
python run.py create-site mysite "My Site"
```

### Access Verification
- Public site: http://localhost:5555
- Admin panel: http://localhost:5555/admin
- User static files: http://localhost:5555/content/static/css/style.css (NEW route)
- User uploads: http://localhost:5555/content/static/images/uploads/filename.jpg (NEW route)
- Engine static files: http://localhost:5555/static/css/admin.css (EXISTING route)

## Benefits

1. **Independent Development**: Engine updates won't affect user content
2. **Easy Static Management**: User CSS/JS co-located dengan templates di `content/static/`
3. **Multi-Site Ready**: Struktur `sites/` siap untuk multi-site di masa depan
4. **Clean Upgrades**: Engine (app/) bisa diupdate tanpa touch content directory
5. **Backward Compatible**: Legacy mode allows gradual migration

## Post-Implementation Enhancements

- Multi-site routing based on domain/subdomain (when needed)
- Admin UI for site management (when needed)
- Site cloning templates (when needed)
- Per-site user permissions (when needed)
