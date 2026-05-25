# Changelog — edifice-mission-report

All notable changes to this plugin are documented here.

## Versioning convention

`0.MINOR.PATCH` (pré-1.0) :
- **PATCH** (`0.x.Y+1`) — bugfix, ajout de champ optionnel, amélioration interne sans impact sur l'interface
- **MINOR** (`0.X+1.0`) — changement d'interface utilisateur : nouveau champ obligatoire dans le JSON, renommage de commande CLI, changement de comportement observable

Règle : les refactors internes (changement de librairie, restructuration code) qui ne modifient pas l'interface publique → PATCH, pas MINOR.

---

## [0.6.2] — 2026-05-25 — EXIF auto-rotation fix

### Fixed
- `render_diagnostic.py` + `render_cr_visite.py` — photos are now auto-rotated based on
  EXIF orientation tag before being embedded as `InlineImage`. Fixes Android photos displayed
  sideways in generated DOCX reports. Uses `PIL.ImageOps.exif_transpose` (Pillow already
  required by docxtpl). No-op if EXIF tag is absent or already correct.

---

## [0.5.0] — 2026-05-19 — Note assessment schema v1 + MCP-first refactor

### Changed (interface)
- `/edifice pull` now calls the **hal-mcp** `get_mission_with_assets` tool
  directly and downloads photos via signed URLs. The Python script
  `pull_mission.py` is removed.
- `/edifice push` now calls the **hal-mcp** `push_mission_context` tool. The
  Python script `push_mission.py` is removed.
- Unified vocabulary on `observations[]`: `desordre`/`observation` →
  `description`, `ie` → `assessment`, `etage_facade`/`localisation` →
  `location`. Renderers keep fallbacks for legacy keys.

### Added
- `download_photos.py` — stdlib-only helper that downloads photos from
  `context.json` signed URLs.
- `organizations/ic-ingenieurs/assessment-config.json` — single source of
  truth for the `assessment` values per service_type.

### Removed
- `pull_mission.py`, `push_mission.py` — replaced by MCP tools.

### Schema
- Migration `20260519000000_note_assessment_zone.sql` (edifice repo) adds
  `zone` + `assessment` columns to `edifice_notes`, backfilled from
  `metadata`.

---

## [0.4.1] — 2026-05-18 — Complete docxtpl migration + service_type uniformity

### Changed
- `render_cr_visite.py` — rewritten as lean docxtpl runner (~70 lines vs 220). Eliminates all
  programmatic python-docx table manipulation, XML shading, and EXIF rotation.
- `render_devis.py` — `titre_service` renamed to `service_type` to match template and other renderers.
- `templates/ic-ingenieurs/suivi_chantier.docx` — manually updated: Jinja2 `{%tr for %}` loops
  for participants and observations, IC branded header/footer, `date_rapport` in header.
- `templates/ic-ingenieurs/devis.docx` — `{{ titre_service }}` → `{{ service_type }}`.

### Architecture
All 3 renderers (`render_diagnostic.py`, `render_cr_visite.py`, `render_devis.py`) are now lean
docxtpl runners with the same pattern. `service_type` is now the uniform variable name across all
3 templates. Template layout is fully owned by Word, not Python.

### Known trade-off
`InlineImage` does not apply EXIF rotation. Photos from Android are displayed as-stored; Word and
LibreOffice apply EXIF at render time. The old python-docx code handled this in Python — no longer needed
for modern viewers.

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
