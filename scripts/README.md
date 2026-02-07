# Wicara CMS Scripts

This directory contains utility scripts for system administration and migration.

## Migration Script (ECS-11)

The migration script helps existing Wicara installations migrate from the legacy structure to the new Engine-Content Separation (ECS) structure.

### What is ECS?

Engine-Content Separation (ECS) is a new architectural pattern that separates the CMS engine code from site content, enabling:
- Better organization of files
- Multi-site support
- Cleaner upgrades (engine updates don't affect content)
- Easier backups (just backup sites/ directory)

### Migration Overview

The migration script performs the following operations:

1. **Checks Prerequisites**
   - Verifies config.json exists
   - Checks if templates/ directory exists
   - Warns if sites/ already exists

2. **Creates Directory Structure**
   - `sites/default/` - Default site directory
   - `sites/default/templates/` - Site templates
   - `sites/default/static/` - Site static files
   - `app/templates/admin/` - Admin templates

3. **Copies Files Safely**
   - Config files: `config.json` → `sites/default/config.json`
   - User templates: `templates/*.html` → `sites/default/templates/`
   - User CSS/JS: `static/css/`, `static/js/` → `sites/default/static/`
   - Uploaded images: `static/images/uploads/` → `sites/default/static/images/uploads/`

4. **Moves Admin Templates**
   - `templates/admin/*` → `app/templates/admin/`

5. **Updates Configuration**
   - Creates or updates `.env` file
   - Sets `SITES_DIR=sites`
   - Sets `DEFAULT_SITE=default`
   - Sets `LEGACY_MODE=false`

### Usage

Run the migration using the CLI command:

```bash
python run.py migrate
```

Or run the script directly:

```bash
python scripts/migrate_to_sites.py
```

### Safety Features

- **Copy, Not Move**: Original files are kept as backup (except admin templates)
- **Interactive Prompts**: Asks for confirmation before proceeding
- **Detailed Progress**: Shows what's happening at each step
- **Error Handling**: Stops on errors and provides clear messages
- **Verification**: Verifies files after copying

### What Gets Copied vs Moved

**Copied (originals kept as backup):**
- `config.json`
- `config.json.backup`
- User templates (`templates/*.html`)
- User CSS files (except `admin.css`)
- User JS files (except `admin*.js`)
- Uploaded images (`static/images/uploads/*`)

**Moved (not copied):**
- Admin templates (`templates/admin/*` → `app/templates/admin/`)

**Not Copied:**
- `static/css/admin.css` (stays in root for admin panel)
- `static/js/admin.js` and `admin*.js` (stay in root for admin panel)

### After Migration

1. **Verify Your Site**
   ```bash
   python run.py
   ```

2. **Test in Browser**
   - Public site: http://localhost:5555
   - Admin panel: http://localhost:5555/admin

3. **Check the Structure**
   ```
   sites/default/
   ├── config.json
   ├── config.json.backup
   ├── templates/
   │   ├── home.html
   │   ├── about.html
   │   └── ...
   └── static/
       ├── css/
       │   └── style.css
       ├── js/
       └── images/
           └── uploads/
   ```

4. **Clean Up (Optional)**
   After verifying everything works, you can delete old files:
   - Original `config.json` (backup is in sites/default/)
   - Original `templates/*.html` (backup is in sites/default/)
   - Original `static/` files (backup is in sites/default/)

### Rollback Instructions

If something goes wrong, you can rollback:

1. Delete `sites/` directory:
   ```bash
   rm -rf sites/
   ```

2. Delete `app/templates/` directory:
   ```bash
   rm -rf app/templates/
   ```

3. Restore admin templates if needed (from backup or git)

4. Update `.env` file:
   ```bash
   # Set LEGACY_MODE back to true or delete these lines:
   LEGACY_MODE=true
   ```

5. Restart application:
   ```bash
   python run.py
   ```

### Troubleshooting

**Error: config.json not found**
- Make sure you're running the script from the Wicara root directory
- Verify config.json exists in the root directory

**Error: templates/ directory not found**
- Verify templates/ directory exists
- Check that you have user templates (*.html files)

**Warning: sites/ directory already exists**
- The script will modify the existing sites/ directory
- You can cancel and backup the existing sites/ directory first

**Migration fails partway through**
- Check the error messages
- The script stops on errors to prevent data loss
- You can safely re-run the script after fixing issues

### Technical Details

- **Script Location**: `scripts/migrate_to_sites.py`
- **Lines of Code**: ~400 lines
- **Language**: Python 3
- **Dependencies**: Standard library only (os, sys, shutil, pathlib, datetime)

### Development

The migration script is part of the Engine-Content Separation (ECS) implementation:
- **Task ID**: ECS-11
- **Dependencies**: ECS-01 through ECS-10
- **Related Documentation**: See `docs/` directory for ECS design docs

### Support

For issues or questions:
1. Check the error messages - they're designed to be helpful
2. Review the rollback instructions above
3. Check the main documentation in `docs/`
4. Review the CLAUDE.md file for architecture details
