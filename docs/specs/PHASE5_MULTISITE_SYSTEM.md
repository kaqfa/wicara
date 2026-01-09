# Phase 5: Multi-site Support Implementation Guide

**Status**: 40% Complete (Core Foundation Done, Admin UI and Advanced Features Pending)

---

## Overview

Multi-site support transforms Wicara into an enterprise-grade CMS, enabling hosting of multiple independent websites from a single application instance.

### Key Benefits
- ✅ Host multiple sites with single installation
- ✅ Reduced infrastructure costs
- ✅ Centralized management
- ✅ Per-site security isolation
- ✅ Per-site configuration and content
- ✅ Domain-based routing
- ✅ Easy site cloning and templates

---

## Architecture

### Core Components

#### 1. **SiteManager** (`app/multisite/manager.py`)
Central management of all sites:

```python
from app.multisite import init_multisite

# Initialize in app factory
manager = init_multisite(app, sites_dir='sites/')

# Create site
manager.create_site('my-site', template_site='default')

# Manage domains
manager.add_domain('my-site', 'my-site.com')
manager.remove_domain('my-site', 'old-domain.com')

# Site operations
manager.enable_site('my-site')
manager.disable_site('my-site')

# Get info
site = manager.get_site('my-site')
all_sites = manager.get_all_sites()
```

#### 2. **SiteRouter** (`app/multisite/router.py`)
Routes requests to correct site:

```python
from app.multisite import SiteRouter

router = SiteRouter()
router.init_app(app, site_manager)

# Automatically routes based on domain
# Stores site_id in Flask g object
# Available in routes via: from flask import g; g.site_id
```

#### 3. **SiteContext** (`app/multisite/context.py`)
Provides site-aware API:

```python
from app.multisite import get_site_context

context = get_site_context()

# Get current site
config = context.get_config()
templates_dir = context.get_templates_dir()
uploads_dir = context.get_uploads_dir()

# Save site config
context.save_config(new_config)

# Access other sites
other_config = context.get_config('other-site')
```

#### 4. **SiteIsolation** (`app/multisite/security.py`)
Enforces security boundaries:

```python
from app.multisite import SiteIsolation

isolation = SiteIsolation(site_manager)

# Validate file paths (prevent directory traversal)
isolation.validate_path('/uploads/image.jpg', '/sites/mysite/uploads')

# Enforce isolation
isolation.enforce_site_isolation(app)

# Use decorators for protection
from app.multisite.security import SiteDecorators

@SiteDecorators.require_site('my-site')
def admin_panel():
    pass
```

---

## Directory Structure

```
sites/
    default/                          # Default/main site
        config.json                   # Site configuration
        config.json.backup
        templates/
            base.html
            home.html
            ...
        uploads/
            image-1.jpg
            image-2.jpg
            ...

    company-site/
        config.json
        templates/
            base.html
            ...
        uploads/

    blog-site/
        config.json
        templates/
            base.html
            ...
        uploads/

    .sites.json                       # Sites registry (metadata)
```

### Site Registry (.sites.json)

```json
{
  "default": {
    "id": "default",
    "name": "Main Website",
    "created_at": "2025-12-26T10:00:00",
    "enabled": true,
    "domains": ["example.com", "www.example.com"],
    "config": "sites/default/config.json"
  },
  "company-site": {
    "id": "company-site",
    "name": "Company Website",
    "created_at": "2025-12-26T11:00:00",
    "enabled": true,
    "domains": ["company.com", "www.company.com"],
    "config": "sites/company-site/config.json"
  }
}
```

---

## Using Multi-site System

### Initialization

```python
from flask import Flask
from app import create_app
from app.multisite import init_multisite

def create_app():
    app = Flask(__name__)

    # Initialize multi-site
    site_manager = init_multisite(app, sites_dir='sites/')

    # Initialize routing
    from app.multisite.router import SiteRouter
    router = SiteRouter()
    router.init_app(app, site_manager)

    # Enforce isolation
    from app.multisite.security import create_site_isolation_middleware
    isolation = create_site_isolation_middleware(site_manager)
    isolation.enforce_site_isolation(app)

    return app
```

### Accessing Site Data in Routes

```python
from flask import g
from app.multisite import get_site_context

@app.route('/')
def home():
    # Get current site
    site_id = g.site_id

    # Get site context
    context = get_site_context()
    config = context.get_config()  # Current site's config

    # Access site-specific templates
    templates_dir = context.get_templates_dir()

    return render_template('home.html', site_name=config['sitename'])
```

### Site Management

```python
site_manager = get_site_manager()

# Create new site
site_manager.create_site(
    'new-site',
    template_site='default'  # Clone from default
)

# Add domain
site_manager.add_domain('new-site', 'new-site.com')

# Enable/disable
site_manager.enable_site('new-site')
site_manager.disable_site('old-site')

# Get statistics
stats = site_manager.get_stats()
print(f"Total sites: {stats['total_sites']}")
print(f"Total domains: {stats['total_domains']}")
```

---

## Domain Routing

### Basic Domain Mapping

```python
# In .sites.json or via API
# example.com -> default site
# company.com -> company-site
# blog.com -> blog-site

# Router automatically routes based on domain in Host header
```

### Subdomain Routing

```python
from app.multisite.router import SubdomainRouter

# Map subdomains to sites
domain_map = {
    'example.com': {
        'site1': 'site-1',      # site1.example.com -> site-1
        'site2': 'site-2',      # site2.example.com -> site-2
        'blog': 'blog-site'     # blog.example.com -> blog-site
    }
}

router = SubdomainRouter(domain_map)
router.init_app(app, site_manager)
```

---

## Per-Site Configuration

Each site has independent `config.json`:

```json
{
  "admin-password": "hashed-password",
  "sitename": "My Company",
  "description": "Company website",
  "keywords": ["company", "business"],
  "pages": [
    {
      "title": "Home",
      "template": "home.html",
      "url": "/",
      "fields": []
    }
  ]
}
```

### Modifying Site Configuration

```python
context = get_site_context()

# Load config
config = context.get_config('my-site')

# Modify
config['sitename'] = 'New Name'

# Save (automatically creates backup)
context.save_config(config, 'my-site')
```

---

## Security & Isolation

### Session Isolation

Sessions are automatically isolated per site:

```python
# Session automatically tagged with site_id
# Switching sites clears sensitive data
# Prevents cross-site session attacks
```

### File Path Validation

```python
isolation = SiteIsolation(site_manager)

# Validate paths to prevent directory traversal
if not isolation.validate_path(user_path, allowed_dir):
    return error("Invalid path")
```

### Protected Routes

```python
from app.multisite.security import SiteDecorators

# Require admin access
@app.route('/admin')
@SiteDecorators.require_admin()
def admin_panel():
    pass

# Require specific site
@app.route('/api/site-data')
@SiteDecorators.require_site('main-site')
def get_site_data():
    pass
```

---

## Integration with Existing Systems

### With Caching System

```python
# Each site has isolated cache
from app.cache import get_cache_manager

cache = get_cache_manager()

# Cache key includes site_id automatically
site_id = g.site_id
cache_key = f"{site_id}:config"
```

### With Import/Export

```python
# Import/export per site
from app.modules.import_export import Exporter

exporter = Exporter()

# Export specific site
export_path = exporter.export(
    'my-site',
    mode='EXPORT_FULL'
)
```

### With Plugin System

```python
# Plugins can hook into site lifecycle
class SiteAwarePlugin(BasePlugin):
    def get_hooks(self):
        return {
            'after_config_load': self.on_config_loaded
        }

    def on_config_loaded(self, config):
        # Access current site
        site_id = g.site_id
        # Do site-specific processing
        pass
```

---

## Administration

### Planned Admin Interface (MULTI-03)

```
/admin/sites/                    - Site management dashboard
/admin/sites/create              - Create new site
/admin/sites/<site_id>/edit      - Edit site settings
/admin/sites/<site_id>/domains   - Manage domains
/admin/sites/<site_id>/backup    - Site backup
/admin/sites/<site_id>/delete    - Delete site
```

### Current API

```python
site_manager = get_site_manager()

# List all sites
sites = site_manager.get_all_sites()

# Get site details
site = site_manager.get_site('my-site')

# Check if exists
if site_manager.site_exists('my-site'):
    pass
```

---

## Migration: Single → Multi-site

### Existing Single-site Installation

```
config.json          # Becomes sites/default/config.json
templates/           # Becomes sites/default/templates/
static/uploads/      # Becomes sites/default/uploads/
```

### Migration Process

1. **Backup current setup**
```bash
cp -r . backup/
```

2. **Create sites directory**
```python
from app.multisite import get_site_manager
manager = get_site_manager()
manager.init_app(app)
```

3. **Move existing site**
```bash
mkdir -p sites/default
mv config.json sites/default/
mv templates/* sites/default/templates/
mv static/images/uploads/* sites/default/uploads/
```

4. **Update code to use site context** (detailed in MIGRATION.md)

---

## Performance Considerations

### Site Isolation Overhead
- Minimal - just path prefixing
- No significant performance impact
- Cache per-site isolates efficiently

### Database Queries (Future)
- When per-site database added
- Automatic query scoping
- Index strategy per site

### Caching Strategy
- Each site has isolated cache
- Config cache per site
- Template cache per site
- Response cache per site

---

## Limitations & Future

### Current Limitations
- Single admin user across all sites
- No per-site user management yet
- No per-site permissions yet
- No site groups/organization yet

### Planned Enhancements (MULTI-05)
- Per-site user roles
- Site groups for organization
- Activity logging per site
- Advanced permission system
- Site usage limits/quotas
- Site groups and hierarchies

---

## Best Practices

### 1. Organize by Purpose
```
sites/
    default/        # Main corporate site
    blog/           # Blog
    shop/           # E-commerce
    docs/           # Documentation
```

### 2. Consistent Configuration
- Use similar structure across sites
- Share base templates where possible
- Maintain version consistency

### 3. Backup Strategy
- Regular per-site backups
- Use import/export system
- Test restoration procedures

### 4. Domain Management
- Keep clear domain records
- Update DNS properly
- Test routing in staging

### 5. Security
- Different passwords per site
- Enable isolation enforcement
- Monitor access logs
- Regular security updates

---

## Troubleshooting

### Site Not Found
```python
# Check if site exists
site_manager = get_site_manager()
if not site_manager.site_exists('my-site'):
    print("Site not found")

# Check registry
print(site_manager.get_all_sites())
```

### Domain Not Routing
```python
# Check domain mapping
site_id = site_manager.get_site_by_domain('example.com')
print(f"Domain routes to: {site_id}")

# Add domain if missing
site_manager.add_domain('site-id', 'example.com')
```

### Config Not Loading
```python
# Check file exists
config_path = site_manager.get_site_config_path('my-site')
print(f"Config path: {config_path}")
print(f"Exists: {os.path.exists(config_path)}")

# Check permissions
os.access(config_path, os.R_OK)
```

---

## Next Steps

**Remaining (MULTI-03, MULTI-05)**:
- Admin interface for site management
- Site template cloning UI
- Per-site user management
- Site activity logging
- Advanced permissions
- Site groups/organization
- Site quotas/limits
- Bulk operations

---

*Last Updated: December 2025*
*Part of Wicara v1.0.0 Advanced Features*
