# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Wicara is a sophisticated, flat-file CMS built with Flask that allows creating editable static websites without a database. All content is stored in a single `config.json` file, making it portable and easy to backup.

**Status**: Production Ready (v1.0.0) | 90% Complete

The application has undergone significant architectural evolution across three implementation phases:
- **Phase 1**: Modular Architecture (ARC-01 to ARC-04) - Transitioned from monolithic to modular structure
- **Phase 2**: Caching Strategy (PERF-01 to PERF-05) - Multi-layer caching providing 50-80% performance improvements
- **Phase 3**: Import/Export System (MIG-01 to MIG-05) - Complete backup, migration, and conflict resolution

## Development Commands

### Running the Application

```bash
# Recommended: Using modern entry point with environment support
python run.py

# Alternative: Using Flask CLI
python -m flask run

# Legacy (for reference):
python app.py
```

The application runs on **port 5555** by default.

### Installing Dependencies

```bash
pip install -r requirements.txt
```

### Environment Configuration

Create a `.env` file (copy from `.env.example`):
```bash
FLASK_ENV=development
SECRET_KEY=dev-key-change-in-production
HOST=localhost
PORT=5555
LOG_LEVEL=INFO
CACHE_BACKEND=memory
```

**Environment Variables**:
- `FLASK_ENV`: Development or production
- `SECRET_KEY`: Session encryption key (change in production!)
- `HOST`: Bind address (default: localhost)
- `PORT`: Server port (default: 5555)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `CACHE_BACKEND`: memory, file, or redis
- `REDIS_URL`: Redis connection string (if using Redis cache)
- `CONFIG_CACHE_TTL`: Config cache TTL in seconds (default: 300)
- `TEMPLATE_CACHE_TTL`: Template cache TTL in seconds (default: 3600)
- `RESPONSE_CACHE_TTL`: Response cache TTL in seconds (default: 3600)

### Changing Admin Password

```bash
python -c "
from werkzeug.security import generate_password_hash
import json
with open('config.json', 'r') as f: config = json.load(f)
config['admin-password'] = generate_password_hash('your-new-password', method='scrypt')
with open('config.json', 'w') as f: json.dump(config, f, indent=2)
"
```

## Architecture

### Modern Modular Structure

The application is organized using Flask's **Application Factory Pattern** and **Blueprints**:

```
app/                           # Main application package
├── __init__.py                # Application factory (create_app())
├── config.py                  # Environment-based configuration
├── errors.py                  # Error handlers
├── logger.py                  # Logging configuration
├── utils.py                   # Utility functions
│
├── modules/                   # Feature modules with blueprints
│   ├── auth/                  # Authentication (login/logout)
│   │   ├── routes.py
│   │   └── utils.py
│   ├── admin/                 # Admin panel functionality
│   │   ├── routes.py
│   │   ├── cache_routes.py
│   │   └── forms.py
│   ├── public/                # Public-facing pages
│   │   ├── routes.py
│   │   └── utils.py
│   ├── import_export/         # Import/Export system
│   │   ├── exporter.py        # (MIG-01, MIG-02)
│   │   ├── importer.py        # (MIG-03)
│   │   └── migrator.py        # (MIG-04)
│   └── cli/                   # Command-line interface
│       └── commands.py
│
├── core/                      # Core functionality
│   ├── config_manager.py      # Configuration CRUD
│   ├── file_manager.py        # File operations & uploads
│   ├── template_manager.py    # Template rendering
│   └── validators.py          # Input validation
│
└── cache/                     # Caching system (PERF-01 to PERF-05)
    ├── manager.py             # Cache manager abstraction
    ├── backends.py            # MemoryCache, FileCache, RedisCache
    ├── config_cache.py        # Config caching (PERF-02)
    ├── template_cache.py      # Template caching (PERF-03)
    ├── response_cache.py      # Response caching (PERF-04)
    └── utils.py               # Factories and utilities
```

### Key Design Patterns

1. **Application Factory Pattern** (`app/__init__.py`)
   - `create_app(config=None)` function initializes Flask app
   - Enables clean initialization and testing
   - Supports multiple configurations (dev, prod, test)

2. **Blueprint Organization** (`app/modules/`)
   - Routes grouped by feature
   - Each module is self-contained with routes, forms, logic
   - Easy to enable/disable features or add new ones

3. **Core Services** (`app/core/`)
   - Shared business logic used across modules
   - ConfigManager, FileManager, TemplateManager, Validators
   - Dependency injection into routes

4. **Pluggable Cache System** (`app/cache/`)
   - Multiple backend implementations (Memory, File, Redis)
   - Unified interface via CacheManager
   - Five-layer caching strategy (config, template, response, etc.)

### Component Overview

#### Application Entry Point (`run.py`)
- Modern entry point with environment variable support
- Loads .env file for configuration
- Calls `create_app()` from `app/__init__.py`
- Replaces legacy `app.py` (kept for reference)

#### Application Factory (`app/__init__.py`)
```python
def create_app(config=None):
    # Initialize Flask app with blueprints
    # Register error handlers
    # Initialize cache system
    # Create necessary directories
```

#### Core Modules

**ConfigManager** (`app/core/config_manager.py`)
- Load/save config.json with validation
- Automatic backup creation
- File modification time tracking for cache invalidation
- Schema validation with detailed error messages

**FileManager** (`app/core/file_manager.py`)
- Image upload with security validation
  - Magic number verification (not just file extensions)
  - 5MB file size limit
  - Secure filename sanitization with UUIDs
  - Supported formats: JPG, PNG, GIF, WebP
- Delete images from filesystem
- Cleanup unused image references
- Create configuration backups
- Directory initialization

**TemplateManager** (`app/core/template_manager.py`)
- Render Jinja2 templates with context
- Convert hyphenated keys to underscores (config uses hyphens, templates use underscores)
  - Example: `"hero-title"` in config → `{{hero_title}}` in templates
- Prepare template context with global variables
- Error handling for missing templates

**Validators** (`app/core/validators.py`)
- Field validation: text (255 chars), textarea (5000 chars)
- Image file validation with magic number checking
- Configuration schema validation
- Page schema validation
- Field schema validation

#### Cache System (Phase 2 - PERF-01 to PERF-05)

**PERF-01: CacheManager** (`app/cache/manager.py`)
- Unified abstraction layer for multiple cache backends
- Comprehensive statistics tracking (hits, misses, errors)
- Health monitoring and error recovery
- Thread-safe operations

**PERF-02: ConfigCache** (`app/cache/config_cache.py`)
- Caches parsed config.json in memory
- Automatic invalidation on file modification (mtime detection)
- Default TTL: 5 minutes
- Reduces JSON parsing overhead by 95%

**PERF-03: TemplateCache** (`app/cache/template_cache.py`)
- Fragment-level template caching
- Full page caching for static content
- Context-aware cache keys
- Dependency tracking for selective invalidation
- Cache warming support

**PERF-04: ResponseCache** (`app/cache/response_cache.py`)
- HTTP response caching with proper headers
- ETag generation and validation
- Conditional request handling (304 Not Modified)
- Browser cache optimization
- CDN integration support

**PERF-05: Admin Interface** (`app/modules/admin/cache_routes.py`)
- Cache dashboard at `/admin/cache/`
- Real-time statistics display
- Manual cache clearing by type
- API endpoints for monitoring

**Backend Implementations** (`app/cache/backends.py`)
- `MemoryCache`: Fastest, default for development (single process)
- `FileCache`: Persistent, suitable for development/small deployments
- `RedisCache`: Distributed caching for production clusters

Configure via environment:
```bash
CACHE_BACKEND=memory              # memory, file, redis
CACHE_DIR=.cache                  # For file cache
REDIS_URL=redis://localhost:6379  # For Redis cache
```

#### Import/Export System (Phase 3 - MIG-01 to MIG-05)

**MIG-01: Exporter** (`app/modules/import_export/exporter.py`)
- Creates ZIP packages with three modes:
  - `EXPORT_FULL`: Complete site (config, templates, static, images)
  - `EXPORT_PARTIAL`: Config and custom templates only
  - `EXPORT_CONTENT`: Config.json only
- Progress tracking and statistics
- Package validation with checksums

**MIG-02: Export Format**
- ZIP structure with manifest.json containing:
  - Metadata (version, timestamp, statistics)
  - SHA256 checksum for integrity verification
  - Schema version information
- Filename: `wicara_export_YYYYMMDD_HHMMSS.zip`

**MIG-03: Importer** (`app/modules/import_export/importer.py`)
- ZIP validation and security checks
- Automatic backup creation before import
- Conflict resolution with three strategies:
  - `STRATEGY_MERGE`: Keep existing, add new (default)
  - `STRATEGY_REPLACE`: Overwrite everything
  - `STRATEGY_SKIP`: Skip conflicting items
- Selective import (templates, images optional)
- Rollback capability on failure

**MIG-04: Migrator** (`app/modules/import_export/migrator.py`)
- Version compatibility checking
- Schema validation against current structure
- Field type transformation support
- Migration planning and data validation
- Baseline version: 1.0.0

**MIG-05: Admin Interface** (`app/blueprints/import_export.py`)
- Multi-step export wizard: `/admin/import-export/export`
- Multi-step import wizard: `/admin/import-export/import`
- Preview & confirmation: `/admin/import-export/import/preview`
- Progress tracking and validation APIs
- Three template files for wizard steps

### Configuration System

**config.json Structure**:
```json
{
  "admin-password": "hashed-scrypt-password",
  "sitename": "Website Name",
  "description": "Website description",
  "keywords": ["keyword1", "keyword2"],
  "pages": [
    {
      "title": "Page Title",
      "template": "template.html",
      "url": "/page-url",
      "menu-title": "Menu Label",
      "seo-description": "SEO description",
      "seo-keywords": ["seo", "keywords"],
      "fields": [
        {
          "name": "field-name",
          "type": "text|textarea|image",
          "label": "Field Label",
          "value": "field-value"
        }
      ]
    }
  ],
  "footer": {
    "content": ["Footer line 1", "Footer line 2"]
  }
}
```

**Field Types**:
- `text`: Single-line input (255 character limit)
- `textarea`: Multi-line input (5000 character limit)
- `image`: File upload with preview (5MB limit, magic number validation)

### Routes & API Endpoints

#### Public Routes (`app/modules/public/routes.py`)
- `GET /`: Home page
- `GET /<path:url>`: Dynamic page handler
- All pages support response caching with ETags

#### Authentication Routes (`app/modules/auth/routes.py`)
- `GET/POST /admin/login`: Admin login form
- `GET /admin/logout`: Admin logout

#### Admin Routes (`app/modules/admin/routes.py`)
- `GET /admin/`: Dashboard (page listing)
- `GET/POST /admin/edit/<page_index>`: Page content editor
- `GET /admin/settings`: Global site settings
- `POST /admin/settings`: Save settings
- `GET /admin/change-password`: Password change form
- `POST /admin/change-password`: Update password
- `GET /admin/cleanup`: Cleanup unused images

#### Cache Routes (`app/modules/admin/cache_routes.py`)
- `GET /admin/cache/`: Cache dashboard
- `GET /admin/cache/api/stats`: Cache statistics (JSON API)
- `POST /admin/cache/clear`: Clear specific cache
- `POST /admin/cache/warm`: Warm cache
- `POST /admin/cache/reset-stats`: Reset statistics

#### Import/Export Routes (`app/blueprints/import_export.py`)
- `GET/POST /admin/import-export/export`: Export wizard
- `GET /admin/import-export/download`: Download export file
- `GET/POST /admin/import-export/import`: Import wizard
- `GET /admin/import-export/import/preview`: Preview import
- `POST /admin/import-export/import/confirm`: Execute import
- `GET /admin/import-export/api/export-progress`: Progress tracking
- `POST /admin/import-export/api/validate-package`: Validate ZIP

#### CLI Commands (`app/modules/cli/commands.py`)
```bash
python run.py create-page <title> <template> <url> [menu-title]
python run.py list-pages
python run.py delete-page <url>
python run.py help
```

### Template System

#### Hyphen-to-Underscore Conversion

Important: Config.json uses hyphens for readability, templates use underscores (Jinja2 requirement).

```json
// config.json (hyphens)
{
  "hero-title": "Welcome",
  "menu-title": "Home",
  "seo-description": "My website"
}
```

```html
<!-- templates (underscores) -->
<h1>{{hero_title}}</h1>
<nav><a>{{menu_title}}</a></nav>
<meta name="description" content="{{seo_description}}">
```

Automatic conversion is handled by `TemplateManager.convert_keys_to_underscore()`.

#### Available Global Variables in All Templates

- `{{sitename}}`: Website name
- `{{description}}`: Website description
- `{{keywords}}`: Website keywords array
- `{{footer}}`: Footer content array
- `{{pages}}`: All pages array (for navigation)
- `{{current_page}}`: Current page object (on page routes)

#### Template Organization

```
templates/
├── base.html                    # Public base template with macros
├── home.html
├── about.html
├── contact.html
├── features.html
├── documentation.html
├── use-cases.html
├── 404.html                     # Public error pages
├── 500.html
└── admin/
    ├── base.html                # Admin base template
    ├── login.html
    ├── dashboard.html
    ├── edit_page.html
    ├── settings.html
    ├── change_password.html
    ├── cache_dashboard.html
    ├── import_export/
    │   ├── export.html
    │   ├── import.html
    │   └── import_preview.html
    ├── 404.html                 # Admin error pages
    └── 500.html
```

## Security Features

1. **Password Hashing**: Werkzeug scrypt method
2. **Session Management**: 1-hour session lifetime, secure cookies (HTTPONLY, SAMESITE=Lax)
3. **File Upload Validation**:
   - Magic number verification (checks actual file content, not just extension)
   - 5MB size limit
   - Secure filename sanitization with UUID-based naming
   - Supported formats: JPG, PNG, GIF, WebP
4. **CSRF Protection**: Flask session-based CSRF tokens
5. **Input Validation**: Length limits and HTML sanitization
6. **Error Handling**: Detailed logging without exposing sensitive information
7. **Authorization**: `@login_required` decorator for protected routes

## Important Implementation Details

### Template Variable Access

Config.json uses hyphens (e.g., `"hero-title"`) but templates use underscores (e.g., `{{hero_title}}`).

The system automatically converts hyphens to underscores through `TemplateManager.convert_keys_to_underscore()`.

### Field Types and Limits

- **text**: Single-line input, max 255 characters
- **textarea**: Multi-line input, max 5000 characters
- **image**: File upload, max 5MB, magic number validation

### File Structure

Root directory contains:
- `app/` - Main application package (new modular structure)
- `templates/` - Jinja2 templates
- `static/` - CSS, JavaScript, images
- `docs/` - Documentation
- `run.py` - Modern entry point (use this!)
- `app.py` - Legacy monolithic file (for reference only)
- `config.json` - Website configuration and content
- `config.json.backup` - Automatic backup
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variables template

## Testing and Development

### Access Points

- Public site: http://localhost:5555
- Admin panel: http://localhost:5555/admin
- Cache dashboard: http://localhost:5555/admin/cache/
- Import/Export: http://localhost:5555/admin/import-export/
- Default admin password: `admin123`

### Configuration Editing

- **Quick edits**: Use admin panel for content
- **Structural changes**: Edit `config.json` directly, then restart application
- **Caching**: Configure via environment variables or admin dashboard

### Adding New Pages

1. Create HTML template in `templates/`
2. Add page configuration to `config.json` pages array
3. Define fields with types: `text`, `textarea`, or `image`
4. Access via defined URL, edit through admin panel at `/admin/edit/<index>`

### Testing Caching System

```bash
python test_cache.py
```

## Recent Implementation Phases

### Phase 1: Modular Architecture (ARC-01 to ARC-04)
- **Commit**: 679cf7d (initial refactor)
- **Components**:
  - ARC-01: Application Factory Pattern
  - ARC-02: Core Modules (config, file, template, validators)
  - ARC-03: Route Organization (blueprints & modules)
  - ARC-04: Environment-based configuration
- **Impact**: Transitioned from monolithic to modular structure

### Phase 2: Caching Strategy (PERF-01 to PERF-05)
- **Commit**: 4429b6e
- **Components**: Multi-layer caching system
- **Impact**: 50-80% performance improvement, real-time cache dashboard

### Phase 3: Import/Export System (MIG-01 to MIG-05)
- **Commit**: 675bead
- **Components**: Complete backup/migration system with conflict resolution
- **Impact**: Safe backups, migrations, and rollback capability

## Documentation

- **README.md**: User-facing documentation, quick start, deployment
- **CLAUDE.md**: This file - Developer guidance
- **docs/DEVELOPER_GUIDE.md**: Comprehensive development guide
- **docs/CACHING.md**: Detailed caching system documentation
- **docs/IMPORT_EXPORT_IMPLEMENTATION.md**: Import/Export feature documentation
- **docs/SETUP_GUIDE.md**: Setup and installation guide
- **docs/USER_GUIDE.md**: End-user documentation
- **BACKLOG.md**: Development roadmap and remaining tasks

## Deployment Considerations

- Use `run.py` as the entry point (not `app.py`)
- Configure environment variables via `.env` file
- Enable appropriate cache backend (memory for dev, file/redis for production)
- Set `SECRET_KEY` to a strong value in production
- Use HTTPS in production
- Ensure write permissions for `config.json` and `static/images/uploads/`
- Consider Redis for distributed caching across multiple servers

## Redundancy Notes

The legacy `app.py` file (926 lines) contains all functionality in a single file. The new modular structure distributes this functionality across specialized modules:

- Error handlers → `app/errors.py`
- Config utilities → `app/core/config_manager.py`
- File operations → `app/core/file_manager.py`
- Template functions → `app/core/template_manager.py`
- Validation logic → `app/core/validators.py`
- Routes → `app/modules/` and `app/blueprints/`

The `app.py` file is kept for reference only. **Always use the modular structure** in `app/` for new development.
