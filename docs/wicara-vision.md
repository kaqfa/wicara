# Software Vision: Editable Static Web

## 1. Pendahuluan

### 1.1 Latar Belakang
Di era digital saat ini, banyak individu dan usaha kecil yang membutuhkan website profile sederhana namun tetap bisa dikelola sendiri tanpa harus memahami coding. Di sisi lain, CMS tradisional seperti WordPress seringkali terlalu kompleks, berat, dan membutuhkan database yang membuat hosting menjadi lebih mahal.

Ada gap di tengah: antara website statis murni (yang cepat tapi tidak bisa diedit) dengan CMS full-blown (yang powerful tapi overkill untuk kebutuhan sederhana).

### 1.2 Problem Statement
**Target Users:** 
- Developer yang ingin membuat website profile untuk klien dengan maintenance minimal
- Small business owner yang butuh website sederhana dan bisa update konten sendiri
- Individu yang ingin punya website personal tanpa ribet setup database

**Pain Points yang Diselesaikan:**
- Website statis tidak bisa diedit tanpa coding
- CMS tradisional terlalu kompleks untuk kebutuhan sederhana
- Hosting database menambah biaya dan kompleksitas
- Update konten butuh developer untuk website statis
- Backup dan migrasi website yang ribet

### 1.3 Product Vision
**Editable Static Web** adalah flat-file CMS minimalis yang memungkinkan pembuatan website profile dengan konten yang dapat diedit melalui admin panel sederhana, tanpa memerlukan database. Semua konten disimpan dalam single JSON file yang mudah di-backup dan dipindahkan.

**Tagline:** *"Static Speed, Dynamic Content - No Database Required"*

## 2. Target Users & Use Cases

### 2.1 Primary Users

**Developer/Web Designer**
- Membuat website profile untuk klien
- Menentukan bagian mana yang editable oleh klien
- Deploy dan handover ke klien dengan mudah

**End User/Client (Non-Technical)**
- Mengupdate konten website melalui admin panel
- Mengganti teks, gambar, dan informasi kontak
- Tidak perlu memahami HTML/CSS/PHP

### 2.2 Core Use Cases

**UC-01: Setup Website Baru**
1. Developer membuat template HTML statis
2. Developer setup config.json dengan struktur minimal
3. Developer meeting dengan klien untuk identifikasi editable fields
4. Developer menambahkan fields ke config.json
5. Developer mengubah template HTML menjadi dynamic dengan placeholder

**UC-02: Edit Konten Website**
1. User login ke admin panel
2. User memilih halaman yang ingin diedit
3. User mengubah konten melalui form
4. User menyimpan perubahan
5. Perubahan langsung terlihat di website

**UC-03: Upload/Ganti Gambar**
1. User masuk ke admin panel
2. User memilih field image yang ingin diganti
3. User upload gambar baru
4. Sistem menyimpan gambar dan update path di config.json
5. Gambar baru langsung muncul di website

**UC-04: Backup & Restore**
1. User download config.json
2. User simpan sebagai backup
3. Jika perlu restore, user upload kembali config.json lama

## 3. Key Features

### 3.1 Core Features (MVP)

**F-01: Single File Configuration**
- Semua data website tersimpan dalam config.json
- Mudah di-backup (tinggal download 1 file)
- Mudah di-migrate (copy-paste file)

**F-02: Template-Based Rendering**
- Template HTML dengan placeholder syntax `{{field-name}}`
- Dynamic content injection saat page load
- Support multiple pages dengan template berbeda

**F-03: Admin Panel**
- Simple authentication dengan password di config.json
- List semua pages yang bisa diedit
- Form auto-generate dari fields di config.json
- Preview changes (optional untuk v2)

**F-04: Field Types Support**
- Text: single line input
- Textarea: multi-line text input
- Image: file upload dengan preview

**F-05: Zero Database**
- Pure file-based system
- Tidak butuh MySQL/PostgreSQL/SQLite
- File I/O langsung ke config.json

### 3.2 Technical Features

**TF-01: Lightweight**
- Native PHP tanpa framework
- Minimal dependencies
- Fast page load

**TF-02: Portable**
- Bisa jalan di shared hosting murah
- Tidak butuh special server configuration
- Easy deployment (upload via FTP)

**TF-03: Secure**
- Password encryption dengan PHP native
- Session-based authentication
- File upload validation

## 4. Success Metrics

### 4.1 Technical Metrics
- Page load time < 500ms
- Admin panel response time < 1s
- File size config.json < 100KB untuk website 5 halaman
- Compatibility: PHP 7.4+

### 4.2 User Metrics
- Setup time untuk developer: < 30 menit
- Learning curve untuk end user: < 10 menit
- Content update time: < 2 menit per field

## 5. Scope & Limitations

### 5.1 In Scope (V1)
- Profile/landing page website
- 5-10 halaman maksimal
- Basic content editing (text, textarea, image)
- Single admin user
- Simple authentication

### 5.2 Out of Scope (V1)
- Multi-user management
- Blog/dynamic content dengan pagination
- Database integration
- Advanced WYSIWYG editor
- Form submission handling
- E-commerce features
- Multi-language support
- Version control/history

### 5.3 Future Considerations (V2+)
- WYSIWYG editor integration
- Multi-user dengan role management
- Content versioning
- Template marketplace
- Plugin system
- Form builder & submission handler

## 6. Differentiators

**vs WordPress:**
- ✅ Jauh lebih ringan dan cepat
- ✅ No database required
- ✅ Lebih secure (minimal attack surface)
- ✅ Mudah backup & migrate
- ❌ Tidak se-flexible WordPress
- ❌ No plugin ecosystem

**vs Static Site Generator (Hugo, Jekyll):**
- ✅ User bisa edit tanpa rebuild
- ✅ No technical knowledge required
- ✅ Real-time update
- ❌ Not purely static
- ❌ Butuh PHP hosting

**vs Headless CMS (Strapi, Contentful):**
- ✅ Self-hosted, no vendor lock-in
- ✅ Jauh lebih simple
- ✅ Zero configuration
- ❌ No API
- ❌ Limited scalability

## 7. Technical Architecture (High Level)

### 7.1 System Components
```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       ├─────────────┐
       │             │
       v             v
┌──────────┐   ┌──────────┐
│  Public  │   │  Admin   │
│  Pages   │   │  Panel   │
└────┬─────┘   └────┬─────┘
     │              │
     └──────┬───────┘
            v
    ┌───────────────┐
    │   Backend     │
    │   Handlers    │
    └───────┬───────┘
            │
            v
    ┌───────────────┐
    │  config.json  │
    └───────────────┘
```

### 7.2 Tech Stack Options

**Backend Options:**
- **PHP Native:** Mudah deploy di shared hosting, zero dependency
- **Python Flask:** Clean code structure, Jinja2 templating
- **Node.js Express:** Modern, npm ecosystem, async by default

**Frontend:**
- HTML5, CSS3, Vanilla JS (minimal)
- Optional: Alpine.js / Petite Vue untuk interaktivitas ringan

**Data Storage:**
- JSON file (single source of truth)

**Server:**
- Development: Built-in server (PHP/Flask/Node)
- Production: Apache/Nginx sebagai reverse proxy atau static server

**Deployment:**
- Simple: FTP/SFTP upload
- Modern: Git-based deployment, Docker (optional)

## 8. Development Roadmap

### Phase 1: MVP (2-3 hari)
- Core functions (load/save JSON)
- Public page rendering
- Basic admin panel
- Text & textarea fields
- Simple authentication

### Phase 2: Polish (1-2 hari)
- Image upload feature
- Better admin UI
- Error handling
- Input validation
- Documentation

### Phase 3: Testing & Refinement (1 hari)
- End-to-end testing
- Performance optimization
- Security hardening
- User guide creation

## 9. Risks & Mitigations

### R-01: Concurrent Edit Conflicts
**Risk:** Dua user edit bersamaan, data tertimpa
**Mitigation:** V1 - single user only. V2 - implement file locking

### R-02: File Corruption
**Risk:** config.json corrupt saat save
**Mitigation:** Backup otomatis sebelum save, validation sebelum write

### R-03: Security Vulnerabilities
**Risk:** File upload exploit, unauthorized access
**Mitigation:** 
- Whitelist file types
- File size limit
- Path traversal protection
- Session timeout

### R-04: Scalability Limit
**Risk:** Tidak cocok untuk website besar
**Mitigation:** Clear documentation tentang use case yang tepat

## 10. Conclusion

Editable Static Web mengisi gap antara website statis murni dengan CMS kompleks. Produk ini cocok untuk profile website, landing page, dan website sederhana yang butuh content management tanpa kompleksitas database dan framework berat.

Dengan fokus pada simplicity, portability, dan ease of use, produk ini memberikan solusi praktis bagi developer yang ingin delivery website yang mudah di-maintain oleh client non-technical.
