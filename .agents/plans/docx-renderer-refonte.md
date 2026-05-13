# Feature Brief — DOCX Renderer Refonte (docxtpl + branded templates)

**Plugin**: `plugins/edifice-mission-report/`
**Date**: 2026-05-13
**Status**: Ready to plan

---

## Context

The `edifice-mission-report` plugin generates DOCX reports for IC Ingénieurs Conseils
from a local `mission/context.json` produced by the Edifice terrain app.

Today, two of the three renderers are **fully programmatic** (python-docx, no template):
- `render_diagnostic.py` — python-docx, ~400 lines of layout code, hard to maintain
- `render_devis.py` — python-docx, programmatic

One renderer already uses docxtpl with a branded template:
- `render_cr_visite.py` — docxtpl + `templates/suivi_chantier.docx` ✅

The dispatcher `render_report.py` reads `project_type` from `context.json` and routes
to the right renderer. **It must not be modified.**

### Why migrate to docxtpl

- Laurent can edit the visual layout in Word without touching code
- IC brand (colors, fonts, logo, headers/footers) lives in the `.docx` file, not in code
- Less code: the renderer becomes a context builder, not a layout engine
- Consistent with the existing `suivi_chantier` renderer that already works well

### Architecture decision (already made — do not revisit)

One plugin, org-aware template registry:

```
plugins/edifice-mission-report/
├── templates/
│   ├── ic-ingenieurs/          ← default org
│   │   ├── diagnostic.docx     ← TO CREATE
│   │   ├── suivi_chantier.docx ← MOVE from templates/ root
│   │   └── devis.docx          ← TO CREATE
│   └── blue-green/             ← placeholder, empty for now
├── render_report.py            ← update: org-aware path resolution
├── render_diagnostic.py        ← migrate to docxtpl
├── render_cr_visite.py         ← update: new template path
├── render_devis.py             ← migrate to docxtpl
└── skills/edifice/SKILL.md     ← update: document org override + trigger phrases
```

Org detection in `render_report.py` — cascade (do not over-engineer):
```python
org = context.get("org") \
   or os.environ.get("EDIFICE_ORG") \
   or "ic-ingenieurs"           # hardcoded default
template = PLUGIN_DIR / "templates" / org / f"{project_type}.docx"
```

The `project_type` comes from `context.json` — already works, no change needed.

---

## What to build

### Step 1 — Reorganize templates directory

Move `templates/suivi_chantier.docx` → `templates/ic-ingenieurs/suivi_chantier.docx`.
Create `templates/blue-green/` placeholder (empty dir with `.gitkeep`).
Update `render_report.py` to pass the template path from the new location to `render_cr`.

### Step 2 — Create `templates/ic-ingenieurs/diagnostic.docx`

**This is the hardest step.** Create a branded Word template for the diagnostic report.

IC brand reference (extract from existing `render_diagnostic.py`):
- `IC_BLUE = RGBColor(0x1F, 0x3A, 0x5F)` — headers, table borders
- `IC_ORANGE = RGBColor(0xE8, 0x6A, 0x1A)` — IE badges, accents
- Alternating row: `F0F4F8`
- Font: Calibri

**Sections and docxtpl tags** (all `{{ }}` are Jinja2, `{% %}` are loops):

```
[Page de garde]
  {{ titre_service }}
  {{ client }}         {{ residence }}
  {{ adresse }}        {{ ref_dossier }}
  {{ date_visite }}

[1. Objet de la mission]
  {{ objet_visite }}

[2. Présentation du bâtiment]
  {{ description_batiment }}

[3. Échelle d'évaluation IE]
  Static table (IE 1–5 with color badges) — hardcoded in template, no tags

[4. Résultats de la visite]
  {% for obs in observations %}
  Row 1: {{ obs.ref }} | {{ obs.zone }} | {{ obs.localisation }} | IE {{ obs.ie }}
  Row 2 (merged): {{ obs.desordre }}
  Row 3 (merged): Photo: {{ obs.photo_image }}   ← InlineImage(doc, path, width=Cm(8))
  Row 4 (merged): Action : {{ obs.action }}
  {% endfor %}

[5. Synthèse]
  {{ synthese }}

[6. Conclusion et recommandations]
  {{ conclusion }}
```

**Reference template to open and study** (IC branded, already deployed):
```
plugins/edifice-mission-report/templates/ic-ingenieurs/suivi_chantier.docx
```
Replicate its page layout, header, footer, and font style.

**Also study** (different document-generator approach):
The `agent/document-generator/` directory in `BluegReeno/edifice` repo has IC templates
and a `render_ic_report.py` script — useful reference for IC brand conventions.

### Step 3 — Migrate `render_diagnostic.py` to docxtpl

Replace the current ~400-line python-docx renderer with a lean docxtpl runner.

**Target interface (must keep):**
```python
def render_diagnostic(context: dict, photos_dir: str = ".", output_path: str = "rapport.docx") -> str:
```

**Target implementation pattern:**
```python
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Cm

TEMPLATE_PATH = Path(__file__).parent / "templates" / "ic-ingenieurs" / "diagnostic.docx"

def render_diagnostic(context, photos_dir=".", output_path="rapport.docx"):
    doc = DocxTemplate(TEMPLATE_PATH)
    tpl_ctx = _build_context(context, photos_dir, doc)
    doc.render(tpl_ctx)
    doc.save(output_path)
    return output_path

def _build_context(context, photos_dir, doc):
    observations = []
    for obs in context.get("observations", []):
        photo_path = Path(photos_dir) / obs.get("photo", "")
        photo_image = InlineImage(doc, str(photo_path), width=Cm(8)) if photo_path.exists() else None
        observations.append({**obs, "photo_image": photo_image})
    return {**context, "observations": observations}
```

**Dependencies** (update `requirements.txt`):
- Remove: `python-docx`, `lxml` (not needed for docxtpl)
- Add: `docxtpl>=0.18`
- Keep: `pillow` (for image handling in docxtpl)

### Step 4 — Create `templates/ic-ingenieurs/devis.docx` + migrate `render_devis.py`

Same approach as Step 2+3 but for the devis report.

**Sections and tags:**
```
[Page de garde]
  "RAPPORT PRÉLIMINAIRE — DEMANDE DE DEVIS"
  {{ titre_service }} | {{ client }} | {{ adresse }} | {{ date_visite }} | {{ technicien }}

[1. Contexte client]
  Tableau : {{ client }} | {{ type_acteur }} | {{ interlocuteur_nom }} | {{ interlocuteur_role }} | {{ interlocuteur_contact }}

[2. Mission]
  Tableau : {{ type_mission }} | {{ declencheur }} | {{ livrable }} | {{ urgence }}

[3. Bâtiment]
  Tableau : {{ adresse }} | {{ type_batiment }} | {{ annee_construction }} | {{ nb_etages }} | {{ description_batiment }}

[4. Documents fournis]
  {% for doc in documents_fournis %}
  {{ doc.document }} | {{ "✓ Oui" if doc.fourni else "✗ Non" }}
  {% endfor %}

[5. Observations terrain]
  {% for obs in observations %}
  {{ obs.localisation }} | {{ obs.desordre }} | {{ obs.donnees_cles }} | {{ obs.ref_photo }}
  {% endfor %}

[6. Proposition de mission]
  {{ proposition_mission }}
  Incertitudes : {{ incertitudes }}

[7. Chiffrage estimatif]
  {% for ligne in chiffrage %}
  {{ ligne.prestation }} | {{ ligne.nb_heures }} h | {{ ligne.montant_ht }} €
  {% endfor %}

[Validation]
  {{ technicien }} | {{ date_visite }} | {{ date_envoi }}
```

### Step 5 — Update `render_report.py` for org-aware dispatch

```python
PLUGIN_DIR = Path(__file__).resolve().parent

def _template_path(org: str, project_type: str) -> Path:
    path = PLUGIN_DIR / "templates" / org / f"{project_type}.docx"
    if not path.exists():
        raise SystemExit(f"Template not found: {path}\nSet EDIFICE_ORG or add --org flag.")
    return path

def render(context, photos_dir, output_path):
    org = context.get("org") or os.environ.get("EDIFICE_ORG") or "ic-ingenieurs"
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
```

Add `--org` CLI flag to `render_report.py` for override from command line.

### Step 6 — Update `SKILL.md`

In the `/edifice report` section, document:
1. That template selection is automatic from `context.json.project_type`
2. Org override: `EDIFICE_ORG=ic-ingenieurs` env var or `--org ic-ingenieurs` flag
3. Update the `uv run` command to use `docxtpl` instead of `python-docx`
4. Natural language triggers to add to `description:` field:
   - "génère le rapport", "generate the report", "create the report"
   - "faire le rapport", "rapport de visite", "diagnostic report"

Also update the `uv run` invocation in SKILL.md:
```bash
# OLD
uv run --with "python-docx>=1.1" --with pillow python3 $PLUGIN_DIR/render_report.py ...

# NEW
uv run --with "docxtpl>=0.18" --with pillow python3 $PLUGIN_DIR/render_report.py ...
```

---

## Test data available

**Diagnostic (primary test — most complete):**
```
~/Library/CloudStorage/GoogleDrive-renaud@bluegreen.ai/
  Drive partagés/PARTENAIRES/IC Ingénieurs Conseils/Dev-xxx-Diag rue de varenne/
  mission/context.json     ← 8 observations, synthese rédigée, project_type=diagnostic
  mission/photos/          ← 28 photos terrain
```

**Suivi chantier:**
```
~/edifice-missions/yani-savigny-2026-05-06/mission/
  context.json             ← 6 notes, project_type=suivi_chantier
  photos/                  ← 18 photos
```

Compare output with `mission/rapport.docx` (current programmatic output) to validate.

---

## Constraints

- `render_report.py` public interface (`render(context, photos_dir, output_path)`) must not change
- `render_diagnostic(context, photos_dir, output_path)` signature must be preserved
- `render_cr(context, photos_dir, output_path, template_path)` signature must be preserved
- `render_devis(context, photos_dir, output_path)` signature must be preserved
- `uv run` invocation in SKILL.md is the user-facing entry point — must stay working
- `python-docx` import in `render_diagnostic.py` must be replaced (no mixed deps)
- `requirements.txt` must reflect the new dep set

---

## What NOT to build

- No Blue Green templates yet (placeholder dir only)
- No org auto-detection from Supabase profile (future improvement)
- No new CLI arguments beyond `--org`
- No changes to `pull_mission.py`, `push_mission.py`, `pair.py`
- No changes to the schema-contract (no Supabase schema touched)

---

## Key files to read before planning

| File | Why |
|------|-----|
| `plugins/edifice-mission-report/render_report.py` | Dispatcher — understand routing |
| `plugins/edifice-mission-report/render_cr_visite.py` | Reference docxtpl renderer already working |
| `plugins/edifice-mission-report/render_diagnostic.py` | Source to migrate (python-docx) |
| `plugins/edifice-mission-report/templates/suivi_chantier.docx` | Reference IC template (open in Word) |
| `plugins/edifice-mission-report/skills/edifice/SKILL.md` | SKILL to update |
| `plugins/edifice-mission-report/requirements.txt` | Deps to update |

---

## Definition of done

- [ ] `templates/ic-ingenieurs/diagnostic.docx` exists and renders cleanly on Varenne test data
- [ ] `templates/ic-ingenieurs/suivi_chantier.docx` at new path, renderer updated
- [ ] `templates/ic-ingenieurs/devis.docx` exists and renders cleanly
- [ ] All 3 renderers use docxtpl — zero `python-docx` imports
- [ ] `render_report.py` passes template path from org-aware resolution
- [ ] `requirements.txt` updated: docxtpl>=0.18, pillow; no python-docx, no lxml
- [ ] `SKILL.md` `uv run` invocation uses docxtpl dep, org override documented
- [ ] `uv run ... render_report.py mission/context.json` works end-to-end for all 3 types
