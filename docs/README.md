# WICARA CMS - Documentation Index

**Version**: 1.0.0
**Last Updated**: 2026-01-09

## 📚 Quick Navigation

### Getting Started
- **[Setup Guide](guides/SETUP_GUIDE.md)** - Installation, configuration, and deployment
- **[User Guide](guides/USER_GUIDE.md)** - End-user documentation for the admin panel

### Developer Resources
- **[Developer Guide](guides/DEVELOPER_GUIDE.md)** - Template creation, field types, and API reference
- **[Architecture](ARCHITECTURE.md)** - Technical architecture, design patterns, and system overview

### Project Management
- **[Backlog](BACKLOG.md)** - Development roadmap, feature status, and progress tracking

### Feature Specifications
- **[Engine-Content Separation](specs/ENGINE_CONTENT_SEPARATION.md)** - Plan for separating engine and user content
- **[Plugin System](specs/PHASE4_PLUGIN_SYSTEM.md)** - Plugin architecture and development guide
- **[Multi-site System](specs/PHASE5_MULTISITE_SYSTEM.md)** - Multi-site support implementation

### Reference Documentation
- **[Caching Strategy](reference/CACHING.md)** - Caching system documentation (Phase 2)
- **[Import/Export](reference/IMPORT_EXPORT_IMPLEMENTATION.md)** - Import/Export feature (Phase 3)

### Legacy Documents
- **[SRS](legacy/wicara-srs.md)** - Software Requirements Specification
- **[Vision](legacy/wicara-vision.md)** - Project vision and goals
- **[Content Summary](legacy/wicara-content-summary.md)** - Site identity and overview

---

## 📖 Documentation Structure

```
docs/
├── README.md                          # This file - documentation index
├── BACKLOG.md                         # Master development backlog
├── ARCHITECTURE.md                    # Technical architecture
│
├── guides/                            # User and developer guides
│   ├── SETUP_GUIDE.md                 # Installation & setup
│   ├── USER_GUIDE.md                  # End-user guide
│   └── DEVELOPER_GUIDE.md             # Developer documentation
│
├── specs/                             # Feature specifications
│   ├── ENGINE_CONTENT_SEPARATION.md   # ECS implementation plan
│   ├── PHASE4_PLUGIN_SYSTEM.md        # Plugin system spec
│   └── PHASE5_MULTISITE_SYSTEM.md     # Multi-site spec
│
├── reference/                         # Technical reference
│   ├── CACHING.md                     # Caching system reference
│   └── IMPORT_EXPORT_IMPLEMENTATION.md # Import/export reference
│
└── legacy/                            # Legacy/project documents
    ├── wicara-srs.md                  # Requirements specification
    ├── wicara-vision.md               # Project vision
    └── wicara-content-summary.md      # Content overview
```

---

## 🚀 Quick Start

### For Users
1. Read [Setup Guide](guides/SETUP_GUIDE.md) to install WICARA
2. Follow [User Guide](guides/USER_GUIDE.md) to manage your content

### For Developers
1. Read [Architecture](ARCHITECTURE.md) to understand the system
2. Follow [Developer Guide](guides/DEVELOPER_GUIDE.md) to extend functionality
3. Check [Backlog](BACKLOG.md) for contribution opportunities

---

## 📊 Project Status

**Overall Progress**: 90% Complete

| Component | Status | Documentation |
|-----------|--------|---------------|
| Core System | ✅ Complete | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Phase 1: Modular Architecture | ✅ Complete | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Phase 2: Caching Strategy | ✅ Complete | [reference/CACHING.md](reference/CACHING.md) |
| Phase 3: Import/Export System | ✅ Complete | [reference/IMPORT_EXPORT_IMPLEMENTATION.md](reference/IMPORT_EXPORT_IMPLEMENTATION.md) |
| Phase 4: Plugin System | 🚧 In Progress | [specs/PHASE4_PLUGIN_SYSTEM.md](specs/PHASE4_PLUGIN_SYSTEM.md) |
| Phase 5: Multi-site Support | ✅ Complete | [specs/PHASE5_MULTISITE_SYSTEM.md](specs/PHASE5_MULTISITE_SYSTEM.md) |
| Engine-Content Separation | 📋 Planned | [specs/ENGINE_CONTENT_SEPARATION.md](specs/ENGINE_CONTENT_SEPARATION.md) |

---

## 🎯 Key Features

- **Flat-file CMS**: No database required, all content in `config.json`
- **Modular Architecture**: Clean separation with blueprints and core modules
- **High Performance**: Multi-layer caching (50-80% improvement)
- **Portable**: Single file backup and restore
- **Extensible**: Plugin system for custom functionality
- **Multi-site Ready**: Support for multiple sites from one installation

---

## 📝 Documentation Guidelines

### Writing Documentation
1. **Keep it simple** - Clear, concise language
2. **Be specific** - Use exact file paths and line numbers
3. **Show examples** - Code snippets and sample configs
4. **Stay organized** - Use consistent formatting

### File Organization

#### **guides/** - How-to Documentation
- Step-by-step instructions
- User workflows
- Developer tutorials
- Examples: SETUP_GUIDE.md, USER_GUIDE.md, DEVELOPER_GUIDE.md

#### **specs/** - Feature Specifications
- Technical implementation plans
- Architecture decisions
- API specifications
- Examples: ENGINE_CONTENT_SEPARATION.md, PHASE4_PLUGIN_SYSTEM.md

#### **reference/** - Technical Reference
- System documentation
- Implementation details
- Configuration reference
- Examples: CACHING.md, IMPORT_EXPORT_IMPLEMENTATION.md

#### **legacy/** - Historical Documents
- Original project documents
- Requirements and vision
- Kept for historical reference
- Examples: wicara-srs.md, wicara-vision.md

### Updating the Backlog
- Use emojis: ✅ Complete, 🚧 In Progress, 📋 Planned
- Include file names and line counts
- Link to relevant documentation
- Update progress percentages

### Adding New Features
1. Create specification document in `docs/specs/` (if complex)
2. Add to BACKLOG.md with tracking status
3. Implement following architecture patterns
4. Update all related documentation
5. Add tests (if applicable)

---

## 🔍 Finding Information

### I want to...
- **Install WICARA**: → [guides/SETUP_GUIDE.md](guides/SETUP_GUIDE.md)
- **Edit content**: → [guides/USER_GUIDE.md](guides/USER_GUIDE.md)
- **Create templates**: → [guides/DEVELOPER_GUIDE.md](guides/DEVELOPER_GUIDE.md)
- **Understand the code**: → [ARCHITECTURE.md](ARCHITECTURE.md)
- **Add features**: → [BACKLOG.md](BACKLOG.md) → [guides/DEVELOPER_GUIDE.md](guides/DEVELOPER_GUIDE.md)
- **Report issues**: → Check [BACKLOG.md](BACKLOG.md) first
- **Contribute**: → [BACKLOG.md](BACKLOG.md) → "Contribution Guidelines"

---

## 📞 Support

### Documentation Issues
If you find errors or omissions in the documentation:
1. Check [BACKLOG.md](BACKLOG.md) for known issues
2. Update the documentation directly
3. Add a task to BACKLOG.md if it's a larger issue

### Technical Issues
- Check [guides/SETUP_GUIDE.md](guides/SETUP_GUIDE.md) troubleshooting section
- Review [ARCHITECTURE.md](ARCHITECTURE.md) for design patterns
- See [guides/USER_GUIDE.md](guides/USER_GUIDE.md) for common tasks

---

## 🗂️ Document Descriptions

### Guides (`guides/`)
| Document | Description | Audience |
|----------|-------------|----------|
| [SETUP_GUIDE.md](guides/SETUP_GUIDE.md) | Installation, configuration, deployment | Users, Developers |
| [USER_GUIDE.md](guides/USER_GUIDE.md) | Admin panel usage, content management | Users |
| [DEVELOPER_GUIDE.md](guides/DEVELOPER_GUIDE.md) | Templates, field types, API, CLI | Developers |

### Specifications (`specs/`)
| Document | Description | Status |
|----------|-------------|--------|
| [ENGINE_CONTENT_SEPARATION.md](specs/ENGINE_CONTENT_SEPARATION.md) | ECS implementation plan | 📋 Planned |
| [PHASE4_PLUGIN_SYSTEM.md](specs/PHASE4_PLUGIN_SYSTEM.md) | Plugin system (70% complete) | 🚧 In Progress |
| [PHASE5_MULTISITE_SYSTEM.md](specs/PHASE5_MULTISITE_SYSTEM.md) | Multi-site support | ✅ Complete |

### Reference (`reference/`)
| Document | Description | Phase |
|----------|-------------|-------|
| [CACHING.md](reference/CACHING.md) | Cache system implementation | Phase 2 |
| [IMPORT_EXPORT_IMPLEMENTATION.md](reference/IMPORT_EXPORT_IMPLEMENTATION.md) | Import/export feature | Phase 3 |

### Legacy (`legacy/`)
| Document | Description | Type |
|----------|-------------|------|
| [wicara-srs.md](legacy/wicara-srs.md) | Software requirements | Historical |
| [wicara-vision.md](legacy/wicara-vision.md) | Project vision | Historical |

---

## 📈 Version History

### v1.0.0 (2026-01-09)
- Initial documentation structure
- Added ARCHITECTURE.md
- Reorganized BACKLOG.md
- Created documentation index
- Organized files into guides/, specs/, reference/, legacy/

---

*Last Updated: 2026-01-09*
*Documentation Version: 1.0.0*
