#!/usr/bin/env python
"""
Wicara CMS - Migration Script for Engine-Content Separation (ECS-11)
Migrates existing installations from legacy structure to sites/ structure.

This script safely copies content to the new sites/default/ structure while
keeping original files as backup.

Usage:
    python run.py migrate
    or
    python scripts/migrate_to_sites.py
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime


class MigrationScript:
    """Handles migration from legacy structure to sites/ structure."""

    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.sites_dir = self.root_dir / 'sites'
        self.default_site_dir = self.sites_dir / 'default'
        self.errors = []
        self.warnings = []
        self.copied_files = {
            'config': [],
            'templates': [],
            'css': [],
            'js': [],
            'images': []
        }

    def print_header(self, text):
        """Print formatted header."""
        print(f"\n{'=' * 70}")
        print(f"  {text}")
        print(f"{'=' * 70}\n")

    def print_step(self, step_num, text):
        """Print formatted step."""
        print(f"\n[Step {step_num}] {text}")
        print("-" * 70)

    def print_success(self, text):
        """Print success message."""
        print(f"✓ {text}")

    def print_warning(self, text):
        """Print warning message."""
        print(f"⚠ WARNING: {text}")
        self.warnings.append(text)

    def print_error(self, text):
        """Print error message."""
        print(f"✗ ERROR: {text}")
        self.errors.append(text)

    def check_prerequisites(self):
        """Check if migration can proceed."""
        self.print_step(1, "Checking Prerequisites")

        # Check if config.json exists
        config_file = self.root_dir / 'config.json'
        if not config_file.exists():
            self.print_error("config.json not found in root directory")
            return False
        self.print_success(f"Found config.json ({config_file.stat().st_size} bytes)")

        # Check if templates/ exists
        templates_dir = self.root_dir / 'templates'
        if not templates_dir.exists():
            self.print_error("templates/ directory not found")
            return False

        template_count = len(list(templates_dir.glob('*.html')))
        self.print_success(f"Found templates/ directory ({template_count} templates)")

        # Check if static/ exists
        static_dir = self.root_dir / 'static'
        if not static_dir.exists():
            self.print_warning("static/ directory not found")
        else:
            self.print_success("Found static/ directory")

        # Warn if sites/ already exists
        if self.sites_dir.exists():
            self.print_warning("sites/ directory already exists!")
            print("  This migration will modify the existing sites/ directory.")
            response = input("  Continue anyway? (yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                print("\nMigration cancelled by user.")
                return False

        # Warn if app/templates/ already exists
        app_templates_dir = self.root_dir / 'app' / 'templates'
        if app_templates_dir.exists():
            self.print_warning("app/templates/ directory already exists!")
            print("  Admin templates will be moved to app/templates/admin/")
            response = input("  Continue anyway? (yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                print("\nMigration cancelled by user.")
                return False

        return True

    def confirm_migration(self):
        """Ask user to confirm migration."""
        self.print_header("WICARA CMS - Migration to Sites Structure")

        print("This script will migrate your Wicara installation to the new")
        print("Engine-Content Separation (ECS) structure.\n")

        print("What will happen:")
        print("  1. Create sites/default/ directory structure")
        print("  2. COPY config.json → sites/default/config.json")
        print("  3. COPY user templates → sites/default/templates/")
        print("  4. COPY user CSS/JS files → sites/default/static/")
        print("  5. COPY uploaded images → sites/default/static/images/uploads/")
        print("  6. MOVE admin templates → app/templates/admin/")
        print("  7. Update .env file with ECS settings")
        print("\nIMPORTANT:")
        print("  - Original files will be KEPT as backup (except admin templates)")
        print("  - Admin templates will be MOVED (not copied)")
        print("  - You can rollback by deleting sites/ and app/templates/")

        print("\n")
        response = input("Proceed with migration? (yes/no): ").strip().lower()
        return response in ['yes', 'y']

    def create_directory_structure(self):
        """Create sites/default/ directory structure."""
        self.print_step(2, "Creating Directory Structure")

        directories = [
            self.default_site_dir,
            self.default_site_dir / 'templates',
            self.default_site_dir / 'static' / 'css',
            self.default_site_dir / 'static' / 'js',
            self.default_site_dir / 'static' / 'images' / 'uploads',
            self.root_dir / 'app' / 'templates' / 'admin'
        ]

        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                self.print_success(f"Created {directory.relative_to(self.root_dir)}/")
            except Exception as e:
                self.print_error(f"Failed to create {directory}: {e}")
                return False

        return True

    def copy_config_files(self):
        """Copy config.json and backup to sites/default/."""
        self.print_step(3, "Copying Configuration Files")

        files_to_copy = [
            ('config.json', 'Main configuration file'),
            ('config.json.backup', 'Configuration backup (if exists)')
        ]

        for filename, description in files_to_copy:
            src = self.root_dir / filename
            dst = self.default_site_dir / filename

            if not src.exists():
                if filename == 'config.json.backup':
                    self.print_warning(f"{description} not found, skipping")
                    continue
                else:
                    self.print_error(f"{description} not found at {src}")
                    return False

            try:
                shutil.copy2(src, dst)
                file_size = dst.stat().st_size
                self.print_success(f"Copied {filename} ({file_size} bytes)")
                self.copied_files['config'].append(filename)
            except Exception as e:
                self.print_error(f"Failed to copy {filename}: {e}")
                return False

        return True

    def copy_user_templates(self):
        """Copy user templates to sites/default/templates/."""
        self.print_step(4, "Copying User Templates")

        src_dir = self.root_dir / 'templates'
        dst_dir = self.default_site_dir / 'templates'

        # Copy all HTML files except those in admin/ subdirectory
        html_files = [f for f in src_dir.glob('*.html')]

        if not html_files:
            self.print_warning("No user templates found")
            return True

        for src_file in html_files:
            dst_file = dst_dir / src_file.name
            try:
                shutil.copy2(src_file, dst_file)
                self.print_success(f"Copied {src_file.name}")
                self.copied_files['templates'].append(src_file.name)
            except Exception as e:
                self.print_error(f"Failed to copy {src_file.name}: {e}")
                return False

        print(f"\nCopied {len(html_files)} template file(s)")
        return True

    def move_admin_templates(self):
        """Move admin templates to app/templates/admin/."""
        self.print_step(5, "Moving Admin Templates")

        src_dir = self.root_dir / 'templates' / 'admin'
        dst_dir = self.root_dir / 'app' / 'templates' / 'admin'

        if not src_dir.exists():
            self.print_warning("templates/admin/ directory not found, skipping")
            return True

        try:
            # Move entire admin directory
            if dst_dir.exists():
                shutil.rmtree(dst_dir)

            shutil.copytree(src_dir, dst_dir)

            # Count files moved
            admin_files = list(dst_dir.rglob('*'))
            file_count = len([f for f in admin_files if f.is_file()])

            self.print_success(f"Moved admin templates ({file_count} files)")

            # Remove original admin directory
            shutil.rmtree(src_dir)
            self.print_success("Removed original templates/admin/ directory")

        except Exception as e:
            self.print_error(f"Failed to move admin templates: {e}")
            return False

        return True

    def copy_static_files(self):
        """Copy user CSS, JS, and images to sites/default/static/."""
        self.print_step(6, "Copying Static Files")

        static_src = self.root_dir / 'static'
        static_dst = self.default_site_dir / 'static'

        if not static_src.exists():
            self.print_warning("static/ directory not found, skipping")
            return True

        # Copy CSS files (except admin.css)
        css_src = static_src / 'css'
        css_dst = static_dst / 'css'
        if css_src.exists():
            for css_file in css_src.glob('*.css'):
                if css_file.name != 'admin.css':
                    try:
                        shutil.copy2(css_file, css_dst / css_file.name)
                        self.print_success(f"Copied CSS: {css_file.name}")
                        self.copied_files['css'].append(css_file.name)
                    except Exception as e:
                        self.print_error(f"Failed to copy {css_file.name}: {e}")

        # Copy JS files (except admin.js and admin*.js)
        js_src = static_src / 'js'
        js_dst = static_dst / 'js'
        if js_src.exists():
            for js_file in js_src.glob('*.js'):
                if not js_file.name.startswith('admin'):
                    try:
                        shutil.copy2(js_file, js_dst / js_file.name)
                        self.print_success(f"Copied JS: {js_file.name}")
                        self.copied_files['js'].append(js_file.name)
                    except Exception as e:
                        self.print_error(f"Failed to copy {js_file.name}: {e}")

        # Copy uploaded images
        uploads_src = static_src / 'images' / 'uploads'
        uploads_dst = static_dst / 'images' / 'uploads'
        if uploads_src.exists():
            image_files = list(uploads_src.glob('*'))
            for img_file in image_files:
                if img_file.is_file():
                    try:
                        shutil.copy2(img_file, uploads_dst / img_file.name)
                        self.print_success(f"Copied image: {img_file.name}")
                        self.copied_files['images'].append(img_file.name)
                    except Exception as e:
                        self.print_error(f"Failed to copy {img_file.name}: {e}")

            if image_files:
                print(f"\nCopied {len(image_files)} uploaded image(s)")

        return True

    def update_env_file(self):
        """Update .env file with ECS settings."""
        self.print_step(7, "Updating Environment Configuration")

        env_file = self.root_dir / '.env'
        env_example = self.root_dir / '.env.example'

        # If .env doesn't exist, copy from .env.example
        if not env_file.exists():
            if env_example.exists():
                try:
                    shutil.copy2(env_example, env_file)
                    self.print_success("Created .env from .env.example")
                except Exception as e:
                    self.print_error(f"Failed to create .env: {e}")
                    return False
            else:
                # Create minimal .env file
                try:
                    with open(env_file, 'w') as f:
                        f.write("# Wicara CMS Configuration\n")
                        f.write(f"# Generated by migration script on {datetime.now().isoformat()}\n\n")
                    self.print_success("Created new .env file")
                except Exception as e:
                    self.print_error(f"Failed to create .env: {e}")
                    return False

        # Read current .env content
        try:
            with open(env_file, 'r') as f:
                lines = f.readlines()
        except Exception as e:
            self.print_error(f"Failed to read .env: {e}")
            return False

        # Check if ECS variables already exist
        has_sites_dir = any('SITES_DIR=' in line for line in lines)
        has_default_site = any('DEFAULT_SITE=' in line for line in lines)
        has_legacy_mode = any('LEGACY_MODE=' in line for line in lines)

        # Add ECS configuration if not present
        if not (has_sites_dir and has_default_site and has_legacy_mode):
            try:
                with open(env_file, 'a') as f:
                    f.write("\n# Engine-Content Separation Configuration\n")
                    f.write("# Added by migration script\n")
                    if not has_sites_dir:
                        f.write("SITES_DIR=sites\n")
                    if not has_default_site:
                        f.write("DEFAULT_SITE=default\n")
                    if not has_legacy_mode:
                        f.write("LEGACY_MODE=false\n")

                self.print_success("Added ECS configuration to .env")
            except Exception as e:
                self.print_error(f"Failed to update .env: {e}")
                return False
        else:
            # Update LEGACY_MODE to false
            try:
                new_lines = []
                for line in lines:
                    if 'LEGACY_MODE=' in line and not line.strip().startswith('#'):
                        new_lines.append('LEGACY_MODE=false\n')
                    else:
                        new_lines.append(line)

                with open(env_file, 'w') as f:
                    f.writelines(new_lines)

                self.print_success("Updated LEGACY_MODE=false in .env")
            except Exception as e:
                self.print_error(f"Failed to update .env: {e}")
                return False

        return True

    def verify_migration(self):
        """Verify that files were copied correctly."""
        self.print_step(8, "Verifying Migration")

        # Verify config.json
        src_config = self.root_dir / 'config.json'
        dst_config = self.default_site_dir / 'config.json'

        if src_config.stat().st_size == dst_config.stat().st_size:
            self.print_success("Config file size matches")
        else:
            self.print_warning("Config file size mismatch")

        # Count files in each category
        total_copied = sum(len(files) for files in self.copied_files.values())
        self.print_success(f"Total files copied: {total_copied}")

        return True

    def print_summary(self):
        """Print migration summary and next steps."""
        self.print_header("Migration Summary")

        print("Files copied:")
        for category, files in self.copied_files.items():
            if files:
                print(f"  - {category.capitalize()}: {len(files)} file(s)")

        if self.warnings:
            print(f"\nWarnings: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"  ⚠ {warning}")

        if self.errors:
            print(f"\nErrors: {len(self.errors)}")
            for error in self.errors:
                print(f"  ✗ {error}")
            return False

        self.print_header("Migration Complete!")

        print("Next steps:")
        print("  1. Verify your site works: python run.py")
        print("  2. Check http://localhost:5555 in your browser")
        print("  3. Test admin panel: http://localhost:5555/admin")
        print("  4. If everything works, you can delete old files:")
        print("     - Original config.json (backup kept in sites/default/)")
        print("     - Original templates/*.html (backup kept in sites/default/)")
        print("     - Original static files (backup kept in sites/default/)")

        print("\nRollback instructions (if needed):")
        print("  1. Delete sites/ directory")
        print("  2. Delete app/templates/ directory")
        print("  3. Restore templates/admin/ from backup if needed")
        print("  4. Set LEGACY_MODE=true in .env (or delete .env)")
        print("  5. Restart application")

        print("\nNew directory structure:")
        print("  sites/default/")
        print("    ├── config.json")
        print("    ├── templates/")
        print("    └── static/")
        print("  app/templates/admin/")

        return True


def migrate_to_sites():
    """Run the migration process."""
    migrator = MigrationScript()

    # Check prerequisites
    if not migrator.check_prerequisites():
        return False

    # Confirm migration
    if not migrator.confirm_migration():
        print("\nMigration cancelled.")
        return False

    # Run migration steps
    steps = [
        migrator.create_directory_structure,
        migrator.copy_config_files,
        migrator.copy_user_templates,
        migrator.move_admin_templates,
        migrator.copy_static_files,
        migrator.update_env_file,
        migrator.verify_migration,
    ]

    for step in steps:
        if not step():
            print("\n" + "=" * 70)
            print("Migration FAILED. Please check errors above.")
            print("=" * 70)
            return False

    # Print summary
    return migrator.print_summary()


if __name__ == '__main__':
    success = migrate_to_sites()
    sys.exit(0 if success else 1)
