# Wicara - Editable Static Web CMS

A lightweight, flat-file CMS built with Flask that allows you to create editable static websites without a database. Perfect for profile websites, landing pages, and simple business websites.

**Current Status**: Production Ready (v1.0.0) | 90% Complete with Advanced Features

## Features

- **Zero Database**: All content stored in a single `config.json` file
- **Simple Admin Panel**: Easy-to-use interface for content editing
- **Template-Based**: Use HTML templates with dynamic content injection
- **Image Upload**: Support for image uploads with validation
- **Secure**: Password-protected admin area with session management
- **Portable**: Easy backup and migration with export/import system
- **Lightweight**: Minimal dependencies with excellent performance
- **Advanced Caching**: Multi-layer caching system (config, templates, HTTP responses) - 50-80% performance improvement
- **Import/Export System**: Complete backup, migration, and conflict resolution capabilities
- **Modular Architecture**: Clean separation of concerns with blueprints and modules
- **CLI Commands**: Command-line interface for automation and batch operations

## Quick Start

### Prerequisites

- Python 3.8+
- pip package manager
- Optional: Redis for distributed caching (advanced feature)

### Installation

1. **Clone or download the project**
   ```bash
   git clone <repository-url>
   cd wicara
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create environment configuration (optional)**
   ```bash
   cp .env.example .env
   # Edit .env to customize settings (port, cache backend, log level, etc.)
   ```

4. **Run the application**
   ```bash
   # Using the modern entry point (recommended)
   python run.py

   # Or using Flask directly
   python -m flask run
   ```

5. **Access the website**
   - Public site: http://localhost:5555
   - Admin panel: http://localhost:5555/admin
   - Default admin password: `admin123`

### Change Admin Password

After first login, change the admin password by editing `config.json`:

```bash
python -c "
from werkzeug.security import generate_password_hash
import json
with open('config.json', 'r') as f: config = json.load(f)
config['admin-password'] = generate_password_hash('your-new-password', method='scrypt')
with open('config.json', 'w') as f: json.dump(config, f, indent=2)
"
```

## Project Structure

```
wicara/
├── app/                              # Main application package (modular architecture)
│   ├── __init__.py                   # Application factory (create_app)
│   ├── config.py                     # Environment-based configuration
│   ├── errors.py                     # Error handlers (404, 500, 413)
│   ├── logger.py                     # Logging configuration with rotation
│   ├── utils.py                      # Utility functions
│   │
│   ├── modules/                      # Feature modules with blueprints
│   │   ├── auth/                     # Authentication (login/logout)
│   │   ├── admin/                    # Admin panel (dashboard, settings, cache management)
│   │   ├── public/                   # Public-facing pages
│   │   ├── import_export/            # Import/Export system (MIG-01 to MIG-05)
│   │   └── cli/                      # Command-line interface
│   │
│   ├── core/                         # Core functionality
│   │   ├── config_manager.py         # Configuration loading/saving
│   │   ├── file_manager.py           # File operations and uploads
│   │   ├── template_manager.py       # Template rendering and conversion
│   │   └── validators.py             # Input and schema validation
│   │
│   └── cache/                        # Caching system (PERF-01 to PERF-05)
│       ├── manager.py                # Cache manager abstraction
│       ├── backends.py               # Cache implementations (Memory, File, Redis)
│       ├── config_cache.py           # Configuration caching
│       ├── template_cache.py         # Template caching
│       ├── response_cache.py         # HTTP response caching
│       └── utils.py                  # Cache utilities and factories
│
├── docs/                             # Documentation
│   ├── DEVELOPER_GUIDE.md
│   ├── SETUP_GUIDE.md
│   ├── USER_GUIDE.md
│   ├── CACHING.md                    # Caching system documentation
│   ├── IMPORT_EXPORT_IMPLEMENTATION.md  # Import/Export feature docs
│   └── *.md                          # Other guides
│
├── templates/                        # Jinja2 HTML templates
│   ├── base.html                     # Public base template
│   ├── home.html, about.html, etc.   # Public pages
│   ├── 404.html, 500.html            # Public error pages
│   └── admin/                        # Admin panel templates
│       ├── base.html
│       ├── login.html
│       ├── dashboard.html
│       ├── edit_page.html
│       ├── settings.html
│       ├── cache_dashboard.html
│       ├── import_export/            # Import/Export wizard templates
│       └── *.html                    # Other admin pages
│
├── static/                           # Static assets
│   ├── css/
│   │   ├── style.css                 # Public website styles
│   │   └── admin.css                 # Admin panel styles
│   ├── js/
│   │   └── admin.js                  # Admin panel scripts
│   └── images/
│       └── uploads/                  # User uploaded images
│
├── run.py                            # Modern entry point (recommended)
├── app.py                            # Legacy monolithic file (for reference only)
├── config.json                       # Website configuration and content database
├── config.json.backup                # Automatic backup
├── requirements.txt                  # Python dependencies
├── .env.example                      # Environment variables template
├── README.md                         # This file
├── CLAUDE.md                         # Developer guidance for Claude Code
├── BACKLOG.md                        # Development roadmap
└── LICENSE                           # MIT License
```

**Note**: The legacy `app.py` file is kept for reference only. The application now uses a modular structure with `run.py` as the main entry point.

## Configuration

### Website Structure

Edit `config.json` to configure your website:

```json
{
  "admin-password": "hashed-password",
  "sitename": "My Website",
  "description": "Website description",
  "keywords": ["keyword1", "keyword2"],
  "pages": [
    {
      "title": "Page Title",
      "template": "template-file.html",
      "menu-title": "Menu Label",
      "url": "/page-url",
      "seo-description": "SEO description",
      "seo-keywords": ["seo", "keywords"],
      "fields": [
        {
          "name": "field-name",
          "type": "text|textarea|image",
          "label": "Field Label",
          "value": "Default content"
        }
      ]
    }
  ],
  "footer": {
    "content": ["Footer line 1", "Footer line 2"]
  }
}
```

### Field Types

- **text**: Single line input
- **textarea**: Multi-line text input
- **image**: File upload with preview

### Template Syntax

**Important Note**: Config.json uses hyphens for readability, but templates use underscores (Jinja2 requirement):

```json
// config.json (hyphens)
{"hero-title": "Welcome", "seo-description": "My site"}
```

```html
<!-- templates (underscores) -->
<h1>{{hero_title}}</h1>
<p>{{seo_description}}</p>
<img src="{{hero_image}}" alt="Hero">
```

**Automatic Conversion**: The system automatically converts hyphens to underscores, so:
- `hero-title` → `{{hero_title}}`
- `seo-description` → `{{seo_description}}`
- `menu-title` → `{{menu_title}}`

Global variables available in all templates:
- `{{sitename}}`: Website name
- `{{description}}`: Website description
- `{{keywords}}`: Website keywords array
- `{{footer}}`: Footer content array
- `{{pages}}`: All pages array (for navigation)

## Adding New Pages

1. **Create HTML template** in `templates/` folder
2. **Add page configuration** to `config.json`:
   ```json
   {
     "title": "New Page - My Website",
     "template": "newpage.html",
     "menu-title": "New Page",
     "url": "/newpage",
     "fields": [
       {
         "name": "page-content",
         "type": "textarea",
         "label": "Page Content",
         "value": "Default content here"
       }
     ]
   }
   ```
3. **Access the page** at `/newpage` and edit via admin panel

## Deployment

### Production Setup

1. **Create production environment file**:
   ```bash
   cp .env.example .env
   # Edit .env with production settings:
   FLASK_ENV=production
   SECRET_KEY=your-secret-key-here
   HOST=0.0.0.0
   PORT=5555
   LOG_LEVEL=INFO
   CACHE_BACKEND=file  # or redis for distributed caching
   ```

2. **Install production server**:
   ```bash
   pip install gunicorn
   ```

3. **Run with Gunicorn**:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5555 "app:create_app()" --timeout 60
   ```

4. **Configure web server** (Apache/Nginx) to reverse proxy:
   ```nginx
   # Nginx example
   location / {
       proxy_pass http://127.0.0.1:5555;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
   }
   ```

5. **Advanced Caching (Optional)**:
   - For distributed caching across multiple servers, configure Redis:
     ```bash
     CACHE_BACKEND=redis
     REDIS_URL=redis://localhost:6379/0
     ```

### File Permissions

Ensure the application has write permissions to:
- `config.json`
- `static/images/uploads/`

## Security Considerations

- Change default admin password immediately
- Use strong SECRET_KEY in production
- Keep Flask and dependencies updated
- Restrict file upload permissions
- Use HTTPS in production

## Advanced Features

### Caching System (Phase 2)

Wicara includes a sophisticated multi-layer caching system providing 50-80% performance improvements:

- **Configuration Caching**: Caches parsed `config.json` with automatic invalidation
- **Template Caching**: Fragment-level and full page caching with dependency tracking
- **Response Caching**: HTTP response caching with ETags and conditional requests
- **Cache Backends**: Memory, File, or Redis backends (configured via environment)
- **Admin Dashboard**: Cache statistics and management at `/admin/cache/`

Enable caching with environment variables:
```bash
CACHE_BACKEND=memory          # memory, file, or redis
CONFIG_CACHE_TTL=300          # 5 minutes (config cache)
TEMPLATE_CACHE_TTL=3600       # 1 hour (template cache)
RESPONSE_CACHE_TTL=3600       # 1 hour (response cache)
```

See [CACHING.md](docs/CACHING.md) for detailed documentation.

### Import/Export System (Phase 3)

Complete backup, migration, and conflict resolution capabilities:

- **Export**: Create ZIP backups with multiple modes (full, partial, content-only)
- **Import**: Import from ZIP files with conflict resolution strategies
- **Migration**: Automatic schema validation and version compatibility checking
- **Rollback**: Automatic backup before import for safe rollback
- **Admin Interface**: Multi-step import/export wizards at `/admin/import-export/`

Access via admin panel: **Admin Dashboard → Import/Export** or directly at `/admin/import-export/`

See [IMPORT_EXPORT_IMPLEMENTATION.md](docs/IMPORT_EXPORT_IMPLEMENTATION.md) for detailed documentation.

### CLI Commands

Automate tasks via command-line:

```bash
# Create new page
python run.py create-page "Page Title" "template.html" "/url" "Menu Label"

# List all pages
python run.py list-pages

# Delete a page
python run.py delete-page "/url"

# Show help
python run.py help
```

## Backup and Migration

### Backup Methods

**Option 1: Using Admin Export** (Recommended)
1. Go to Admin Dashboard → **Import/Export → Export**
2. Choose export mode (Full, Partial, or Content-only)
3. Download the ZIP file

**Option 2: Manual Backup**
Simply copy:
- `config.json` (contains all content)
- `static/images/uploads/` (uploaded images)

### Migration

**Using Import/Export System** (Recommended - Safe & Reversible)
1. On source system: Admin → Import/Export → Export → Download ZIP
2. On target system: Admin → Import/Export → Import → Upload ZIP
3. System automatically creates backup before import

**Manual Migration**
1. Copy all files to new server
2. Install dependencies: `pip install -r requirements.txt`
3. Set file permissions
4. Run the application: `python run.py`

## Troubleshooting

### Common Issues

1. **Permission Denied**: Check file permissions for `config.json` and upload directory
2. **Template Not Found**: Ensure template files exist in `templates/` folder
3. **Images Not Loading**: Check image paths and ensure files exist in `static/images/uploads/`

### Logs

Check Flask logs for error details. Enable debug mode during development:
```python
app.run(debug=True)
```

## Architecture Overview

Wicara has a modern, modular architecture:

- **Application Factory Pattern**: Clean initialization via `create_app()` in `app/__init__.py`
- **Blueprint Organization**: Routes organized into logical modules (auth, admin, public, import_export)
- **Feature Modules**: Self-contained feature packages with routes, logic, and forms
- **Core Services**: Shared functionality (config, files, templates, validation)
- **Pluggable Cache System**: Multiple backends with consistent interface
- **Error Handling**: Centralized error handlers with proper logging

For detailed architecture documentation, see [CLAUDE.md](CLAUDE.md) and [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md).

## Development

### Adding Features

The modular structure makes it easy to add new features:

1. **For new routes**: Create or modify modules in `app/modules/`
2. **For core logic**: Add to appropriate service in `app/core/`
3. **For UI**: Create templates in `templates/` and styles in `static/css/`
4. **For caching logic**: Extend cache system in `app/cache/`

### Code Organization

- **app/modules/**: Self-contained feature modules with routes and logic
- **app/core/**: Shared services used across modules
- **app/cache/**: Pluggable caching system with multiple backends
- **templates/**: Jinja2 templates organized by section (public, admin)
- **static/**: CSS, JavaScript, and uploaded images

### Running Tests

Development testing utilities are available:
```bash
# Test caching system
python test_cache.py
```

### Contributing

1. Keep changes focused on a specific feature
2. Follow the modular architecture patterns
3. Update relevant documentation
4. Test thoroughly across different configurations
5. Ensure backward compatibility with config.json

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check this README
2. Review the code comments
3. Test with the default configuration
4. Create an issue with detailed information

---

**Wicara**: Static Speed, Dynamic Content - No Database Required
