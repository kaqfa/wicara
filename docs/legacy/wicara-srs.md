# Software Requirements Specification (SRS)
## Editable Static Web - Flat-File CMS

**Version:** 1.0  
**Date:** November 9, 2025  
**Status:** Draft  

---

## 1. Introduction

### 1.1 Purpose
Dokumen ini mendefinisikan functional dan non-functional requirements untuk Editable Static Web, sebuah flat-file CMS yang memungkinkan pembuatan website dengan konten yang dapat diedit tanpa database.

### 1.2 Scope
Sistem ini ditujukan untuk profile website, landing page, dan website sederhana (5-10 halaman) yang membutuhkan content management tanpa kompleksitas CMS tradisional.

### 1.3 Definitions & Acronyms
- **CMS:** Content Management System
- **SRS:** Software Requirements Specification
- **MVP:** Minimum Viable Product
- **Field:** Unit data yang dapat diedit (text, textarea, image)
- **Template:** File HTML dengan placeholder untuk dynamic content
- **Config.json:** File JSON yang menyimpan semua data website

### 1.4 References
- JSON Specification: https://www.json.org/
- Backend-specific documentation (pilih salah satu):
  - PHP: https://www.php.net/docs.php
  - Python Flask: https://flask.palletsprojects.com/
  - Node.js Express: https://expressjs.com/

---

## 2. Overall Description

### 2.1 Product Perspective
Sistem ini adalah standalone application yang berjalan di PHP hosting tradisional. Tidak membutuhkan database atau framework eksternal.

### 2.2 Product Functions
1. Rendering website dari template + JSON data
2. Admin panel untuk edit konten
3. Authentication untuk protect admin area
4. File upload management untuk images
5. JSON file management (read/write)

### 2.3 User Classes
- **Developer:** Setup dan konfigurasi website
- **End User/Client:** Edit konten melalui admin panel

### 2.4 Operating Environment
- **Server:** Web server dengan backend runtime support
  - Apache/Nginx dengan PHP, atau
  - Python WSGI server (Gunicorn, uWSGI), atau
  - Node.js runtime
- **Backend Runtime:** 
  - PHP 7.4+ (jika menggunakan PHP), atau
  - Python 3.8+ (jika menggunakan Flask/FastAPI), atau
  - Node.js 14+ (jika menggunakan Express)
- **Browser:** Modern browsers (Chrome, Firefox, Safari, Edge)
- **Storage:** Read/write permission pada folder project

### 2.5 Design & Implementation Constraints
- Harus bisa jalan di hosting murah (shared hosting atau VPS entry-level)
- Minimal framework/dependency (prefer lightweight atau zero-dependency)
- Ukuran total project (excluding assets) < 1MB
- Easy deployment (FTP, Git, atau Docker)
- Cross-platform compatible

---

## 3. System Features

### 3.1 JSON Configuration Management

**FR-01: Load Configuration**
- **Description:** Sistem harus bisa membaca config.json dan parse menjadi native data structure
- **Priority:** High
- **Input:** config.json file path
- **Output:** Native data structure (dict/object/array)
- **Error Handling:** 
  - Jika file tidak ada, return error
  - Jika JSON invalid, return error dengan detail

**FR-02: Save Configuration**
- **Description:** Sistem harus bisa menyimpan perubahan ke config.json
- **Priority:** High
- **Input:** Native data structure
- **Output:** Updated config.json file
- **Error Handling:**
  - Backup existing file sebelum overwrite
  - Validate JSON structure sebelum save
  - Return error jika file tidak writable

**FR-03: Validate JSON Structure**
- **Description:** Sistem harus memvalidasi struktur JSON sesuai schema
- **Priority:** Medium
- **Validation Rules:**
  - Required keys: `admin-password`, `sitename`, `pages`
  - `pages` harus array dengan minimal 1 page
  - Setiap page harus punya: `title`, `template`, `url`
- **Output:** Boolean (valid/invalid) + error messages

---

### 3.2 Public Page Rendering

**FR-04: Route Management**
- **Description:** Sistem harus bisa memetakan URL ke page configuration
- **Priority:** High
- **Input:** Request URI
- **Process:**
  1. Parse URI dari request
  2. Cari matching page di config.json berdasarkan `url` field
  3. Return page data atau 404
- **Output:** Page configuration array atau 404 error

**FR-05: Template Rendering**
- **Description:** Sistem harus bisa render template HTML dengan data dari config.json
- **Priority:** High
- **Input:** 
  - Template file path
  - Fields array dari page
  - Global data (sitename, footer, etc)
- **Process:**
  1. Load template file
  2. Replace `{{field-name}}` dengan actual value
  3. Replace global placeholders ({{sitename}}, {{footer}})
- **Output:** Rendered HTML string
- **Placeholder Syntax:** `{{field-name}}`

**FR-06: 404 Error Page**
- **Description:** Sistem harus menampilkan 404 page untuk URL yang tidak ditemukan
- **Priority:** Medium
- **Output:** 404 HTTP status + error page

**FR-07: Global Data Injection**
- **Description:** Data global (sitename, footer, keywords) harus tersedia di semua page
- **Priority:** Medium
- **Scope:** Semua template bisa akses: `{{sitename}}`, `{{description}}`, `{{footer}}`

---

### 3.3 Authentication

**FR-08: Admin Login**
- **Description:** Sistem harus menyediakan login page untuk akses admin panel
- **Priority:** High
- **Input:** Password dari form
- **Process:**
  1. Hash password yang diinput
  2. Bandingkan dengan `admin-password` di config.json
  3. Jika match, create session
- **Output:** Redirect ke admin dashboard atau error message
- **Security:** 
  - Password harus di-hash dengan secure algorithm (bcrypt/argon2)
  - Session timeout: 30 menit
  - Max login attempt: tidak ada limit di v1 (future: rate limiting)

**FR-09: Session Management**
- **Description:** Sistem harus maintain user session setelah login
- **Priority:** High
- **Process:**
  - Simpan session data: `admin_logged_in`, `login_time`
  - Check session di setiap request ke admin page
  - Auto logout setelah 30 menit inactive
- **Session Data:** 
  - `admin_logged_in` (boolean)
  - `login_time` (timestamp)

**FR-10: Logout**
- **Description:** User harus bisa logout dari admin panel
- **Priority:** Medium
- **Process:**
  1. Destroy session
  2. Redirect ke login page

---

### 3.4 Admin Panel

**FR-11: Admin Dashboard**
- **Description:** Halaman utama admin yang menampilkan list pages
- **Priority:** High
- **Display:**
  - List semua pages dengan title dan menu-title
  - Link edit untuk setiap page
  - Logout button
- **Access Control:** Harus login terlebih dahulu

**FR-12: Edit Page Form**
- **Description:** Form untuk edit fields dari sebuah page
- **Priority:** High
- **Input:** Page identifier (index atau url)
- **Process:**
  1. Load page data dari config.json
  2. Generate form berdasarkan `fields` array
  3. Loop setiap field dan render input sesuai type
- **Form Fields:**
  - Text: `<input type="text">`
  - Textarea: `<textarea>`
  - Image: `<input type="file">` + preview current image
- **Display:** Current value harus pre-filled di form

**FR-13: Save Page Changes**
- **Description:** Proses penyimpanan perubahan dari edit form
- **Priority:** High
- **Input:** POST data dari form
- **Process:**
  1. Validate input (tidak boleh kosong untuk required fields)
  2. Update nilai fields di config.json
  3. Save config.json
- **Output:** Success message + redirect ke dashboard atau error message
- **Validation:**
  - Text: max length 255 chars
  - Textarea: max length 5000 chars
  - Image: validate file type dan size

**FR-14: Global Settings Edit**
- **Description:** Form untuk edit global settings (sitename, description, footer)
- **Priority:** Medium
- **Input:** Global settings fields
- **Output:** Updated config.json

---

### 3.5 File Upload Management

**FR-15: Image Upload**
- **Description:** Sistem harus bisa handle image upload untuk image fields
- **Priority:** High
- **Input:** File dari form (multipart/form-data)
- **Process:**
  1. Validate file type (jpg, jpeg, png, gif, webp)
  2. Validate file size (max 5MB)
  3. Generate unique filename (timestamp + original name)
  4. Save file ke `assets/images/uploads/`
  5. Update path di config.json
- **Allowed Types:** `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`
- **Max Size:** 5 MB
- **Output:** File path relative ke root (`/assets/images/uploads/filename.jpg`)

**FR-16: Image Preview**
- **Description:** Admin panel harus menampilkan preview image yang sudah diupload
- **Priority:** Medium
- **Display:** Thumbnail image dengan max width 200px

**FR-17: Old Image Cleanup**
- **Description:** Saat image diganti, file lama harus dihapus (optional untuk v1)
- **Priority:** Low
- **Process:**
  1. Sebelum upload image baru, simpan path image lama
  2. Setelah upload sukses, hapus file lama
- **Note:** Feature ini optional, bisa di-skip di v1

---

### 3.6 Error Handling & Validation

**FR-18: Input Validation**
- **Description:** Semua input dari user harus divalidasi
- **Validation Rules:**
  - Text field: tidak boleh kosong, max 255 chars
  - Textarea: tidak boleh kosong, max 5000 chars
  - Image: file type dan size validation
- **Output:** Error message yang jelas untuk user

**FR-19: File Write Error Handling**
- **Description:** Handle error saat save config.json
- **Scenarios:**
  - File tidak writable
  - Disk full
  - JSON encoding error
- **Output:** User-friendly error message

**FR-20: Template Not Found Handling**
- **Description:** Handle error saat template file tidak ditemukan
- **Output:** Error message + fallback ke default template atau 404

---

## 4. Non-Functional Requirements

### 4.1 Performance Requirements

**NFR-01: Page Load Time**
- Public page harus load dalam < 500ms (excluding network latency)
- Admin panel harus load dalam < 1s

**NFR-02: File Size**
- config.json harus < 100KB untuk website dengan 10 pages
- Total backend code harus < 1MB

**NFR-03: Scalability Limit**
- Sistem dirancang untuk max 10 pages
- Max 50 fields per page
- Max 5MB per image upload

### 4.2 Security Requirements

**NFR-04: Password Security**
- Password harus disimpan dalam bentuk hash
- Recommended algorithms: bcrypt, argon2, atau PBKDF2
- Implementation:
  - PHP: `password_hash()` dengan PASSWORD_DEFAULT
  - Python: `werkzeug.security.generate_password_hash()` atau `bcrypt`
  - Node.js: `bcrypt` library

**NFR-05: File Upload Security**
- Hanya allow image file types
- Validate file signature, bukan hanya extension
- Prevent path traversal attack
- Store uploaded files di dedicated folder dengan proper permissions

**NFR-06: Session Security**
- Session ID harus random dan secure
- Session timeout: 30 menit
- Session data harus di-validate setiap request

**NFR-07: Input Sanitization**
- Semua user input harus di-sanitize sebelum save
- Escape output untuk prevent XSS
- Prevent SQL injection (not applicable karena no DB, tapi tetap sanitize)

### 4.3 Usability Requirements

**NFR-08: Admin UI Simplicity**
- Admin panel harus bisa digunakan oleh non-technical user
- Form labels harus jelas dan descriptive
- Error messages harus user-friendly (bukan technical error)

**NFR-09: Setup Simplicity**
- Developer harus bisa setup website baru dalam < 30 menit
- Cukup copy files + edit config.json

**NFR-10: Learning Curve**
- End user harus bisa edit konten dalam < 10 menit setelah diberi brief tutorial

### 4.4 Portability Requirements

**NFR-11: Hosting Compatibility**
- Harus bisa jalan di hosting murah dengan minimal requirements
- Tidak butuh special server extensions atau libraries
- Tidak butuh SSH access atau command line (untuk deployment via FTP)
- Alternatif: Support Docker deployment untuk modern hosting

**NFR-12: Migration Ease**
- Website harus bisa dipindah ke hosting lain dengan copy-paste files
- Tidak ada hardcoded paths
- Config.json portability (backup & restore)

### 4.5 Maintainability Requirements

**NFR-13: Code Simplicity**
- Code harus mudah dibaca dan dimodifikasi
- Minimal abstraction (karena target simple use case)
- Clear function naming dan structure

**NFR-14: Documentation**
- Inline comments untuk logic yang kompleks saja
- README dengan setup instruction
- User guide untuk end user

---

## 5. Data Requirements

### 5.1 JSON Configuration Schema

```json
{
  "admin-password": {
    "type": "string",
    "description": "Hashed password untuk admin login",
    "required": true,
    "example": "$2y$10$..."
  },
  "sitename": {
    "type": "string",
    "description": "Nama website",
    "required": true,
    "maxLength": 100
  },
  "description": {
    "type": "string",
    "description": "Deskripsi website untuk meta tag",
    "required": false,
    "maxLength": 255
  },
  "keywords": {
    "type": "array",
    "description": "Keywords untuk SEO",
    "required": false,
    "items": "string"
  },
  "pages": {
    "type": "array",
    "description": "Array of page objects",
    "required": true,
    "minItems": 1,
    "items": {
      "title": {
        "type": "string",
        "description": "Page title untuk <title> tag",
        "required": true
      },
      "template": {
        "type": "string",
        "description": "Nama file template (e.g., home.html)",
        "required": true
      },
      "menu-title": {
        "type": "string",
        "description": "Judul untuk navigation menu",
        "required": false
      },
      "url": {
        "type": "string",
        "description": "URL path (e.g., /, /about, /contact)",
        "required": true,
        "unique": true
      },
      "seo-description": {
        "type": "string",
        "description": "Meta description untuk SEO",
        "required": false
      },
      "seo-keywords": {
        "type": "array",
        "description": "Keywords spesifik untuk page ini",
        "required": false
      },
      "fields": {
        "type": "array",
        "description": "Editable fields untuk page ini",
        "required": false,
        "items": {
          "name": {
            "type": "string",
            "description": "Field identifier untuk placeholder",
            "required": true
          },
          "type": {
            "type": "string",
            "enum": ["text", "textarea", "image"],
            "description": "Field type",
            "required": true
          },
          "label": {
            "type": "string",
            "description": "Label untuk form input di admin",
            "required": false
          },
          "value": {
            "type": "string",
            "description": "Actual content/path",
            "required": false
          }
        }
      }
    }
  },
  "footer": {
    "type": "object",
    "description": "Global footer content",
    "required": false,
    "properties": {
      "content": {
        "type": "array",
        "items": "string"
      }
    }
  }
}
```

### 5.2 File Structure Requirements

**General Structure:**
```
project-root/
├── server/                # Backend files (PHP/Python/Node.js)
│   ├── main.*            # Entry point (index.php/app.py/server.js)
│   ├── routes.*          # Routing logic
│   ├── handlers.*        # Request handlers
│   └── utils.*           # Helper functions
├── config.json           # Data store
├── templates/
│   ├── home.html
│   ├── about.html
│   └── contact.html
└── assets/
    ├── css/
    │   └── admin.css     # Admin panel styles
    ├── js/
    │   └── admin.js      # Admin panel scripts (if needed)
    └── images/
        └── uploads/      # User uploaded images
```

**PHP Implementation Example:**
```
├── index.php             # Public router
├── admin.php             # Admin panel
├── auth.php              # Authentication handler
├── functions.php         # Core utilities
├── config.json
├── templates/
└── assets/
```

**Python Flask Example:**
```
├── app.py                # Flask app + routes
├── config.json
├── templates/            # Flask templates folder
└── static/               # Static assets (CSS, JS, images)
    └── uploads/
```

**Node.js Express Example:**
```
├── server.js             # Express app
├── routes/
│   ├── public.js
│   └── admin.js
├── config.json
├── views/                # Template files
└── public/               # Static assets
    └── uploads/
```

---

## 6. Interface Requirements

### 6.1 User Interfaces

**UI-01: Public Pages**
- Design: Sesuai template yang dibuat developer
- Responsive: Tergantung template
- Navigation: Auto-generated dari pages array

**UI-02: Login Page**
- Simple form: password field + submit button
- Error message area
- Minimal styling (functional)

**UI-03: Admin Dashboard**
- List pages dalam bentuk table atau cards
- Columns: Page Title, URL, Actions (Edit button)
- Logout button di header/footer
- Link ke global settings

**UI-04: Edit Page Form**
- Page title di header
- Form fields sesuai page.fields
- Submit dan Cancel button
- Success/error message area

### 6.2 API Interfaces
Tidak ada external API. Semua interaksi via PHP page requests.

### 6.3 Communication Interfaces
- HTTP/HTTPS untuk web access
- Standard HTTP methods: GET, POST

---

## 7. Other Requirements

### 7.1 Backup & Recovery

**REQ-01: Manual Backup**
- User bisa download config.json sebagai backup
- User bisa download assets folder sebagai backup

**REQ-02: Restore**
- User bisa upload config.json untuk restore

### 7.2 Documentation Requirements

**REQ-03: Developer Documentation**
- Setup guide
- Template creation guide
- Field type reference
- Deployment guide

**REQ-04: User Documentation**
- Login guide
- Edit content guide
- Image upload guide
- Screenshot untuk setiap step

---

## 8. Appendix

### 8.1 Sample config.json

```json
{
  "admin-password": "$2y$10$abcdefghijklmnopqrstuv",
  "_comment": "Password hash format depends on backend (bcrypt for PHP/Node, werkzeug for Flask)",
  "sitename": "My Awesome Website",
  "description": "A simple website built with Editable Static Web",
  "keywords": ["website", "profile", "business"],
  "pages": [
    {
      "title": "Home - My Awesome Website",
      "template": "home.html",
      "menu-title": "Home",
      "url": "/",
      "seo-description": "Welcome to my awesome website",
      "seo-keywords": ["home", "welcome"],
      "fields": [
        {
          "name": "hero-title",
          "type": "text",
          "label": "Hero Title",
          "value": "Welcome to Our Website"
        },
        {
          "name": "hero-description",
          "type": "textarea",
          "label": "Hero Description",
          "value": "We provide amazing services for your business"
        },
        {
          "name": "hero-image",
          "type": "image",
          "label": "Hero Background Image",
          "value": "/assets/images/hero-bg.jpg"
        }
      ]
    },
    {
      "title": "About Us - My Awesome Website",
      "template": "about.html",
      "menu-title": "About",
      "url": "/about",
      "fields": [
        {
          "name": "about-content",
          "type": "textarea",
          "label": "About Content",
          "value": "We are a company that..."
        }
      ]
    }
  ],
  "footer": {
    "content": [
      "Copyright © 2025 My Awesome Website. All rights reserved."
    ]
  }
}
```

### 8.2 Sample Template (home.html)

**Note:** Placeholder syntax tergantung implementation:
- Simple replacement: `{{field-name}}`
- Jinja2 (Flask): `{{ field_name }}`
- EJS (Node.js): `<%= fieldName %>`

**Example dengan simple placeholder:**

```html
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{page-title}}</title>
    <meta name="description" content="{{seo-description}}">
    <meta name="keywords" content="{{seo-keywords}}">
    <link rel="stylesheet" href="/assets/css/style.css">
</head>
<body>
    <header>
        <h1>{{sitename}}</h1>
        <nav>
            {{navigation}}
        </nav>
    </header>
    
    <section class="hero" style="background-image: url('{{hero-image}}')">
        <h1>{{hero-title}}</h1>
        <p>{{hero-description}}</p>
    </section>
    
    <footer>
        <p>{{footer}}</p>
    </footer>
</body>
</html>
```

### 8.3 Change Log

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-11-09 | Initial draft | IDA |

---

**End of Document**
