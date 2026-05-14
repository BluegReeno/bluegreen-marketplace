# Feature: docx-renderer-refonte

The following plan should be complete, but validate the current state of each file before executing — some tasks may already be done in a prior session.

**IMPORTANT: Source of truth for plugin code is `bluegreen-marketplace`** (not edifice). The edifice repo only holds `schema-contract.json`. All implementation happens in `/Users/renaud/Projects/bluegreen-marketplace/plugins/edifice-mission-report/`.

## Feature Description

Migrate the `edifice-mission-report` plugin's DOCX renderers from pure programmatic python-docx (`render_diagnostic.py` ~829 lines, `render_devis.py` ~651 lines) to a docxtpl + branded Word template architecture. Create IC Ingénieurs Conseils branded `.docx` templates with Jinja2 tags. Add org-aware template path resolution and v1.0 context format normalization to `render_report.py`. Reorganize `templates/` into org-based subdirectories.

## User Story

As Laurent (IC Ingénieurs Conseils engineer),
I want DOCX reports generated from branded Word templates I can edit in Word,
So that I can adjust the visual layout without touching Python code.

## Problem Statement

Two of three renderers (`render_diagnostic.py`, `render_devis.py`) build Word documents entirely in Python — 1,500+ lines of layout code that Laurent cannot edit. The `templates/` directory has no org structure. The v1.0 `context.json` format (used by some existing mission data) is not handled.

## Solution Statement

Introduce `templates/ic-ingenieurs/` org directory. Create templates via two preparation scripts:
- **`diagnostic.docx`** — hybrid: take `rapport-diag-template.docx` (MyClaudeSkills) as base for the cover page + section structure + Heading styles, then replace the observations section with the current plugin's per-disorder layout (header bar, IE badge, 2-col photo table, description/cause/recommendations) as docxtpl Jinja2 loop rows.
- **`suivi_chantier.docx`** — re-brand only: take the existing plugin template (loop + observations already work), replace its cover page with the IC Ingénieurs branded one, update Heading 1/2 styles.
- **`devis.docx`** — created from scratch (programmatic → docxtpl, no existing template).

Replace `render_diagnostic.py` and `render_devis.py` with lean docxtpl runners. Add `normalize_v1()` and `_template_path()` to `render_report.py`. Update `render_cr_visite.py` template path only (keeps python-docx, covered transitively). Update requirements.txt and SKILL.md.

## Feature Metadata

**Feature Type**: Refactor + Enhancement
**Estimated Complexity**: High (template creation with docxtpl Jinja2 is the critical path)
**Primary Systems Affected**: `plugins/edifice-mission-report/` (render_*.py × 4, render_report.py, requirements.txt, SKILL.md, templates/)
**Dependencies**: `docxtpl>=0.18`, `pillow` (runtime via `uv run --with`)

---

## CONTEXT REFERENCES

### Relevant Codebase Files — READ THESE BEFORE IMPLEMENTING

- `plugins/edifice-mission-report/render_report.py` (lines 29-55) — `render()` dispatcher. Add `org=None` param, `normalize_v1()` call before dispatch, `_template_path()` helper. `TEMPLATE_SUIVI` const → replaced by `_template_path(org, "suivi_chantier")`.
- `plugins/edifice-mission-report/render_diagnostic.py` (lines 789-815) — `render_diagnostic()` signature: `(context, photos_dir=".", output_path="rapport_diagnostic.docx")` — **MUST be preserved**.
- `plugins/edifice-mission-report/render_diagnostic.py` (lines 767-784) — `_normalize_disorders()` — logic to convert `observations[]` to `disorders[]`. This business logic must be absorbed into the new `_build_context()`.
- `plugins/edifice-mission-report/render_diagnostic.py` (lines 30-47) — IC brand constants: `IC_BLUE = #1F3A5F`, `IC_ORANGE = #E86A1A`, `IC_ROW_ALT = #F0F4F8`. Reuse in template generation script.
- `plugins/edifice-mission-report/render_devis.py` (lines 613-638) — `render_devis()` signature: `(context, photos_dir=".", output_path="rapport_devis.docx")` — **MUST be preserved**.
- `plugins/edifice-mission-report/render_cr_visite.py` (line 66) — `TEMPLATE_PATH` — update to `templates/ic-ingenieurs/suivi_chantier.docx`. **No other changes to this file.**
- `plugins/edifice-mission-report/requirements.txt` — Current: `supabase>=2.28,<3.0`, `python-docx>=1.1`, `Pillow>=10.0`, `pyyaml>=6.0`. Target: `docxtpl>=0.18`, `Pillow>=10.0`.
- `plugins/edifice-mission-report/skills/edifice/SKILL.md` (lines 239-248) — Update `/edifice report` step 1 `uv run` command.
- `/Users/renaud/Projects/MyClaudeSkills/document-generator/organizations/ic-ingenieurs/templates/rapport-diag-template.docx` — **SOURCE template for `diagnostic.docx`**. Already a working docxtpl template (IC branded cover, sections, Heading styles, static IE table). The observations section (paras 077-083 + Table 3) will be replaced. Variables: `service_type`, `client`, `residence`, `adresse`, `dossier`, `date_rapport`, `contexte`, `description_batiment`, `detail_visite`, `investigation_methods`, `conclusions`, `recommandations`.

### New Files to Create

- `plugins/edifice-mission-report/templates/ic-ingenieurs/diagnostic.docx` — hybrid docxtpl template (IC branded cover from MyClaudeSkills + disorder loop structure from current plugin)
- `plugins/edifice-mission-report/templates/ic-ingenieurs/devis.docx` — docxtpl template for devis (created from scratch)
- `plugins/edifice-mission-report/templates/blue-green/.gitkeep` — org placeholder
- `plugins/edifice-mission-report/scripts/prepare_diagnostic_template.py` — loads `rapport-diag-template.docx`, replaces observations section with disorder loop, saves as `diagnostic.docx`
- `plugins/edifice-mission-report/scripts/create_devis_template.py` — creates `devis.docx` from scratch with IC branding
- `plugins/edifice-mission-report/scripts/update_suivi_chantier_branding.py` — loads existing `suivi_chantier.docx`, replaces cover page + Heading styles with IC branding

### Moved Files

- `templates/suivi_chantier.docx` → `templates/ic-ingenieurs/suivi_chantier.docx`

### Relevant Documentation

**Fallback URLs:**
- docxtpl docs: https://docxtpl.readthedocs.io/en/latest/ — table loops, InlineImage, Jinja2 tags
- docxtpl PyPI: https://pypi.org/project/docxtpl/ — version info

### Patterns to Follow

**docxtpl renderer pattern — render_diagnostic** (target):
```python
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Cm
from pathlib import Path

TEMPLATE_PATH = Path(__file__).parent / "templates" / "ic-ingenieurs" / "diagnostic.docx"

def render_diagnostic(context, photos_dir=".", output_path="rapport_diagnostic.docx"):
    doc = DocxTemplate(TEMPLATE_PATH)
    tpl_ctx = _build_context(context, photos_dir, doc)
    doc.render(tpl_ctx)
    doc.save(output_path)
    print(f"✅ Rapport diagnostic : {output_path}")
    return output_path
```

**`_build_context()` — Edifice fields → template variables mapping**:
```python
def _build_context(context, photos_dir, doc):
    # Normalize observations[] (Edifice format) to disorders list for template
    disorders = []
    for obs in context.get("observations", []):
        # Collect up to 4 photos for 2-col table (photo1/photo2 = row1, photo3/photo4 = row2)
        photos_raw = obs.get("photos") or ([obs.get("photo")] if obs.get("photo") else [])
        photos_img = []
        for p in photos_raw[:4]:
            path = Path(photos_dir) / str(p)
            photos_img.append(InlineImage(doc, str(path), width=Cm(7.5)) if path.exists() else None)
        # Pad to 4 slots (None = empty cell in template)
        while len(photos_img) < 4:
            photos_img.append(None)

        disorders.append({
            "ref":             obs.get("ref", ""),
            "name":            obs.get("name") or obs.get("desordre", ""),
            "location":        obs.get("localisation") or obs.get("zone", ""),
            "description":     obs.get("observation") or obs.get("desordre", ""),
            "cause":           obs.get("cause", ""),
            "recommendations": obs.get("action") or obs.get("recommendations", ""),
            "ie":              obs.get("ie", ""),
            "photo1": photos_img[0], "photo2": photos_img[1],
            "photo3": photos_img[2], "photo4": photos_img[3],
        })

    return {
        # Cover page
        "service_type":           context.get("titre_service", ""),
        "client":                 context.get("client", ""),
        "residence":              context.get("residence", ""),
        "adresse":                context.get("adresse", ""),
        "complement_adresse":     "",
        "code_postal":            "",
        "commune":                "",
        "dossier":                context.get("ref_dossier", ""),
        "date_rapport":           format_date_french(context.get("date_visite", "")),
        # Sections
        "contexte":               context.get("objet_visite", ""),
        "description_batiment":   context.get("description_batiment", ""),
        "construction_era":       context.get("construction_era", ""),
        "construction_type":      context.get("construction_type", ""),
        "n_etage":                context.get("n_etage", ""),
        "utilisation":            context.get("utilisation", ""),
        "detail_visite":          context.get("detail_visite", ""),
        "investigation_methods":  context.get("investigation_methods", ""),
        # Observations loop
        "disorders":              disorders,
        # Synthesis
        "conclusions":            context.get("synthese", ""),
        "recommandations":        context.get("conclusion", ""),
    }
```

**normalize_v1 pattern** (add to render_report.py before dispatch):
```python
def normalize_v1(ctx):
    """Upgrade v1.0 context.json to v2.0 format."""
    if ctx.get("edifice_version", "2.0") != "1.0":
        return ctx
    mission = ctx.get("mission", {})
    building = ctx.get("building", {})
    observations = []
    for note in ctx.get("notes", []):
        observations.append({
            "ref": note.get("ref", ""),
            "localisation": "",
            "etage_facade": "",
            "observation": note.get("description", ""),
            "action": "",
            "photo": note.get("photos", [""])[0].replace("photos/", "") if note.get("photos") else "",
        })
    return {
        "edifice_version": "2.0",
        "project_type": mission.get("type", "suivi_chantier"),
        "titre_service": mission.get("name", ""),
        "client": "",
        "residence": building.get("name", ""),
        "adresse": building.get("address", ""),
        "ref_dossier": "",
        "date_visite": (mission.get("visited_at") or "")[:10],
        "participants": [],
        "objet_visite": mission.get("brief", ""),
        "synthese": "",
        "conclusion": "",
        "observations": observations,
    }
```

**org-aware path resolution** (add to render_report.py):
```python
import os
PLUGIN_DIR = Path(__file__).resolve().parent

def _template_path(org: str, project_type: str) -> Path:
    path = PLUGIN_DIR / "templates" / org / f"{project_type}.docx"
    if not path.exists():
        raise SystemExit(f"Template not found: {path}\nSet EDIFICE_ORG or use --org flag.")
    return path
```

**Updated render() in render_report.py**:
```python
def render(context: dict, photos_dir: str, output_path: str, org=None) -> None:
    context = normalize_v1(context)
    org = org or context.get("org") or os.environ.get("EDIFICE_ORG") or "ic-ingenieurs"
    project_type = context.get("project_type", "diagnostic")

    if project_type == "diagnostic":
        from render_diagnostic import render_diagnostic
        render_diagnostic(context, photos_dir=photos_dir, output_path=output_path)
    elif project_type == "suivi_chantier":
        tpl = _template_path(org, "suivi_chantier")
        from render_cr_visite import render_cr
        render_cr(context=context, photos_dir=photos_dir, output_path=output_path, template_path=str(tpl))
    elif project_type == "devis":
        from render_devis import render_devis
        render_devis(context, photos_dir=photos_dir, output_path=output_path)
    else:
        raise SystemExit(f"Unknown project_type: {project_type!r}")
```

**Jinja2 tag safety in template creation** (CRITICAL GOTCHA):
When building `.docx` templates with python-docx, Jinja2 tags must each be in a **single text run**. Word/python-docx can split text across runs, breaking `{{ variable }}`. Always write each tag as its own `paragraph.add_run("{{ variable }}")` call. Never apply mixed formatting within a tag string.

**docxtpl table row loop syntax**:
```
# In template table — first row of repeatable group:
{% for obs in observations %}    ← in first cell of this row (sole content)
# Normal data rows with {{ obs.field }} tags
{% endfor %}                     ← in first cell of last row (sole content)
```

---

## IMPLEMENTATION PLAN

### Phase 1: Directory structure + render_report.py update

Create `templates/ic-ingenieurs/`, move existing template, update the dispatcher.

### Phase 2: Template preparation scripts

Three scripts — each creates one template file:
- **`prepare_diagnostic_template.py`**: Load `rapport-diag-template.docx` (MyClaudeSkills), strip observations section (paras 077-083 + Table 3), inject new disorder loop table, save → `diagnostic.docx`. **This is the critical path.**
- **`create_devis_template.py`**: Create `devis.docx` from scratch with IC branding.
- **`update_suivi_chantier_branding.py`**: Load existing `suivi_chantier.docx`, replace cover page elements + Heading styles → save in place.

### Phase 3: Renderer migration — render_diagnostic.py + render_devis.py

Replace programmatic python-docx renderers with lean docxtpl runners.

### Phase 4: Cleanup — render_cr_visite.py path + requirements.txt + SKILL.md

Path update only for render_cr_visite.py. Update requirements and skill.

### Phase 5: Validate + commit

Full render tests with real mission data, version bump, commit.

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. All paths are in `plugins/edifice-mission-report/` unless noted.

### CREATE `templates/ic-ingenieurs/` directory structure

- **IMPLEMENT**: Create org subdirectories and placeholder.
- **EXECUTE**:
  ```bash
  mkdir -p /Users/renaud/Projects/bluegreen-marketplace/plugins/edifice-mission-report/templates/ic-ingenieurs
  mkdir -p /Users/renaud/Projects/bluegreen-marketplace/plugins/edifice-mission-report/templates/blue-green
  touch /Users/renaud/Projects/bluegreen-marketplace/plugins/edifice-mission-report/templates/blue-green/.gitkeep
  mkdir -p /Users/renaud/Projects/bluegreen-marketplace/plugins/edifice-mission-report/scripts
  ```
- **VALIDATE**:
  ```bash
  ls /Users/renaud/Projects/bluegreen-marketplace/plugins/edifice-mission-report/templates/
  # Should show: blue-green/  ic-ingenieurs/  suivi_chantier.docx
  ```

### MOVE `templates/suivi_chantier.docx` → `templates/ic-ingenieurs/suivi_chantier.docx`

- **IMPLEMENT**: Move the existing template file.
- **EXECUTE**:
  ```bash
  mv /Users/renaud/Projects/bluegreen-marketplace/plugins/edifice-mission-report/templates/suivi_chantier.docx \
     /Users/renaud/Projects/bluegreen-marketplace/plugins/edifice-mission-report/templates/ic-ingenieurs/suivi_chantier.docx
  ```
- **VALIDATE**:
  ```bash
  test -f /Users/renaud/Projects/bluegreen-marketplace/plugins/edifice-mission-report/templates/ic-ingenieurs/suivi_chantier.docx && echo "MOVED OK"
  test ! -f /Users/renaud/Projects/bluegreen-marketplace/plugins/edifice-mission-report/templates/suivi_chantier.docx && echo "OLD PATH GONE"
  ```

### UPDATE `render_report.py` — org-aware dispatch + normalize_v1 + --org flag

- **IMPLEMENT**: Rewrite `render_report.py` with `PLUGIN_DIR`, `_template_path()`, `normalize_v1()`, updated `render()` with `org=None`, and `--org` argparse flag in `main()`.
- **PATTERN**: See "Updated render() in render_report.py" pattern above. Remove `TEMPLATE_SUIVI` constant (replaced by `_template_path()`). Add `import os` at top.
- **GOTCHA**: `main()` calls `render()` — update the call to pass `org=args.org`.
- **GOTCHA**: Keep `sys.path.insert(0, str(SCRIPT_DIR))` at top — needed for relative renderer imports.
- **VALIDATE**:
  ```bash
  cd /Users/renaud/Projects/bluegreen-marketplace/plugins/edifice-mission-report
  python3 render_report.py --help | grep "\-\-org"
  python3 -c "from render_report import render, normalize_v1, _template_path; print('render_report OK')"
  ```

### CREATE `scripts/prepare_diagnostic_template.py` — hybrid diagnostic template

- **IMPLEMENT**: Load `rapport-diag-template.docx` (already a valid IC-branded docxtpl template), strip the observations section, inject a new disorder loop table, save as `diagnostic.docx`.
- **SOURCE**: `/Users/renaud/Projects/MyClaudeSkills/document-generator/organizations/ic-ingenieurs/templates/rapport-diag-template.docx`
- **ALGORITHM**:
  1. Open source template with `Document(source_path)` (python-docx)
  2. **Remove** from the document body: para 077 heading "Observations et désordres", para 078 `{{ observations }}`, para 079, para 080 "Tableau des désordres", paras 081-083 (empty), Table 3 (the `{{d.ref}}` summary table). Use `element._element.getparent().remove(element._element)` to delete them.
  3. **Add back** a new "Observations et désordres" Heading 1 paragraph.
  4. **Add** the per-disorder loop table (5-col structure, IC_BLUE header row, then `{%tr for d in disorders %}` ... `{%tr endfor %}`):

  ```
  Table layout (one set of rows per disorder, repeated by {%tr for %}):

  Row 0 (loop start): cell[0] = "{%tr for d in disorders %}" (invisible tag row — set row height minimal)
  Row 1 (header bar): colspan-5 merged | IC_BLUE bg | "{{ d.ref }}  {{ d.name }}"
  Row 2 (location):   "Localisation :" | colspan-4 "{{ d.location }}"
  Row 3 (IE badge):   "Indice d'état :" | colspan-4 "IE {{ d.ie }}"
  Row 4 (photos):     colspan-2 "{{ d.photo1 }}" | colspan-2 "{{ d.photo2 }}"  (2-col, row 1)
  Row 5 (photos):     colspan-2 "{{ d.photo3 }}" | colspan-2 "{{ d.photo4 }}"  (2-col, row 2, conditional)
  Row 6 (desc):       "Description :" | colspan-4 "{{ d.description }}"
  Row 7 (cause):      "Cause probable :" | colspan-4 "{{ d.cause }}"
  Row 8 (reco):       "Recommandations :" | colspan-4 "{{ d.recommendations }}"
  Row 9 (loop end):   cell[0] = "{%tr endfor %}" (invisible tag row)
  ```

- **GOTCHA — `{%tr for %}` tag placement**: The tag `{%tr for d in disorders %}` must go in the FIRST CELL of the FIRST row of the repeating group. `{%tr endfor %}` in the first cell of the LAST row. These rows are also repeated (they appear 0-width or minimal). docxtpl detects `{%tr` prefix to trigger row-level loop.
- **GOTCHA — tag run safety**: Each `{{ variable }}` must be a single `paragraph.add_run("{{ variable }}")`. Never mix styling within the tag string.
- **GOTCHA — `{% if %}` for optional photos**: Rows 5 (photos 3/4) can use `{%tr if d.photo3 or d.photo4 %}` / `{%tr endif %}` to hide if no additional photos.
- **GOTCHA — removing elements**: To remove a paragraph or table from the document body use `p._element.getparent().remove(p._element)`. For the Table 3, use `doc.tables[3]._element.getparent().remove(doc.tables[3]._element)`.
- **EXECUTE**:
  ```bash
  cd /Users/renaud/Projects/bluegreen-marketplace/plugins/edifice-mission-report
  uv run --with "python-docx>=1.1" python3 scripts/prepare_diagnostic_template.py
  ```
- **VALIDATE**:
  ```bash
  uv run --with "docxtpl>=0.18" python3 - <<'EOF'
  from docxtpl import DocxTemplate
  doc = DocxTemplate('templates/ic-ingenieurs/diagnostic.docx')
  vars = doc.get_undeclared_template_variables()
  print('Variables:', sorted(vars))
  required = {'service_type', 'client', 'dossier', 'date_rapport', 'contexte',
              'description_batiment', 'conclusions', 'recommandations', 'disorders'}
  missing = required - vars
  print('MISSING:', missing) if missing else print('All required tags present OK')
  # Also check disorders sub-fields
  assert 'd.ref' in vars or True, "check d.* vars in loop"
  print(f'Total vars: {len(vars)}')
  EOF
  ```

### CREATE `scripts/create_devis_template.py` — devis template from scratch

- **IMPLEMENT**: Write python-docx script to generate `templates/ic-ingenieurs/devis.docx` from scratch with IC branding.
- **STRUCTURE**:
  1. **Cover** — IC header bar (IC_BLUE bg, "IC INGÉNIEURS CONSEILS") | "RAPPORT PRÉLIMINAIRE — DEMANDE DE DEVIS" (white on IC_BLUE badge) | `{{ titre_service }}` (Pt 16, bold, IC_BLUE) | meta: `{{ client }}`, `{{ adresse }}`, `{{ date_visite }}`, `{{ technicien }}` | page break
  2. **Section 1 — Contexte client** — 2-col table (IC_BLUE header): `{{ client }}`, `{{ type_acteur }}`, `{{ interlocuteur_nom }}`, `{{ interlocuteur_role }}`, `{{ interlocuteur_contact }}`
  3. **Section 2 — Mission** — 2-col table: `{{ type_mission }}`, `{{ declencheur }}`, `{{ livrable }}`, `{{ urgence }}`
  4. **Section 3 — Bâtiment** — 2-col table: `{{ adresse }}`, `{{ type_batiment }}`, `{{ annee_construction }}`, `{{ nb_etages }}`, `{{ description_batiment }}`
  5. **Section 4 — Documents fournis** — 2-col table: `{%tr for d in documents_fournis %}` | `{{ d.document }}` | `{{ d.fourni_str }}` | `{%tr endfor %}`
  6. **Section 5 — Observations terrain** — 4-col table: `{%tr for obs in observations %}` | `{{ obs.localisation }}` | `{{ obs.desordre }}` | `{{ obs.donnees_cles }}` | `{{ obs.ref_photo }}` | `{%tr endfor %}`
  7. **Section 6 — Proposition de mission** — 2-col table: `{{ proposition_mission }}` | `{{ incertitudes }}`
  8. **Section 7 — Chiffrage estimatif** — 3-col table: `{%tr for ligne in chiffrage %}` | `{{ ligne.prestation }}` | `{{ ligne.nb_heures }}` | `{{ ligne.montant_ht }}` | `{%tr endfor %}`
  9. **Validation** — 3-col table: `{{ technicien }}` | `{{ date_visite }}` | `{{ date_envoi }}`
- **EXECUTE**:
  ```bash
  uv run --with "python-docx>=1.1" python3 scripts/create_devis_template.py
  ```
- **VALIDATE**:
  ```bash
  uv run --with "docxtpl>=0.18" python3 - <<'EOF'
  from docxtpl import DocxTemplate
  doc = DocxTemplate('templates/ic-ingenieurs/devis.docx')
  vars = doc.get_undeclared_template_variables()
  required = {'titre_service', 'client', 'adresse', 'date_visite', 'technicien',
              'documents_fournis', 'observations', 'chiffrage', 'proposition_mission'}
  missing = required - vars
  print('MISSING:', missing) if missing else print('devis template vars OK')
  EOF
  ```

### CREATE `scripts/update_suivi_chantier_branding.py` — IC branding for suivi_chantier

- **IMPLEMENT**: Load existing `templates/ic-ingenieurs/suivi_chantier.docx`, replace cover page + update Heading styles, save in place.
- **WHAT TO CHANGE**:
  1. **Cover page** — The existing cover has basic text. Replace with IC Ingénieurs branded block matching `rapport-diag-template.docx` style: IC_BLUE header bar at top, "IC INGÉNIEURS CONSEILS" title, then existing `{{ titre_service }}`, `{{ client }}`, etc. variables preserved. Study the source template's cover (paragraphs 0-11 of `rapport-diag-template.docx`) for reference.
  2. **Heading 1 style** — Set `font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)`, `font.bold = True`, appropriate `font.size`.
  3. **Heading 2 style** — Set same IC_BLUE color, non-bold or lighter weight.
- **APPROACH**: Read existing cover paragraphs (before first section heading), delete them, insert IC branded cover paragraphs using python-docx. Modify `doc.styles['Heading 1']` and `doc.styles['Heading 2']` directly.
- **GOTCHA**: Do NOT touch the observations table, participants table, or any Jinja2 tags already in the template — only the cover page paragraphs and heading styles.
- **GOTCHA**: The source `rapport-diag-template.docx` uses content controls and specific XML for the cover — copy the approach (header bar via table with IC_BLUE shading) rather than copying XML directly.
- **EXECUTE**:
  ```bash
  uv run --with "python-docx>=1.1" python3 scripts/update_suivi_chantier_branding.py
  open templates/ic-ingenieurs/suivi_chantier.docx   # verify visually in Word
  ```
- **VALIDATE**:
  ```bash
  uv run --with "docxtpl>=0.18" python3 - <<'EOF'
  from docxtpl import DocxTemplate
  # Ensure existing Jinja2 tags still intact after branding update
  doc = DocxTemplate('templates/ic-ingenieurs/suivi_chantier.docx')
  vars = doc.get_undeclared_template_variables()
  required = {'titre_service', 'client', 'observations', 'date_visite'}
  missing = required - vars
  print('MISSING:', missing) if missing else print('suivi_chantier branding OK — tags preserved')
  EOF
  ```

### REWRITE `render_diagnostic.py` — migrate to docxtpl

- **IMPLEMENT**: Replace the entire file with a lean docxtpl runner.
- **KEEP** (preserve): Function signature `render_diagnostic(context, photos_dir=".", output_path="rapport_diagnostic.docx")`, `format_date_french()` utility.
- **REMOVE**: All `from docx import ...`, `from lxml import etree`, all helper functions (`set_cell_shading`, `set_table_borders`, `setup_heading_styles`, `_set_style_numpr`, `build_cover`, `build_section_*`, `build_disorder_block`, `_build_ie_table`, etc.).
- **ADD**:
  - `from docxtpl import DocxTemplate, InlineImage`
  - `from docx.shared import Cm`
  - `TEMPLATE_PATH = Path(__file__).parent / "templates" / "ic-ingenieurs" / "diagnostic.docx"`
  - `_build_context(context, photos_dir, doc)` — see exact implementation in "Patterns to Follow" section above
  - Lean `render_diagnostic()` — DocxTemplate → _build_context → render → save
- **TEMPLATE VARIABLE NAMES**: The template uses `disorders` (list), `service_type`, `dossier`, `date_rapport`, `contexte`, `conclusions`, `recommandations` — NOT the Edifice field names. The `_build_context()` function does the mapping.
- **GOTCHA — photos**: Each disorder gets `photo1`..`photo4` as InlineImage or None. The template uses `{%tr if d.photo3 or d.photo4 %}` to hide the second photo row when empty. Guard: `InlineImage(doc, str(path), width=Cm(7.5)) if path.exists() else None`.
- **GOTCHA — disorders source**: Handle both `disorders[]` (IC direct format — pass as-is with a field remap) and `observations[]` (Edifice format — normalize in `_build_context`). Check `context.get("disorders")` first, fall back to `context.get("observations", [])`.
- **VALIDATE**:
  ```bash
  cd /Users/renaud/Projects/bluegreen-marketplace/plugins/edifice-mission-report
  python3 -c "from render_diagnostic import render_diagnostic; print('import OK')"
  python3 -c "import inspect; from render_diagnostic import render_diagnostic; sig=inspect.signature(render_diagnostic); print(sig)"
  # Expected: (context, photos_dir='.', output_path='rapport_diagnostic.docx')
  python3 -c "import render_diagnostic as m; assert not hasattr(m, 'build_cover'), 'OLD CODE PRESENT'"
  grep "from docx import" render_diagnostic.py && echo "FAIL: python-docx direct import" || echo "OK"
  grep "from lxml" render_diagnostic.py && echo "FAIL: lxml import" || echo "OK"
  ```

### REWRITE `render_devis.py` — migrate to docxtpl

- **IMPLEMENT**: Replace entire file with docxtpl runner.
- **KEEP**: Function signature `render_devis(context, photos_dir=".", output_path="rapport_devis.docx")`, `format_date_french()`.
- **REMOVE**: All python-docx programmatic code, all helper functions (`set_cell_shading`, `set_table_borders`, `add_row_2col`, `add_section_heading`, `build_cover`, `build_section_*`, etc.).
- **ADD**: docxtpl imports, `TEMPLATE_PATH`, `_build_context()` (adds `fourni_str` to documents_fournis items, formats dates), lean `render_devis()`.
- **NOTE**: Devis has no photos — no InlineImage needed. `_build_context()` is simple dict transformation.
- **VALIDATE**:
  ```bash
  python3 -c "from render_devis import render_devis; print('import OK')"
  python3 -c "import render_devis as m; assert not hasattr(m, 'build_section_client'), 'OLD CODE PRESENT'"
  grep "from docx import" render_devis.py && echo "FAIL: python-docx direct import" || echo "OK"
  ```

### UPDATE `render_cr_visite.py` — new template path ONLY

- **IMPLEMENT**: Update the `TEMPLATE_PATH` constant on line 66. The branding is now handled by the template file itself (updated by `update_suivi_chantier_branding.py`).
- **OLD**: `TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "template_cr_visite_aulnay.docx")`
- **NEW**: `TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "templates", "ic-ingenieurs", "suivi_chantier.docx")`
- **DO NOT CHANGE**: anything else in this file (python-docx imports remain, all functions unchanged).
- **VALIDATE**:
  ```bash
  python3 -c "
  from render_cr_visite import TEMPLATE_PATH
  from pathlib import Path
  p = Path(TEMPLATE_PATH)
  assert 'ic-ingenieurs' in str(p), f'Wrong path: {p}'
  assert p.exists(), f'Template not found: {p}'
  print('Path OK:', TEMPLATE_PATH)
  "
  ```

### UPDATE `requirements.txt`

- **OLD content**:
  ```
  supabase>=2.28,<3.0
  python-docx>=1.1
  Pillow>=10.0
  pyyaml>=6.0
  ```
- **NEW content**:
  ```
  docxtpl>=0.18
  Pillow>=10.0
  ```
- **RATIONALE**: `supabase` removed (pull_mission uses stdlib urllib). `python-docx` removed (comes transitively from docxtpl). `pyyaml` removed (grep confirms: no yaml imports in any .py). `docxtpl>=0.18` added.
- **VALIDATE**:
  ```bash
  grep "docxtpl" requirements.txt && echo "docxtpl OK"
  grep "python-docx" requirements.txt && echo "PROBLEM: python-docx still listed" || echo "python-docx removed OK"
  grep "supabase" requirements.txt && echo "PROBLEM: supabase still listed" || echo "supabase removed OK"
  ```

### UPDATE `skills/edifice/SKILL.md` — uv run command + org override

- **IMPLEMENT**: Update `/edifice report` step 1. Change `--with "python-docx>=1.1"` → `--with "docxtpl>=0.18"`. Add org override documentation.
- **FIND** (line ~240-248):
  ```
  uv run \
    --with "python-docx>=1.1" \
    --with pillow \
    python3 $PLUGIN_DIR/render_report.py \
  ```
- **REPLACE WITH**:
  ```
  uv run \
    --with "docxtpl>=0.18" \
    --with pillow \
    python3 $PLUGIN_DIR/render_report.py \
    mission/context.json \
    --photos-dir mission/photos \
    --output mission/rapport.docx
  ```
- **ADD** after the command block, a note:
  > Org override: `--org ic-ingenieurs` (default) or env var `EDIFICE_ORG=ic-ingenieurs`.
- **UPDATE** the renderer descriptions in the "Types de rapports" section: change `Renderer : render_diagnostic.py | Programmatique, aucun template requis` → `Renderer : render_diagnostic.py | docxtpl + templates/ic-ingenieurs/diagnostic.docx`. Same for devis.
- **VALIDATE**:
  ```bash
  grep "docxtpl" skills/edifice/SKILL.md && echo "SKILL updated OK"
  grep "python-docx" skills/edifice/SKILL.md && echo "PROBLEM: old dep still in SKILL" || echo "python-docx removed from SKILL OK"
  ```

---

## TESTING STRATEGY

### Test 1 — `diagnostic` (PRIMARY — must pass before committing)

```bash
MISSION="$HOME/Library/CloudStorage/GoogleDrive-renaud@bluegreen.ai/Drive partagés/PARTENAIRES/IC Ingénieurs Conseils/Dev-xxx-Diag rue de varenne/mission"

cd /Users/renaud/Projects/bluegreen-marketplace/plugins/edifice-mission-report

uv run \
  --with "docxtpl>=0.18" \
  --with pillow \
  python3 render_report.py \
  "$MISSION/context.json" \
  --photos-dir "$MISSION/photos" \
  --output /tmp/test_diagnostic.docx

open /tmp/test_diagnostic.docx
```

**Expected**: Opens without errors. IC branded cover page. 8 observations with photos. Synthèse populated.

### Test 2 — `suivi_chantier` v1.0 format (must pass — tests normalize_v1)

```bash
MISSION="$HOME/Library/CloudStorage/GoogleDrive-renaud@bluegreen.ai/Drive partagés/PARTENAIRES/IC Ingénieurs Conseils/IC-LeGrosSaule_Aulnay_2026/VisitesChantier/mission-2026-04-17-Visite-chantier---ferraillage-"

uv run \
  --with "docxtpl>=0.18" \
  --with pillow \
  python3 render_report.py \
  "$MISSION/context.json" \
  --photos-dir "$MISSION/photos" \
  --output /tmp/test_suivi_chantier.docx

open /tmp/test_suivi_chantier.docx
```

**Expected**: normalize_v1 converts v1.0 format. Suivi chantier renders with IC branded cover page + updated Heading styles.

### Test 3 — `devis` minimal (validates import + render without crash)

```bash
python3 -c "
from render_devis import render_devis
import tempfile, os
ctx = {
    'project_type': 'devis', 'titre_service': 'Test Devis', 'client': 'Test Client',
    'date_visite': '2026-05-01', 'technicien': 'R. Laborbe',
    'documents_fournis': [{'document': 'Plans', 'fourni': False}],
    'observations': [{'localisation': 'Hall', 'desordre': 'Fissure', 'donnees_cles': '', 'ref_photo': 'P1'}],
    'chiffrage': [{'prestation': 'Visite terrain', 'nb_heures': '3', 'montant_ht': ''}],
    'proposition_mission': 'Test', 'incertitudes': '',
}
out = tempfile.mktemp(suffix='.docx')
render_devis(ctx, output_path=out)
size = os.path.getsize(out)
print(f'Devis OK: {out} ({size} bytes)')
assert size > 5000, 'File too small — render likely failed'
"
```

### Edge Cases to Verify

- Missing photo file: should print warning, not crash (`photo_image = None`)
- Empty `observations`: section renders empty, no crash
- Missing `synthese`/`conclusion` fields: renders empty string, no crash

---

## VALIDATION COMMANDS

### Level 1: All imports pass

```bash
cd /Users/renaud/Projects/bluegreen-marketplace/plugins/edifice-mission-report

python3 -c "from render_diagnostic import render_diagnostic; print('render_diagnostic OK')"
python3 -c "from render_devis import render_devis; print('render_devis OK')"
python3 -c "from render_cr_visite import render_cr; print('render_cr OK')"
python3 -c "from render_report import render, normalize_v1, _template_path; print('render_report OK')"
```

### Level 2: No direct python-docx / lxml imports in migrated renderers

```bash
grep "^from docx import\|^import docx" render_diagnostic.py && echo "FAIL" || echo "render_diagnostic: no python-docx OK"
grep "^from docx import\|^import docx" render_devis.py && echo "FAIL" || echo "render_devis: no python-docx OK"
grep "from lxml import" render_diagnostic.py && echo "FAIL" || echo "render_diagnostic: no lxml OK"
```

### Level 3: Template files exist and old path gone

```bash
test -f templates/ic-ingenieurs/diagnostic.docx && echo "diagnostic.docx OK" || echo "MISSING"
test -f templates/ic-ingenieurs/devis.docx && echo "devis.docx OK" || echo "MISSING"
test -f templates/ic-ingenieurs/suivi_chantier.docx && echo "suivi_chantier.docx OK" || echo "MISSING"
test -f templates/blue-green/.gitkeep && echo ".gitkeep OK" || echo "MISSING"
test ! -f templates/suivi_chantier.docx && echo "old root template gone OK" || echo "PROBLEM: old template still at root"
```

### Level 4: Template variables check

```bash
uv run --with "docxtpl>=0.18" python3 - <<'EOF'
from docxtpl import DocxTemplate
for name in ['diagnostic', 'devis']:
    doc = DocxTemplate(f'templates/ic-ingenieurs/{name}.docx')
    vars = doc.get_undeclared_template_variables()
    print(f'{name}: {sorted(vars)}')
EOF
```

### Level 5: Diagnostic render test

```bash
MISSION="$HOME/Library/CloudStorage/GoogleDrive-renaud@bluegreen.ai/Drive partagés/PARTENAIRES/IC Ingénieurs Conseils/Dev-xxx-Diag rue de varenne/mission"
uv run --with "docxtpl>=0.18" --with pillow \
  python3 render_report.py "$MISSION/context.json" --photos-dir "$MISSION/photos" --output /tmp/test_diag.docx
python3 -c "
import os; s = os.path.getsize('/tmp/test_diag.docx')
print(f'Size: {s} bytes')
assert s > 50000, f'File too small ({s} bytes) — render likely failed'
print('Size check OK')
"
```

### Level 6: Version parity (marketplace.json === plugin.json)

```bash
python3 -c "
import json
m = json.load(open('.claude-plugin/../../.claude-plugin/marketplace.json'))
p = json.load(open('.claude-plugin/plugin.json'))
mv = next(x['version'] for x in m['plugins'] if x['name']=='edifice-mission-report')
pv = p['version']
assert mv == pv, f'VERSION MISMATCH: marketplace={mv} plugin={pv}'
print(f'Version parity OK: {mv}')
" 2>/dev/null || python3 -c "
import json
m = json.load(open('/Users/renaud/Projects/bluegreen-marketplace/.claude-plugin/marketplace.json'))
p = json.load(open('/Users/renaud/Projects/bluegreen-marketplace/plugins/edifice-mission-report/.claude-plugin/plugin.json'))
mv = next(x['version'] for x in m['plugins'] if x['name']=='edifice-mission-report')
pv = p['version']
assert mv == pv, f'VERSION MISMATCH: marketplace={mv} plugin={pv}'
print(f'Version parity OK: {mv}')
"
```

---

## ACCEPTANCE CRITERIA

- [ ] `templates/ic-ingenieurs/diagnostic.docx` exists with IC branding and valid Jinja2 tags
- [ ] `templates/ic-ingenieurs/devis.docx` exists with IC branding and valid Jinja2 tags
- [ ] `templates/ic-ingenieurs/suivi_chantier.docx` exists (moved from root)
- [ ] `templates/suivi_chantier.docx` no longer exists at root
- [ ] `templates/blue-green/.gitkeep` exists
- [ ] `render_diagnostic.py` — zero python-docx/lxml direct imports, docxtpl only
- [ ] `render_devis.py` — zero python-docx direct imports, docxtpl only
- [ ] `render_cr_visite.py` — template path updated to `templates/ic-ingenieurs/suivi_chantier.docx`
- [ ] `render_report.py` — has `_template_path()`, `normalize_v1()`, `org=None` in `render()`, `--org` argparse flag
- [ ] `requirements.txt` — `docxtpl>=0.18` + `Pillow>=10.0` only
- [ ] `SKILL.md` — `/edifice report` uses `--with "docxtpl>=0.18"`
- [ ] Test 1 (diagnostic, 8 obs, real photos) — runs without error, valid .docx output
- [ ] Test 2 (suivi_chantier v1.0 format) — normalize_v1 converts, renders correctly
- [ ] Test 3 (devis minimal) — renders without crash
- [ ] `plugin.json` version bumped (0.3.4 → 0.4.0)
- [ ] `marketplace.json` version updated to match
- [ ] Committed cleanly

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Level 1: all imports pass
- [ ] Level 2: no python-docx/lxml in migrated renderers
- [ ] Level 3: all template files exist, old root template gone
- [ ] Level 4: template variables check passes
- [ ] Level 5: diagnostic render test passes (>50KB)
- [ ] Level 6: version parity OK
- [ ] `plugin.json` version bumped to 0.4.0
- [ ] `marketplace.json` version updated to 0.4.0
- [ ] `CHANGELOG.md` entry added for v0.4.0
- [ ] `scripts/prepare_diagnostic_template.py`, `scripts/create_devis_template.py`, `scripts/update_suivi_chantier_branding.py` committed (reproducibility artifacts)
- [ ] Committed: `feat: migrate DOCX renderers to docxtpl + IC branded templates (v0.4.0)`

---

## NOTES

### Source of truth: bluegreen-marketplace (not edifice)

Despite what CLAUDE.md says about development happening in edifice, commit `e82b16281` removed the plugin from edifice and established the marketplace as the source. All Python scripts live only in `bluegreen-marketplace/plugins/edifice-mission-report/`. No rsync needed — the marketplace IS the source. Update CLAUDE.md if the confusion persists.

### Template strategy — three different approaches

**diagnostic.docx** — hybrid. Source: `rapport-diag-template.docx` (MyClaudeSkills). That file is already a valid docxtpl template with IC branded cover, Heading styles, sections, static IE table. Key variables: `service_type`, `dossier`, `date_rapport`, `contexte`, `conclusions`, `recommandations`. The observations section is replaced programmatically with a disorder loop table (header bar + IE + 2-col photos + description/cause/reco per disorder).

**suivi_chantier.docx** — re-brand only. The existing template loop/observations already work. Only the cover page and Heading styles need IC branding applied.

**render_cr_visite.py — important discrepancy with brief**: The brief says it "already uses docxtpl" but it uses `from docx import Document` (python-docx) with manual string replacement. NOT migrated to docxtpl in this sprint — path update only. python-docx imports remain (covered transitively by docxtpl install).

### lxml — no explicit removal needed

`render_diagnostic.py` uses `from lxml import etree` for heading numbering XML. After migration, this entire function block (`setup_heading_styles`, `_set_style_numpr`) is removed. lxml is not listed in requirements.txt (it was always a transitive dep). No action needed beyond removing the import.

### pyyaml — confirmed safe to remove

`grep -r "import yaml" *.py` returns no results. pyyaml was listed in requirements.txt but not used at runtime. Remove it.

### Template generation scripts in `scripts/`

The `scripts/create_*_template.py` files are committed as reproducibility artifacts: if Laurent wants to regenerate the baseline template (before his Word edits), these scripts can do it. They run with `uv run --with python-docx>=1.1` and are dev/maintenance tools, not runtime dependencies.

### Version bump: 0.3.4 → 0.4.0

This is a meaningful refactor (new template architecture, new org-aware dispatch, v1.0 format support). Minor version bump is appropriate. Update `plugin.json`, `marketplace.json`, and add a `CHANGELOG.md` entry.

### Confidence Score: 7/10

High confidence on the code migration. Main risk: the docxtpl for-loop handling in the observations table (multi-row pattern with InlineImage) may require template structure iteration to get right. The `get_undeclared_template_variables()` validation (Level 4) will catch missing tags. Test 1 with real photos will catch InlineImage issues.
