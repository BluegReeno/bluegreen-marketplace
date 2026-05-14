# Feature: docx-renderer-refonte

## Goal
Migrate edifice-mission-report DOCX renderers from programmatic python-docx to docxtpl + branded Word templates.

## Context
- **Plan**: `.agents/plans/docx-renderer-refonte-implementation.md`
- **Plugin dir**: `plugins/edifice-mission-report/`
- **Source template**: `/Users/renaud/Projects/MyClaudeSkills/document-generator/organizations/ic-ingenieurs/templates/rapport-diag-template.docx`

## Tasks

### Phase 1: Directory structure + render_report.py
- [x] Create `templates/ic-ingenieurs/` and `templates/blue-green/` directories ✓ 2026-05-14
- [x] Move `templates/suivi_chantier.docx` → `templates/ic-ingenieurs/suivi_chantier.docx` ✓ 2026-05-14
- [x] Update `render_report.py` — `_template_path()`, `normalize_v1()`, `--org` flag ✓ 2026-05-14

### Phase 2: Template preparation scripts
- [x] Create `scripts/prepare_diagnostic_template.py` — hybrid diagnostic template ✓ 2026-05-14
- [x] Run `prepare_diagnostic_template.py` → `templates/ic-ingenieurs/diagnostic.docx` ✓ 2026-05-14
- [x] Create `scripts/create_devis_template.py` — devis template from scratch ✓ 2026-05-14
- [x] Run `create_devis_template.py` → `templates/ic-ingenieurs/devis.docx` ✓ 2026-05-14
- [x] Create `scripts/update_suivi_chantier_branding.py` — IC branding for suivi_chantier ✓ 2026-05-14
- [x] Run `update_suivi_chantier_branding.py` ✓ 2026-05-14

### Phase 3: Renderer migration
- [x] Rewrite `render_diagnostic.py` — lean docxtpl runner ✓ 2026-05-14
- [x] Rewrite `render_devis.py` — lean docxtpl runner ✓ 2026-05-14

### Phase 4: Cleanup
- [x] Update `render_cr_visite.py` — template path + table lookup fix ✓ 2026-05-14
- [x] Update `requirements.txt` — docxtpl>=0.18 + Pillow>=10.0 ✓ 2026-05-14
- [x] Update `skills/edifice/SKILL.md` — uv run command ✓ 2026-05-14

### Phase 5: Validate + version bump
- [x] Level 1: All imports pass ✓ 2026-05-14
- [x] Level 2: No python-docx/lxml in migrated renderers ✓ 2026-05-14
- [x] Level 3: All template files exist ✓ 2026-05-14
- [x] Level 4: Template variables check ✓ 2026-05-14
- [x] Level 5: Diagnostic render test (real mission data, 10 disorders, 46MB) ✓ 2026-05-14
- [x] Level 6: Version parity check ✓ 2026-05-14
- [x] Bump `plugin.json` + `marketplace.json` to v0.4.0 ✓ 2026-05-14
- [x] Add CHANGELOG.md entry for v0.4.0 ✓ 2026-05-14

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `templates/ic-ingenieurs/` | Create dir | Org-based template directory |
| `templates/blue-green/.gitkeep` | Create | Placeholder |
| `templates/ic-ingenieurs/diagnostic.docx` | Create via script | Hybrid template |
| `templates/ic-ingenieurs/devis.docx` | Create via script | Devis template |
| `templates/ic-ingenieurs/suivi_chantier.docx` | Move from root | |
| `scripts/prepare_diagnostic_template.py` | Create | Template generation |
| `scripts/create_devis_template.py` | Create | Template generation |
| `scripts/update_suivi_chantier_branding.py` | Create | Branding update |
| `render_report.py` | Modify | Add normalize_v1, _template_path, --org |
| `render_diagnostic.py` | Rewrite | docxtpl runner |
| `render_devis.py` | Rewrite | docxtpl runner |
| `render_cr_visite.py` | Modify | Path update only |
| `requirements.txt` | Modify | docxtpl>=0.18 + Pillow>=10.0 |
| `skills/edifice/SKILL.md` | Modify | uv run command update |

## Notes
- bluegreen-marketplace IS the source of truth (not edifice)
- render_cr_visite.py stays with python-docx — path update only
- scripts/ are reproducibility artifacts, not runtime deps

## Completion
- **Started**: 2026-05-14
- **Completed**: 2026-05-14
- **Commit**: feat: migrate DOCX renderers to docxtpl + IC branded templates (v0.4.0)
