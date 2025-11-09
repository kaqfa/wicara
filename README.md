# Wicara - Editable Static Web CMS

A lightweight, flat-file CMS built with Flask that allows you to create editable static websites without a database. Perfect for profile websites, landing pages, and simple business websites.

## Features

- **Zero Database**: All content stored in a single `config.json` file
- **Simple Admin Panel**: Easy-to-use interface for content editing
- **Template-Based**: Use HTML templates with placeholder syntax
- **Image Upload**: Support for image uploads with validation
- **Secure**: Password-protected admin area with session management
- **Portable**: Easy backup and migration (just copy files)
- **Lightweight**: Minimal dependencies and fast performance

## Quick Start

### Prerequisites

- Python 3.8+
- pip package manager

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

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Access the website**
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
├── app.py                 # Main Flask application
├── config.json           # Website configuration and content
├── requirements.txt      # Python dependencies
├── templates/            # HTML templates
│   ├── home.html
│   ├── about.html
│   ├── contact.html
│   └── admin/           # Admin panel templates
│       ├── login.html
│       ├── dashboard.html
│       └── edit_page.html
├── static/              # Static assets
│   ├── css/
│   │   ├── style.css    # Public website styles
│   │   └── admin.css    # Admin panel styles
│   ├── js/
│   │   └── admin.js     # Admin panel scripts
│   └── images/
│       └── uploads/     # User uploaded images
└── utils/               # Helper functions (if needed)
```

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

1. **Set environment variables**:
   ```bash
   export SECRET_KEY="your-secret-key-here"
   export FLASK_ENV="production"
   ```

2. **Use a production WSGI server**:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```

3. **Configure web server** (Apache/Nginx) to reverse proxy to the WSGI server

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

## Backup and Migration

### Backup

Simply copy the entire project directory or download:
- `config.json` (contains all content)
- `static/images/uploads/` (uploaded images)

### Migration

1. Copy all files to new server
2. Install dependencies: `pip install -r requirements.txt`
3. Set file permissions
4. Run the application

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

## Development

### Adding Features

The codebase is intentionally simple. To add new features:

1. Modify `app.py` for new routes/logic
2. Update templates in `templates/`
3. Add styles in `static/css/`
4. Test thoroughly

### Contributing

1. Keep changes minimal and focused
2. Follow existing code style
3. Test all functionality
4. Update documentation

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
