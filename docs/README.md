# Wicara CMS Documentation

This directory contains all project-level documentation for Wicara CMS.

## Quick Navigation

- [Architecture](ARCHITECTURE.md)
- [Backlog](BACKLOG.md)
- [Developer Guide](guides/DEVELOPER_GUIDE.md)
- [User Guide](guides/USER_GUIDE.md)
- [Setup Guide](guides/SETUP_GUIDE.md)
- [Migration Guide](guides/MIGRATION_GUIDE.md)

## Directory Layout

```
docs/
|-- README.md
|-- ARCHITECTURE.md
|-- BACKLOG.md
|-- PLUGIN_CLI_GUIDE.md
|-- ECS_CORE_INTEGRATION_IMPLEMENTATION.md
|-- guides/
|-- specs/
|-- reference/
|-- legacy/
`-- archive/
```

## What Goes Where

- `guides/`: user and developer how-to documentation
- `specs/`: design specs, plans, and proposal documents
- `reference/`: technical implementation reference docs
- `legacy/`: historical project artifacts kept for context
- `archive/`: completed delivery reports, implementation summaries, and superseded docs

## Archived Reports

The `archive/` folder contains one-time implementation outputs and reports that are preserved for traceability but are not part of the active docs set.

## Notes

- Keep `README.md` at project root for primary project onboarding.
- Keep `AGENTS.md` and `CLAUDE.md` at project root for agent/editor instructions.
- Component-local docs remain in place (for example `scripts/README.md` and plugin `README.md` files).
