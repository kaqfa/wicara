# Wicara CMS - Development Backlog

## 📋 Project Status: **60% Complete** - MVP Ready, Production Features Missing

> **Note**: Default development port changed to **5555** to avoid conflicts on macOS

---

## ✅ **COMPLETED FEATURES**

### Core System
- [x] **FR-01**: Load Configuration - `load_config()` dengan error handling
- [x] **FR-02**: Save Configuration - `save_config()` dengan error handling  
- [x] **FR-04**: Route Management - URL mapping untuk public pages
- [x] **FR-05**: Template Rendering - `render_template_with_data()` dengan Jinja2
- [x] **FR-06**: 404 Error Page - Return 404 untuk missing pages
- [x] **FR-07**: Global Data Injection - Global vars tersedia di templates

### Authentication & Admin
- [x] **FR-08**: Admin Login - Password hashing dengan werkzeug
- [x] **FR-09**: Session Management - Flask sessions dengan timeout
- [x] **FR-10**: Logout - Session clearing implemented
- [x] **FR-11**: Admin Dashboard - Page listing dengan edit links
- [x] **FR-12**: Edit Page Form - Dynamic form generation
- [x] **FR-13**: Save Page Changes - POST handling dan config updates

### Templates & UI
- [x] **UI-01**: Public Pages - Template-based rendering (home, about, contact)
- [x] **UI-02**: Login Page - Simple form dengan styling
- [x] **UI-03**: Admin Dashboard - Page listing dengan actions
- [x] **UI-04**: Edit Page Form - Dynamic form generation
- [x] **UI-05**: Responsive Design - Mobile-friendly admin interface

### Configuration
- [x] JSON Schema Compliance - Struktur config.json sesuai SRS
- [x] Field Types Support - text, textarea, image fields
- [x] Basic Image Upload - File upload ke static/images/uploads/

---

## 🚧 **IN PROGRESS / PARTIAL**

### File Upload System
- [ ] **FR-15**: Image Upload - ⚠️ Basic upload works, missing validation
- [ ] **FR-16**: Image Preview - ⚠️ Preview shown, missing thumbnail generation
- [ ] **FR-17**: Old Image Cleanup - ❌ No cleanup saat replace images

### Validation & Security
- [ ] **FR-03**: JSON Structure Validation - ⚠️ Basic validation only
- [ ] **FR-18**: Input Validation - ❌ Missing length limits & sanitization
- [ ] **FR-19**: File Write Error Handling - ⚠️ Basic error handling only
- [ ] **FR-20**: Template Not Found Handling - ❌ No fallback for missing templates

---

## 📝 **PENDING BACKLOG**

### **HIGH PRIORITY** (Security & Core Features)

#### Security Hardening
- [ ] **SEC-01**: Input Validation
  - Text field max length: 255 chars
  - Textarea max length: 5000 chars  
  - HTML sanitization before save
  - Required field validation

- [ ] **SEC-02**: File Upload Security
  - File type validation (jpg, jpeg, png, gif, webp)
  - File size limit: 5MB
  - File signature validation (not just extension)
  - Path traversal protection
  - Secure filename generation

- [ ] **SEC-03**: Session Security
  - Session timeout configuration
  - Session regeneration on login
  - CSRF protection for forms

#### Admin Interface Enhancement
- [ ] **ADMIN-01**: Global Settings Editor
  - Edit sitename, description, keywords
  - Edit footer content
  - Save changes to config.json
  - Form validation

- [ ] **ADMIN-02**: Password Change Interface
  - Current password verification
  - New password confirmation
  - Password strength requirements
  - Update admin-password hash

- [ ] **ADMIN-03**: Better Error Handling
  - User-friendly error messages
  - Flash message improvements
  - Form validation feedback
  - File operation error handling

### **MEDIUM PRIORITY** (Features & UX)

#### Template System
- [ ] **TPL-01**: Template Error Handling
  - Fallback template for missing files
  - Template syntax error handling
  - Debug mode for template issues

- [ ] **TPL-02**: Navigation Auto-Generation
  - Auto-create menu from pages array
  - Active page highlighting
  - Menu ordering configuration

#### Content Management
- [ ] **CONTENT-01**: Image Management
  - Old image cleanup on replace
  - Image preview thumbnails
  - Image gallery view
  - Bulk image operations

- [ ] **CONTENT-02**: JSON Schema Validation
  - Required field validation
  - Data type validation
  - Unique URL validation
  - Schema migration handling

### **LOW PRIORITY** (Nice to Have)

#### Developer Tools
- [ ] **DEV-01**: Management Commands
  - CLI command untuk create new page
  - Template generator command
  - Config validation command
  - Backup/restore commands

- [ ] **DEV-02**: Development Tools
  - Debug mode improvements
  - Performance monitoring
  - Error logging
  - Configuration wizard

#### Documentation & UX
- [ ] **DOC-01**: User Documentation
  - Admin panel user guide
  - Setup instructions
  - Troubleshooting guide
  - Video tutorials

- [ ] **DOC-02**: Developer Documentation
  - Template creation guide
  - Field type reference
  - API documentation
  - Contribution guidelines

---

## 🆕 **NEW FEATURE REQUESTS**

### **Management Commands System**
- [ ] **CLI-01**: Page Creation Command
  ```bash
  python manage.py create-page --title "About Us" --template about.html --url /about
  ```
  - Interactive page creation wizard
  - Auto-generate template skeleton
  - Add to config.json automatically
  - Validate URL uniqueness

- [ ] **CLI-02**: User Management Commands
  ```bash
  python manage.py change-password
  python manage.py reset-admin
  ```
  - Password change utility
  - Admin reset functionality
  - Session management commands

- [ ] **CLI-03**: Content Management Commands
  ```bash
  python manage.py backup
  python manage.py restore backup.json
  python manage.py validate-config
  ```
  - Backup/restore functionality
  - Configuration validation
  - Data migration tools

### **Enhanced Admin Interface**
- [ ] **UI-06**: Settings Menu
  - Global website settings
  - SEO configuration
  - Social media links
  - Analytics integration

- [ ] **UI-07**: User Profile Section
  - Admin profile management
  - Password change form
  - Session management
  - Activity log

- [ ] **UI-08**: Advanced Content Editor
  - Rich text editor (optional)
  - Image gallery manager
  - File browser
  - Content preview

---

## 📊 **Progress Metrics**

### Completion Status
- **Total Items**: 47
- **Completed**: 15 (32%)
- **In Progress**: 6 (13%)
- **Pending**: 26 (55%)

### SRS Compliance
- **Functional Requirements**: 12/20 implemented (60%)
- **Non-Functional Requirements**: 8/14 implemented (57%)
- **Security Requirements**: 4/7 implemented (57%)

### Target Timeline
- **Phase 1** (Security & Core): 2-3 days
- **Phase 2** (Features & UX): 2-3 days  
- **Phase 3** (Documentation & Polish): 1-2 days

---

## 🎯 **Next Sprint Focus**

### **Priority 1: Security Hardening**
1. Input validation implementation
2. File upload security
3. Session security improvements

### **Priority 2: Admin Interface**
1. Global settings editor
2. Password change interface
3. Better error handling

### **Priority 3: Management Commands**
1. Page creation CLI
2. Password management CLI
3. Backup/restore utilities

---

*Last Updated: November 9, 2025*
*Next Review: After Phase 1 completion*