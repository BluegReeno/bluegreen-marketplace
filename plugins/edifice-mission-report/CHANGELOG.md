# Changelog — edifice-mission-report

All notable changes to this plugin are documented here.

---

## [0.3.3] — 2026-05-13 — Initial marketplace publish

First publication to `bluegreen-marketplace`.

### What's included
- `/edifice pull` — pull mission data via `pull_mission.py` (Supabase SDK + refresh token)
- `/edifice pull` also supports `get_mission_with_assets` MCP tool (hal-mcp Phase 1)
- `/edifice improve` — AI-assisted observation enrichment
- `/edifice report` — generate DOCX report (diagnostic / suivi_chantier / devis)
- `/edifice push` — push updated notes back to Supabase
- `/edifice pair` — OAuth 2.0 device flow laptop pairing

### Supabase tables read
`edifice_projects`, `edifice_buildings`, `edifice_notes`, `edifice_photos`

### Supabase tables written
`edifice_notes` (push only)

---

## Upcoming

### [0.4.0] — planned
- `/edifice pull` fully migrated to hal-mcp `get_mission_with_assets` (no Supabase SDK required)
- `pull_mission.py` kept for backward compat / Cowork sandbox
