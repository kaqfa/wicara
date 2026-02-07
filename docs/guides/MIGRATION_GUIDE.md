# Migration Guide: Legacy Structure to ECS

This guide helps you migrate an existing Wicara installation from the legacy structure to the new Engine-Content Separation (ECS) structure.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Migration Process](#migration-process)
4. [Post-Migration Steps](#post-migration-steps)
5. [Rollback Instructions](#rollback-instructions)
6. [FAQ](#faq)

## Overview

### What is ECS?

Engine-Content Separation (ECS) is a new architectural pattern that separates the CMS engine code from site content. This enables:

- **Better Organization**: Clear separation between engine and content
- **Multi-Site Support**: Multiple sites can share the same engine
- **Easier Upgrades**: Update the engine without affecting content
- **Simpler Backups**: Just backup the `sites/` directory
- **Development Workflow**: Developers work on engine, content editors work on sites

### What Changes?

**Before (Legacy Structure):**
```
wicara/
├── config.json           # Site configuration
├── templates/            # All templates (public + admin)
│   ├── home.html
│   ├── about.html
│   └── admin/
└── static/               # All static files
    ├── css/
    ├── js/
    └── images/
```

**After (ECS Structure):**
```
wicara/
├── app/                  # Engine code
│   └── templates/
│       └── admin/        # Admin templates
├── sites/                # Content directory
│   └── default/          # Default site
│       ├── config.json
│       ├── templates/
│       └── static/
├── config.json           # Legacy backup
└── templates/            # Legacy backup
```

## Prerequisites

### Before You Start

1. **Backup Your Data**
   - The migration script keeps originals, but backup anyway
   - Recommended: Use git to commit current state
   ```bash
   git add .
   git commit -m "Pre-migration backup"
   ```

2. **Check System Requirements**
   - Python 3.7+
   - Wicara v1.0.0+ with ECS support
   - Write permissions to create directories

3. **Verify Current Structure**
   ```bash
   # Check config.json exists
   ls -l config.json

   # Check templates exist
   ls -l templates/

   # Check static files
   ls -l static/
   ```

4. **Test Your Site**
   - Run the site and verify everything works
   - Login to admin panel
   - Check all pages load correctly

## Migration Process

### Step 1: Run the Migration Script

```bash
python run.py migrate
```

Or directly:

```bash
python scripts/migrate_to_sites.py
```

### Step 2: Review Pre-Migration Checks

The script will:
- Check if `config.json` exists
- Check if `templates/` exists
- Warn if `sites/` already exists
- Warn if `app/templates/` already exists

Example output:
```
======================================================================
  WICARA CMS - Migration to Sites Structure
======================================================================

This script will migrate your Wicara installation to the new
Engine-Content Separation (ECS) structure.

What will happen:
  1. Create sites/default/ directory structure
  2. COPY config.json → sites/default/config.json
  3. COPY user templates → sites/default/templates/
  4. COPY user CSS/JS files → sites/default/static/
  5. COPY uploaded images → sites/default/static/images/uploads/
  6. MOVE admin templates → app/templates/admin/
  7. Update .env file with ECS settings

IMPORTANT:
  - Original files will be KEPT as backup (except admin templates)
  - Admin templates will be MOVED (not copied)
  - You can rollback by deleting sites/ and app/templates/

Proceed with migration? (yes/no):
```

### Step 3: Confirm Migration

Type `yes` to proceed.

### Step 4: Monitor Progress

The script will show detailed progress:

```
[Step 1] Checking Prerequisites
----------------------------------------------------------------------
✓ Found config.json (35071 bytes)
✓ Found templates/ directory (10 templates)
✓ Found static/ directory

[Step 2] Creating Directory Structure
----------------------------------------------------------------------
✓ Created sites/default/
✓ Created sites/default/templates/
✓ Created sites/default/static/css/
✓ Created sites/default/static/js/
✓ Created sites/default/static/images/uploads/
✓ Created app/templates/admin/

[Step 3] Copying Configuration Files
----------------------------------------------------------------------
✓ Copied config.json (35071 bytes)
✓ Copied config.json.backup (35071 bytes)

[Step 4] Copying User Templates
----------------------------------------------------------------------
✓ Copied home.html
✓ Copied about.html
✓ Copied contact.html
...

[Step 5] Moving Admin Templates
----------------------------------------------------------------------
✓ Moved admin templates (12 files)
✓ Removed original templates/admin/ directory

[Step 6] Copying Static Files
----------------------------------------------------------------------
✓ Copied CSS: style.css
✓ Copied image: hero.jpg
...

[Step 7] Updating Environment Configuration
----------------------------------------------------------------------
✓ Added ECS configuration to .env

[Step 8] Verifying Migration
----------------------------------------------------------------------
✓ Config file size matches
✓ Total files copied: 25
```

### Step 5: Review Summary

The script will display a summary:

```
======================================================================
  Migration Summary
======================================================================

Files copied:
  - Config: 2 file(s)
  - Templates: 10 file(s)
  - Css: 1 file(s)
  - Images: 5 file(s)

======================================================================
  Migration Complete!
======================================================================

Next steps:
  1. Verify your site works: python run.py
  2. Check http://localhost:5555 in your browser
  3. Test admin panel: http://localhost:5555/admin
  4. If everything works, you can delete old files:
     - Original config.json (backup kept in sites/default/)
     - Original templates/*.html (backup kept in sites/default/)
     - Original static files (backup kept in sites/default/)
```

## Post-Migration Steps

### 1. Verify Your Site

Start the server:
```bash
python run.py
```

Expected output:
```
Loaded 3 environment variable(s) from .env file
Starting server on 0.0.0.0:5555 (debug=True, hot_reload=True)
```

### 2. Test in Browser

**Public Site:**
- Visit: http://localhost:5555
- Test all pages
- Verify images load
- Check navigation

**Admin Panel:**
- Visit: http://localhost:5555/admin
- Login with your credentials
- Verify dashboard loads
- Test editing a page
- Check that changes persist

### 3. Check Directory Structure

```bash
# Verify new structure
ls -la sites/default/
ls -la sites/default/templates/
ls -la sites/default/static/

# Verify admin templates moved
ls -la app/templates/admin/
```

### 4. Check Environment Variables

```bash
cat .env | grep -E "(SITES_DIR|DEFAULT_SITE|LEGACY_MODE)"
```

Should show:
```
SITES_DIR=sites
DEFAULT_SITE=default
LEGACY_MODE=false
```

### 5. Test Key Functionality

- [ ] Homepage loads
- [ ] All pages accessible
- [ ] Admin login works
- [ ] Edit a page
- [ ] Upload an image
- [ ] Change site settings
- [ ] Cache works (if enabled)

### 6. Clean Up (Optional)

Once you've verified everything works, you can delete the legacy files:

```bash
# Backup first (just in case)
tar czf legacy_backup.tar.gz config.json templates/ static/

# Delete legacy files (ONLY after verifying migration!)
# Note: Keep static/css/admin.css and static/js/admin.js
```

**IMPORTANT**: Don't delete:
- `static/css/admin.css` (still used by admin panel)
- `static/js/admin.js` (still used by admin panel)
- `app/` directory (this is the engine!)

## Rollback Instructions

If something goes wrong, you can rollback:

### Quick Rollback

```bash
# 1. Delete new directories
rm -rf sites/
rm -rf app/templates/

# 2. Update .env (or delete it)
sed -i 's/LEGACY_MODE=false/LEGACY_MODE=true/' .env

# 3. Restart
python run.py
```

### Full Rollback

If you deleted legacy files:

```bash
# 1. Restore from backup
tar xzf legacy_backup.tar.gz

# 2. Delete new directories
rm -rf sites/
rm -rf app/templates/

# 3. Restore admin templates
git checkout templates/admin/
# OR restore from backup

# 4. Update .env
sed -i 's/LEGACY_MODE=false/LEGACY_MODE=true/' .env

# 5. Restart
python run.py
```

## FAQ

### Q: Will this affect my live site?

A: No. The migration script only copies files. Your original files remain untouched (except admin templates which are moved). You should still backup first and test on a staging environment.

### Q: Can I run the migration multiple times?

A: Yes. The script will warn if `sites/` exists but will continue if you confirm. However, it will overwrite files in `sites/default/`.

### Q: What if the migration fails halfway?

A: The script stops on errors. Your original files are safe. Check the error message, fix the issue, and re-run the script.

### Q: Do I need to update my code?

A: No. The migration is transparent to your application code. Templates and configuration work the same way.

### Q: Can I still use the legacy structure?

A: Yes! Set `LEGACY_MODE=true` in `.env` and delete the `sites/` directory. This reverts to the legacy behavior.

### Q: What about my custom themes?

A: Custom CSS/JS files are copied to `sites/default/static/`. Update your `.env` if you have custom paths.

### Q: Will my uploaded images still work?

A: Yes. Images are copied to `sites/default/static/images/uploads/`. The application knows where to find them.

### Q: What about plugins?

A: Plugins are in `app/plugins/` and are not affected by the migration.

### Q: Can I migrate multiple sites?

A: This migration creates a single "default" site. For multi-site setups, you'll need to manually create additional site directories under `sites/`.

### Q: What if I have custom templates?

A: All HTML templates (except admin templates) are copied to `sites/default/templates/`. Admin templates are moved to `app/templates/admin/`.

### Q: Will this affect my Git repository?

A: Yes, it will create new files (`sites/`, `scripts/`, `.env`). Commit these changes:
```bash
git add sites/ scripts/ .env
git commit -m "Migrate to ECS structure"
```

### Q: Can I customize the migration?

A: Yes! The script is in `scripts/migrate_to_sites.py`. You can modify it for your needs, but test carefully.

## Troubleshooting

### Error: config.json not found

**Cause**: Running from wrong directory or config.json missing.

**Solution**:
```bash
# Make sure you're in the Wicara root directory
pwd  # Should show /path/to/wicara

# Check if config.json exists
ls -l config.json
```

### Error: Permission denied

**Cause**: Insufficient permissions to create directories.

**Solution**:
```bash
# Check permissions
ls -ld .

# Fix permissions (if safe to do so)
chmod u+w .
```

### Warning: sites/ directory already exists

**Cause**: Previous migration attempt or manual creation.

**Solution**:
- If this is a re-run: Type 'yes' to continue
- If unsure: Backup and delete `sites/` first

### Error: Failed to copy file

**Cause**: Disk space, permissions, or file locked.

**Solution**:
```bash
# Check disk space
df -h .

# Check if file is locked
lsof | grep config.json
```

### Site doesn't work after migration

**Cause**: Various possible issues.

**Solution**:
1. Check `.env` file: `LEGACY_MODE=false`
2. Restart server: `python run.py`
3. Check logs: `tail -f logs/wicara.log`
4. Verify files: `ls -la sites/default/`
5. Test LEGACY_MODE: Set to `true` and test

### Admin panel not found

**Cause**: Admin templates not moved correctly.

**Solution**:
```bash
# Check if admin templates exist
ls -la app/templates/admin/

# If missing, restore from original
cp -r templates/admin app/templates/
```

## Support

If you encounter issues:

1. **Check the logs**: `logs/wicara.log`
2. **Review error messages**: They're designed to be helpful
3. **Test with LEGACY_MODE**: Set to `true` to verify original works
4. **Restore from backup**: Use git or tar backup
5. **Check documentation**: See `docs/` directory

## Related Documentation

- `scripts/README.md` - Migration script documentation
- `docs/specs/ECS_IMPLEMENTATION_PLAN.md` - ECS design specification
- `docs/ECS_CORE_INTEGRATION_IMPLEMENTATION.md` - Implementation details
- `CLAUDE.md` - Developer guidance
- `README.md` - User documentation

## Version History

- **v1.0** (2024-01-17): Initial migration guide for ECS-11
