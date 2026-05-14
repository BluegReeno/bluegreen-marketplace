# Changelog — edifice-mission-report

All notable changes to this plugin are documented here.

---

## [0.4.0] — 2026-05-14 — Migrate DOCX renderers to docxtpl + IC branded templates

### Changed
- `render_diagnostic.py` — rewritten as lean docxtpl runner (~90 lines vs 829). Eliminates all programmatic python-docx layout code.
- `render_devis.py` — rewritten as lean docxtpl runner (~90 lines vs 651). Same elimination.
- `render_cr_visite.py` — template path updated to `templates/ic-ingenieurs/suivi_chantier.docx`. No other changes; table lookup now robust to cover table additions.
- `render_report.py` — added `normalize_v1()` (v1.0→v2.0 context upgrade), `_template_path()` (org-aware path resolution), `--org` CLI flag, `org=None` param in `render()`.
- `requirements.txt` — `docxtpl>=0.18` + `Pillow>=10.0` only. Removed `supabase`, `python-docx`, `pyyaml`.
- `skills/edifice/SKILL.md` — updated `/edifice report` uv run command to `--with "docxtpl>=0.18"`.

### Added
- `templates/ic-ingenieurs/diagnostic.docx` — IC branded Word template with disorder loop (`{%tr for d in disorders %}`), photos (InlineImage), header bar per disorder.
- `templates/ic-ingenieurs/devis.docx` — IC branded devis template with section loops (documents_fournis, observations, chiffrage).
- `templates/ic-ingenieurs/suivi_chantier.docx` — existing template moved from root + IC branding applied (cover, Heading styles).
- `templates/blue-green/.gitkeep` — org placeholder for future Blue Green templates.
- `scripts/prepare_diagnostic_template.py` — reproducibility: generates `diagnostic.docx` from MyClaudeSkills source.
- `scripts/create_devis_template.py` — reproducibility: generates `devis.docx` from scratch.
- `scripts/update_suivi_chantier_branding.py` — reproducibility: applies IC branding to `suivi_chantier.docx`.

### Architecture
Laurent (IC Ingénieurs Conseils) can now edit DOCX layouts directly in Word without touching Python code. Org override via `--org` flag or `EDIFICE_ORG` env var (default: `ic-ingenieurs`).

---

## [0.3.4] — 2026-05-13 — Bugfix: YAML frontmatter quote stripping

### Fixed
- `parse_yaml_frontmatter` now strips surrounding quotes from values (e.g. `supabase_url: "https://..."` was parsed with quotes included, breaking HTTP calls)

---

## [0.3.3] — 2026-05-13 — Initial marketplace publish

First publication to `bluegreen-marketplace`.

### What's included
- `/edifice pull` — pull mission data via `pull_mission.py` (stdlib urllib — no SDK required)
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
