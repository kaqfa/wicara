# WICARA CMS - Setup Instructions

## Table of Contents
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Initial Setup](#initial-setup)
- [Testing Your Installation](#testing-your-installation)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements
- **Python**: Version 3.8 or higher
- **Operating System**: Windows, macOS, Linux
- **Memory**: 512MB RAM minimum
- **Storage**: 100MB available space
- **Permissions**: Write access to project directory

### Recommended Requirements
- **Python**: Version 3.9 or higher
- **Memory**: 1GB RAM or more
- **Storage**: 1GB available space
- **Network**: Internet connection for deployment

### Optional Requirements
- **Git**: For version control
- **Virtual Environment**: Recommended for isolation
- **Web Server**: Nginx/Apache for production
- **SSL Certificate**: For HTTPS deployment

---

## Installation

### Method 1: Clone Repository (Recommended)

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/wicara.git
   cd wicara
   ```

2. **Create Virtual Environment** (Recommended)
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate on Windows
   venv\Scripts\activate
   
   # Activate on macOS/Linux
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Method 2: Download ZIP File

1. **Download** the ZIP file from GitHub
2. **Extract** the archive to your desired location
3. **Navigate** to the extracted directory
4. **Follow steps 2-3** from Method 1

### Method 3: Install from Scratch

1. **Create Project Directory**
   ```bash
   mkdir wicara
   cd wicara
   ```

2. **Create Requirements File**
   ```bash
   cat > requirements.txt << EOF
   Flask==2.3.3
   Werkzeug==2.3.7
   Jinja2==3.1.2
   MarkupSafe==2.1.3
   itsdangerous==2.1.2
   click==8.1.7
   blinker==1.6.3
   EOF
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download Required Files**
   - Get `app.py` from the repository
   - Get template files from `/templates/` directory
   - Get CSS files from `/static/css/` directory
   - Create `config.json` (see Configuration section)

---

## Configuration

### Basic Configuration

1. **Default Configuration File**
   - File: `config.json`
   - Automatically created if missing
   - Contains all website settings

2. **Manual Configuration**
   Create `config.json` with basic structure:
   ```json
   {
     "admin-password": "your-hashed-password",
     "sitename": "My Website",
     "description": "Website description",
     "keywords": ["keyword1", "keyword2"],
     "pages": [],
     "footer": {
       "content": ["Copyright 2025 My Website"]
     }
   }
   ```

### Environment Variables

1. **SECRET_KEY** (Production Required)
   ```bash
   export SECRET_KEY="your-secret-key-here"
   ```
   
2. **FLASK_ENV** (Optional)
   ```bash
   export FLASK_ENV="production"
   ```

### File Permissions

Ensure write permissions for:
- **config.json**: Configuration file
- **static/images/uploads/**: Image upload directory
- **Application directory**: For log files

```bash
# Linux/macOS
chmod 755 wicara/
chmod 644 config.json
chmod 755 static/images/uploads/

# Windows (via file explorer)
- Right-click folder > Properties > Security
- Grant write permissions
```

---

## Initial Setup

### 1. First Launch

1. **Start the Application**
   ```bash
   python app.py
   ```

2. **Verify Installation**
   - Open browser to: http://localhost:5555
   - Should see default WICARA website
   - No errors in console output

### 2. Admin Account Setup

1. **Access Admin Panel**
   - Go to: http://localhost:5555/admin
   - Default password: `admin123`

2. **Change Default Password**
   - Go to: `/admin/change-password`
   - Enter current password: `admin123`
   - Create strong new password
   - Confirm new password

### 3. Basic Configuration

1. **Site Settings**
   - Go to: `/admin/settings`
   - Update site name and description
   - Add SEO keywords
   - Configure footer content

2. **Create First Page**
   ```bash
   python app.py create-page "Home" "home.html" "/" "Home"
   ```

### 4. Test Image Upload

1. **Edit a page with image field**
2. **Upload a test image** (JPG, PNG, GIF, WebP)
3. **Verify image appears** on the website
4. **Check image storage** in `/static/images/uploads/`

---

## Testing Your Installation

### Basic Functionality Tests

1. **Website Access**
   - Visit: http://localhost:5555
   - Should load without errors
   - All CSS and images should load

2. **Admin Panel Access**
   - Visit: http://localhost:5555/admin
   - Login with your password
   - Dashboard should load

3. **Page Editing**
   - Edit any page
   - Add text content
   - Save changes
   - Verify updates appear on website

4. **Image Upload**
   - Upload an image
   - Verify image appears
   - Check image file in uploads directory

### CLI Commands Test

1. **Help Command**
   ```bash
   python app.py help
   ```

2. **List Pages**
   ```bash
   python app.py list-pages
   ```

3. **Create Test Page**
   ```bash
   python app.py create-page "Test" "test.html" "/test"
   ```

### Security Tests

1. **Password Change**
   - Change admin password
   - Verify old password no longer works
   - Login with new password

2. **Session Management**
   - Login to admin panel
   - Close browser and reopen
   - Verify session is maintained
   - Logout and verify session is cleared

### Error Handling Tests

1. **Invalid URL**
   - Visit non-existent page
   - Should see 404 error page
   - No server errors should occur

2. **Invalid Login**
   - Try wrong password
   - Should show error message
   - Should not allow access

---

## Production Deployment

### Option 1: Development Server (Testing Only)

```bash
# Start development server
python app.py

# Server runs on http://0.0.0.0:5555
```

### Option 2: Gunicorn (Production)

1. **Install Gunicorn**
   ```bash
   pip install gunicorn
   ```

2. **Start Gunicorn**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```

3. **Systemd Service** (Linux)
   ```ini
   [Unit]
   Description=WICARA CMS
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/path/to/wicara
   Environment=PATH=/path/to/venv/bin
   ExecStart=/path/to/venv/bin/gunicorn -w 4 -b 0.0.0.0:8000 app:app
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

### Option 3: Docker

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.9-slim

   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt

   COPY . .
   EXPOSE 5555

   CMD ["python", "app.py"]
   ```

2. **Build and Run**
   ```bash
   docker build -t wicara .
   docker run -p 5555:5555 wicara
   ```

### Option 4: Web Server Reverse Proxy

#### Nginx Configuration
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/wicara/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

#### Apache Configuration
```apache
<VirtualHost *:80>
    ServerName yourdomain.com
    DocumentRoot /path/to/wicara

    ProxyPreserveHost On
    ProxyPass /static/ !
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/

    <Directory /path/to/wicara/static>
        Require all granted
    </Directory>
</VirtualHost>
```

---

## Troubleshooting

### Common Installation Issues

#### Python Version Issues
**Problem**: "Python version not supported"
**Solutions**:
- Check Python version: `python --version`
- Upgrade to Python 3.8+
- Use `python3` instead of `python` if needed

#### Permission Issues
**Problem**: "Permission denied" errors
**Solutions**:
- Use virtual environment
- Check file permissions
- Run as appropriate user
- Use `sudo` only when necessary

#### Dependency Issues
**Problem**: Module import errors
**Solutions**:
- Install requirements: `pip install -r requirements.txt`
- Update pip: `pip install --upgrade pip`
- Check for conflicting packages

### Configuration Issues

#### Config File Not Found
**Problem**: "config.json not found"
**Solutions**:
- File should be in same directory as `app.py`
- Check file permissions
- Verify file is valid JSON format

#### Invalid JSON
**Problem**: "Invalid JSON format"
**Solutions**:
- Validate JSON syntax
- Use JSON validator online
- Check for trailing commas
- Verify quote usage

### Runtime Issues

#### Port Already in Use
**Problem**: "Port 5555 already in use"
**Solutions**:
- Kill process using port
- Change port in code
- Use different port for development

#### Template Not Found
**Problem**: "Template not found" errors
**Solutions**:
- Check template file exists
- Verify template path
- Check file permissions
- Restart application

#### Image Upload Issues
**Problem**: Image upload fails
**Solutions**:
- Check upload directory permissions
- Verify file size < 5MB
- Check file format (JPG, PNG, GIF, WebP)
- Ensure sufficient disk space

### Performance Issues

#### Slow Loading
**Problem**: Website loads slowly
**Solutions**:
- Optimize image sizes
- Check server resources
- Review template complexity
- Consider caching solutions

#### High Memory Usage
**Problem**: Application uses too much memory
**Solutions**:
- Restart application
- Check for memory leaks
- Optimize templates
- Monitor resource usage

### Getting Help

1. **Check Logs**: Review console output and error messages
2. **Documentation**: Read all setup instructions
3. **GitHub Issues**: Search for similar problems
4. **Community**: Ask for help in community forums
5. **Support**: Contact development team

---

## Next Steps

After successful installation:

1. **Customize Design**: Modify CSS and templates
2. **Add Content**: Create pages and add content
3. **Configure SEO**: Set up meta descriptions and keywords
4. **Test Functionality**: Verify all features work
5. **Deploy**: Set up production environment
6. **Monitor**: Regularly check performance and logs

---

*Last Updated: November 10, 2025*
*Version: 1.0*