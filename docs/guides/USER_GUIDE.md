# WICARA CMS - User Documentation

## Table of Contents
- [Quick Start](#quick-start)
- [Admin Panel Guide](#admin-panel-guide)
- [Content Management](#content-management)
- [Image Management](#image-management)
- [Settings Management](#settings-management)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

## Quick Start

### 1. Start WICARA CMS
```bash
python app.py
```
The application will start on http://localhost:5555

### 2. Access Admin Panel
- Go to: http://localhost:5555/admin
- Default password: `admin123`
- **Important**: Change the password immediately after first login

### 3. Basic Workflow
1. **Login** to admin panel
2. **Edit pages** from dashboard
3. **Upload images** through the form
4. **Save changes** (updates immediately)
5. **Logout** when finished

---

## Admin Panel Guide

### Login Screen
- **URL**: `/admin/login`
- **Default Password**: `admin123`
- **Security**: Password hashing with scrypt

### Dashboard Overview
The admin dashboard provides:

- **Page List**: All configured pages with edit links
- **Quick Actions**: Edit existing pages instantly
- **Settings Access**: Global site configuration
- **Password Management**: Change admin password

### Navigation Menu
- **Dashboard**: `/admin` - Main page overview
- **Settings**: `/admin/settings` - Global site settings
- **Change Password**: `/admin/change-password` - Password management
- **Logout**: `/admin/logout` - Secure session termination

---

## Content Management

### Editing Pages

1. **Access Page Editor**
   - Click "Edit" next to any page in the dashboard
   - Or go directly to `/admin/edit/[page-index]`

2. **Available Field Types**
   
   #### Text Fields
   - **Purpose**: Single-line text input
   - **Use for**: Titles, links, short descriptions
   - **Limit**: 255 characters
   - **Validation**: Required fields must be filled

   #### Textarea Fields
   - **Purpose**: Multi-line text input
   - **Use for**: Descriptions, content paragraphs
   - **Limit**: 5000 characters
   - **Features**: Auto-resizing textarea

   #### Image Fields
   - **Purpose**: Image upload and management
   - **Supported Formats**: JPG, JPEG, PNG, GIF, WebP
   - **Size Limit**: 5MB
   - **Features**: 
     - Image preview
     - Automatic old image cleanup
     - Secure filename generation

3. **Saving Changes**
   - Click "Save Changes" button
   - Changes update immediately on the website
   - Success message appears on save
   - Error messages show if validation fails

### Auto-save Feature
- No auto-save implemented (manual save required)
- Browser warning if leaving unsaved changes

---

## Image Management

### Supported Formats
- **JPEG/JPG**: Best for photographs
- **PNG**: Best for graphics with transparency
- **GIF**: For simple animations
- **WebP**: Modern format with better compression

### Upload Process
1. Click "Choose File" button
2. Select image from your computer
3. System validates file type and size
4. Image preview appears
5. Save page to upload image

### Storage Location
- **Path**: `/static/images/uploads/`
- **Naming**: Automatic secure filename generation
- **Cleanup**: Old images removed when replaced

### Image Limits
- **Maximum Size**: 5MB per file
- **File Types**: Only allowed formats accepted
- **Validation**: Server-side and client-side validation

---

## Settings Management

### Global Settings (`/admin/settings`)

#### Site Configuration
- **Site Name**: Website title (appears in browser tab and header)
- **Description**: SEO description for search engines
- **Keywords**: SEO keywords (comma-separated)
- **Footer Content**: Footer text lines

#### SEO Optimization
- **Meta Description**: Automatically used by search engines
- **Meta Keywords**: Helps with SEO (deprecated but supported)
- **Page Titles**: Individual page SEO titles

#### Content Organization
- **Menu Order**: Page navigation order
- **URL Structure**: Clean URL configuration
- **Template Assignment**: Page template selection

### Password Management (`/admin/change-password`)

#### Security Features
- **Current Password**: Required for verification
- **New Password**: Strength requirements apply
- **Confirmation**: Must match new password
- **Hashing**: Secure scrypt algorithm

#### Password Guidelines
- Minimum 8 characters recommended
- Mix of letters, numbers, and symbols
- Avoid common words and patterns

---

## Security

### Built-in Security Features

#### Authentication
- **Password Hashing**: Scrypt algorithm
- **Session Management**: Secure Flask sessions
- **Timeout**: Automatic session expiration
- **Logout**: Complete session clearing

#### Input Validation
- **XSS Protection**: HTML sanitization
- **Length Limits**: Text field restrictions
- **Required Fields**: Validation enforcement
- **Type Checking**: Data type validation

#### File Upload Security
- **Type Validation**: Magic number verification
- **Size Limits**: 5MB maximum file size
- **Path Protection**: Directory traversal prevention
- **Secure Naming**: Safe filename generation

#### CSRF Protection
- **Form Tokens**: Request validation
- **Session Binding**: User-specific tokens
- **Automatic Protection**: Built into forms

### Best Practices

1. **Change Default Password**: Immediately after first login
2. **Regular Backups**: Copy `config.json` regularly
3. **Secure Server**: Use HTTPS in production
4. **Access Control**: Limit admin panel access
5. **Update Dependencies**: Keep Flask and packages current

---

## Troubleshooting

### Common Issues

#### Login Problems
**Problem**: Cannot login with admin password
**Solutions**:
- Check password spelling
- Verify default password: `admin123`
- If forgotten, manually reset in `config.json`

#### Image Upload Fails
**Problem**: Image upload shows error
**Solutions**:
- Check file size (under 5MB)
- Verify file format (JPG, PNG, GIF, WebP)
- Ensure upload directory permissions
- Check disk space

#### Page Not Found
**Problem**: 404 error for page
**Solutions**:
- Verify URL in `config.json`
- Check template file exists
- Confirm page is active
- Check for syntax errors in templates

#### Save Changes Fails
**Problem**: Cannot save page changes
**Solutions**:
- Check file permissions for `config.json`
- Verify required fields are filled
- Check for character limit violations
- Ensure server has write permissions

#### Performance Issues
**Problem**: Slow loading pages
**Solutions**:
- Optimize image sizes
- Check server resources
- Review template complexity
- Consider caching

### Error Messages

#### File Operation Errors
- **"Config file not found"**: `config.json` missing or permissions issue
- **"Cannot save config"**: File permissions or disk space issue
- **"Invalid file type"**: Unsupported file format uploaded

#### Validation Errors
- **"Field cannot be empty"**: Required field validation
- **"Text too long"**: Character limit exceeded
- **"Invalid URL format"**: URL validation failed

#### Session Errors
- **"Session expired"**: Login timeout, re-login required
- **"Invalid credentials"**: Password incorrect
- **"Access denied"**: Permission issue

### Debug Mode

For development and troubleshooting:
```bash
# Run with debug mode
python app.py
# Debug automatically enabled in development
```

### Log Files

Check application logs for:
- Error details
- Failed login attempts
- File operation issues
- Template errors

### Getting Help

1. **Documentation**: Read this guide thoroughly
2. **Error Messages**: Note exact error text
3. **Recent Changes**: Identify what changed
4. **Server Logs**: Check application logs
5. **Community**: Contact support channels

---

## FAQ

### General Questions

**Q: What is WICARA CMS?**
A: A lightweight, flat-file CMS built with Flask that stores content in JSON files instead of a database.

**Q: Do I need a database?**
A: No. WICARA uses a single `config.json` file for all content storage.

**Q: Can I use WICARA for large websites?**
A: WICARA is designed for small to medium websites (up to ~50 pages). For larger sites, consider traditional CMS platforms.

### Technical Questions

**Q: What are the server requirements?**
A: Python 3.8+, Flask framework, and write permissions for the project directory.

**Q: Can I customize the templates?**
A: Yes. Templates use Jinja2 syntax and can be fully customized in the `/templates` folder.

**Q: How do I backup my content?**
A: Simply copy the `config.json` file and `/static/images/uploads/` directory.

### Usage Questions

**Q: How do I add a new page?**
A: Use CLI command: `python app.py create-page "Title" "template.html" "/url"`

**Q: Can multiple users edit content?**
A: WICARA has single admin user. For multi-user support, consider enterprise CMS solutions.

**Q: How do I change the site design?**
A: Edit CSS files in `/static/css/` and HTML templates in `/templates/`.

### Security Questions

**Q: Is WICARA secure?**
A: Yes, WICARA includes built-in security features like input validation, file upload security, and session management.

**Q: Should I change the default password?**
A: Absolutely! Change it immediately after first login.

**Q: Can I use WICARA with HTTPS?**
A: Yes, deploy behind a reverse proxy (Nginx/Apache) with SSL certificates.

### Migration Questions

**Q: Can I export content from other CMS?**
A: Yes, you'll need to convert content to JSON format matching WICARA's structure.

**Q: How do I move WICARA to another server?**
A: Copy all project files to the new server and install dependencies.

---

## Contact and Support

For additional help:
- **Documentation**: Read all sections of this guide
- **GitHub Issues**: Report bugs and feature requests
- **Community**: Join Discord community for support
- **Email**: Contact development team for enterprise support

---

*Last Updated: November 10, 2025*
*Version: 1.0*