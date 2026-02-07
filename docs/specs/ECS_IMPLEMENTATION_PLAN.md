# Engine-Content Separation (ECS) Implementation Plan

## Executive Summary

This plan details the implementation of Engine-Content Separation (ECS) for Wicara CMS, separating engine code from user content to enable independent development, easier upgrades, and multi-site readiness. The implementation will leverage the existing multisite infrastructure (Phase 5) which is built but not yet integrated.

## 1. Current State Analysis

### 1.1 Directory Structure
```
wicara/
├── app/                         # Engine code
│   ├── __init__.py              # App factory (160 lines)
│   ├── config.py                # Hard-coded paths
│   ├── core/                    # Core modules
│   │   ├── config_manager.py   # Uses self.config_file
│   │   ├── file_manager.py     # Hard-coded 'static/images/uploads'
│   │   └── template_manager.py # Hard-coded 'templates/'
│   ├── modules/                 # Route modules
│   │   ├── admin/routes.py     # 221 lines, hard-coded paths
│   │   ├── public/routes.py    # 111 lines, uses CONFIG_FILE
│   │   └── cli/commands.py     # Hard-coded 'config.json'
│   ├── multisite/              # EXISTS but NOT integrated
│   │   ├── manager.py          # SiteManager ready to use
│   │   └── context.py          # SiteContext ready to use
│   └── cache/                   # Uses hard-coded config paths
├── templates/                   # Mixed admin + public templates
│   ├── admin/                   # Admin templates (should move to app/)
│   └── *.html                   # Public templates (should move to sites/)
├── static/                      # Engine static files only
│   ├── css/admin.css           # Admin styles
│   └── js/
├── config.json                  # User content (should move to sites/)
└── config.json.backup
```

### 1.2 Hard-coded Path References

Found **118 occurrences** across **20 files**:

**Critical Files:**
1. `app/config.py` - CONFIG_FILE = 'config.json', UPLOAD_FOLDER
2. `app/core/config_manager.py` - self.config_file parameter
3. `app/core/file_manager.py` - 'static/images/uploads' in 5 places
4. `app/core/template_manager.py` - os.path.join('templates', ...)
5. `app/modules/admin/routes.py` - 8 references to CONFIG_FILE and upload paths
6. `app/modules/public/routes.py` - 4 references to CONFIG_FILE
7. `app/modules/cli/commands.py` - 8 references to 'config.json'
8. `app/modules/import_export/exporter.py` - Hard-coded paths for export
9. `app/modules/import_export/importer.py` - Hard-coded paths for import
10. `app/__init__.py` - template_folder and static_folder hard-coded

### 1.3 Key Discovery

**The multisite infrastructure already exists** in `app/multisite/`:
- `SiteManager` - Site CRUD, path management
- `SiteContext` - Per-request site context
- `SiteRouter` - Domain-based routing
- `SiteIsolation` - Security boundaries

**Status:** Built (Phase 5 - marked "COMPLETE") but NOT integrated into app factory

### 1.4 Template Loading

Current implementation in `app/__init__.py`:
```python
template_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
app = Flask(__name__, template_folder=template_folder, ...)
```

**Challenge:** Need to support both engine templates (admin/) and site templates (user content)

## 2. Proposed Architecture

### 2.1 Target Directory Structure

```
wicara/
├── app/                         # ENGINE CODE ONLY
│   ├── templates/               # ADMIN TEMPLATES ONLY (moved from root)
│   │   └── admin/
│   │       ├── base.html
│   │       ├── dashboard.html
│   │       └── ...
│   ├── core/
│   │   └── site_manager.py      # NEW: Simplified site path manager
│   └── ...
│
├── static/                      # ENGINE STATIC FILES ONLY
│   ├── css/admin.css
│   └── js/
│
├── sites/                       # ALL USER CONTENT (NEW)
│   ├── default/                 # Default site (migrated content)
│   │   ├── config.json          # Moved from root
│   │   ├── config.json.backup
│   │   ├── templates/           # User templates (moved from root)
│   │   │   ├── base.html
│   │   │   ├── home.html
│   │   │   └── ...
│   │   └── static/              # User static files (NEW)
│   │       ├── css/style.css    # User CSS
│   │       ├── js/              # User JS
│   │       └── images/
│   │           └── uploads/     # User uploads
│   │
│   └── site2/                   # Additional sites (future)
│       ├── config.json
│       ├── templates/
│       └── static/
│
├── run.py
└── .env                         # Updated with new vars
```

### 2.2 Separation Principles

**Engine (app/):**
- Application code
- Core modules
- Admin templates and assets
- Plugin system
- Cache system

**Content (sites/{site_id}/):**
- User configuration (config.json)
- User templates
- User static files (CSS, JS, images)
- User uploads

### 2.3 Path Abstraction Layer

**New Component:** `SiteManager` (simplified version)
- Can be a wrapper around `multisite.SiteManager` or a standalone implementation
- Provides site-aware path resolution
- Supports legacy mode

```python
class SiteManager:
    def get_config_path(site_id='default') -> str
    def get_templates_dir(site_id='default') -> str
    def get_static_dir(site_id='default') -> str
    def get_uploads_dir(site_id='default') -> str
    def site_exists(site_id) -> bool
    def create_site(site_id) -> bool
```

## 3. Implementation Strategy

### 3.1 Decision: Multisite Integration vs Simple ECS

**Option A: Full Multisite Integration**
- Use existing `app/multisite/manager.py`
- Integrate multisite router and context
- Enable domain-based routing immediately
- More complex, higher risk

**Option B: Simple ECS First (RECOMMENDED)**
- Create lightweight `app/core/site_manager.py`
- Single default site support initially
- Easier migration path
- Lower risk, faster implementation
- Can upgrade to full multisite later

**Recommendation:** Option B - Simple ECS first, then gradually enable multisite features

### 3.2 Implementation Phases

**Phase 1: Preparation (No Breaking Changes)**
- Add new environment variables
- Create SiteManager class
- Add LEGACY_MODE flag (default: true)
- Update documentation

**Phase 2: Core Integration (Backward Compatible)**
- Update app factory to initialize SiteManager
- Configure Jinja2 ChoiceLoader (engine + site templates)
- Add site static file routes
- Maintain legacy path support

**Phase 3: Module Updates (Site-Aware)**
- Update ConfigManager to use SiteManager
- Update FileManager to use SiteManager
- Update admin routes
- Update public routes
- Update import/export
- Update CLI commands

**Phase 4: Migration Tools**
- Create migration script
- Test migration process
- Document migration steps

**Phase 5: Full Transition**
- Set LEGACY_MODE=false as default
- Update documentation
- Deprecate legacy mode (2-3 releases later)

## 4. Task Breakdown

### ECS-01: Create SiteManager Module ✅

**File:** `app/core/site_manager.py` (NEW - ~250 lines)
**Dependencies:** None
**Effort:** 4 hours
**Risk:** Low

### ECS-02: Update Configuration ✅

**File:** `app/config.py` (MODIFY - add ~15 lines)
**Dependencies:** ECS-01
**Effort:** 2 hours
**Risk:** Low

### ECS-03: Update Application Factory ✅

**File:** `app/__init__.py` (MODIFY - add ~40 lines)
**Dependencies:** ECS-01, ECS-02
**Effort:** 4 hours
**Risk:** Medium

### ECS-04: Update ConfigManager ✅

**File:** `app/core/config_manager.py` (MODIFY - add ~20 lines)
**Dependencies:** ECS-01, ECS-03
**Effort:** 3 hours
**Risk:** Medium

### ECS-05: Update FileManager ✅

**File:** `app/core/file_manager.py` (MODIFY - add parameter to functions)
**Dependencies:** ECS-01, ECS-03
**Effort:** 2 hours
**Risk:** Low

### ECS-06: Update TemplateManager ✅

**File:** `app/core/template_manager.py` (MODIFY - minor changes)
**Dependencies:** ECS-03
**Effort:** 1 hour
**Risk:** Low

### ECS-07: Update Admin Routes ✅

**File:** `app/modules/admin/routes.py` (MODIFY - ~30 changes)
**Dependencies:** ECS-01, ECS-04, ECS-05
**Effort:** 4 hours
**Risk:** Medium

### ECS-08: Update Public Routes ✅

**File:** `app/modules/public/routes.py` (MODIFY - ~6 changes)
**Dependencies:** ECS-01, ECS-04
**Effort:** 2 hours
**Risk:** Low

### ECS-09: Update Import/Export ✅

**Files:**
- `app/modules/import_export/exporter.py` (MODIFY)
- `app/modules/import_export/importer.py` (MODIFY)
- `app/blueprints/import_export.py` (MODIFY)

**Dependencies:** ECS-01
**Effort:** 6 hours
**Risk:** Medium

### ECS-10: Update CLI Commands ✅

**File:** `app/modules/cli/commands.py` (MODIFY - ~25 changes)
**Dependencies:** ECS-01
**Effort:** 4 hours
**Risk:** Medium

### ECS-11: Migration Script ✅

**File:** `scripts/migrate_to_sites.py` (NEW - ~200 lines)
**Dependencies:** All previous ECS tasks
**Effort:** 6 hours
**Risk:** Medium

### ECS-12: Update Environment Variables ✅

**File:** `.env.example` (MODIFY - add section)
**Dependencies:** None
**Effort:** 1 hour
**Risk:** Low

## 5. Implementation Roadmap

### 5.1 Task Dependencies

```
ECS-01 (SiteManager)
  ├─> ECS-02 (Config)
  │     └─> ECS-03 (App Factory)
  │           ├─> ECS-04 (ConfigManager)
  │           ├─> ECS-05 (FileManager)
  │           ├─> ECS-06 (TemplateManager)
  │           ├─> ECS-07 (Admin Routes)
  │           ├─> ECS-08 (Public Routes)
  │           └─> ECS-09 (Import/Export)
  ├─> ECS-10 (CLI Commands)
  └─> ECS-12 (.env.example)

ECS-11 (Migration Script) depends on ALL above

Testing depends on ALL
```

### 5.2 Parallel Execution Strategy

**Agent 1 (Foundation):**
- ECS-01 (SiteManager)
- ECS-02 (Config)
- ECS-12 (.env.example)

**Agent 2 (Core Integration):**
- ECS-03 (App Factory) - after ECS-01, ECS-02
- ECS-04 (ConfigManager) - after ECS-03
- ECS-05 (FileManager) - after ECS-03
- ECS-06 (TemplateManager) - after ECS-03

**Agent 3 (Routes):**
- ECS-07 (Admin Routes) - after ECS-04, ECS-05
- ECS-08 (Public Routes) - after ECS-04

**Agent 4 (Import/Export & CLI):**
- ECS-09 (Import/Export) - after ECS-01
- ECS-10 (CLI Commands) - after ECS-01

**Agent 5 (Migration):**
- ECS-11 (Migration Script) - after ALL above

## 6. Success Criteria

**Must Have:**
- [ ] All existing functionality works in legacy mode
- [ ] All existing functionality works in sites mode
- [ ] Migration script completes without errors
- [ ] No data loss during migration
- [ ] Performance within 5% of baseline
- [ ] Documentation updated

**Should Have:**
- [ ] Automated tests cover 80% of code paths
- [ ] Migration rollback tested successfully
- [ ] Import/export works with both structures
- [ ] CLI commands work with site_manager

## 7. Risk Assessment

| Risk | Impact | Probability | Priority | Status |
|------|--------|-------------|----------|--------|
| Template Loading | High | Medium | P1 | Mitigated |
| File Upload Paths | Medium | Low | P2 | Mitigated |
| Config Loading | High | Low | P1 | Mitigated |
| Migration Data Loss | Critical | Very Low | P0 | Mitigated |
| Import/Export | Medium | Medium | P2 | Accepted |
| Cache Invalidation | Low | Low | P3 | Accepted |
| Plugin Compatibility | Medium | Medium | P2 | Documented |

## 8. Testing Strategy

### 8.1 Manual Testing Checklist

**Legacy Mode Testing (LEGACY_MODE=true)**
- [ ] Start application
- [ ] Login to admin
- [ ] View dashboard
- [ ] Edit a page
- [ ] Upload an image
- [ ] Save page changes
- [ ] View public page
- [ ] Change settings
- [ ] Run CLI commands
- [ ] Export/Import site

**Sites Mode Testing (LEGACY_MODE=false)**
- [ ] Start application
- [ ] Login to admin
- [ ] All admin functions work
- [ ] File uploads go to sites/default/
- [ ] Templates load from sites/default/
- [ ] Static files serve correctly
- [ ] CLI commands work
- [ ] Export/Import work

**Migration Testing**
- [ ] Run migration script
- [ ] Verify all files moved correctly
- [ ] No data loss
- [ ] Application works after migration
- [ ] Rollback works (LEGACY_MODE=true)

## 9. Migration Guide

### For Existing Installations

1. **Backup** current installation
2. **Update** code with ECS
3. **Update** .env file (add SITES_DIR, DEFAULT_SITE, LEGACY_MODE=true)
4. **Test** in legacy mode
5. **Run** migration script: `python run.py migrate`
6. **Test** in sites mode (LEGACY_MODE=false)
7. **Cleanup** old files (optional)

### For New Installations

1. Clone and install
2. Configure .env (LEGACY_MODE=false by default)
3. Run application (sites/default/ created automatically)
4. Access and configure

### Rollback Procedure

Set `LEGACY_MODE=true` in .env and restart application.

---

**Document Version:** 1.0
**Last Updated:** 2026-02-07
**Status:** Ready for Implementation
