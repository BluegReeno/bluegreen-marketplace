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
to the right renderer. **It must not be modified** (except for org-aware template path
resolution in Step 5).

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
│   └── blue-green/             ← placeholder only (.gitkeep)
├── render_report.py            ← update: org-aware path resolution + --org flag
├── render_diagnostic.py        ← migrate to docxtpl
├── render_cr_visite.py         ← update: new template path
├── render_devis.py             ← migrate to docxtpl
├── tests/                      ← test instructions (see tests/README.md)
└── skills/edifice/SKILL.md     ← update: org override + trigger phrases
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
Create `templates/blue-green/.gitkeep` (empty placeholder).
Update `render_report.py` to resolve template path via `_template_path(org, project_type)`.

### Step 2 — Create `templates/ic-ingenieurs/diagnostic.docx`

**This is the most important and hardest step.** Create a branded Word template for
the diagnostic report. **The first page must look like a professional IC Ingénieurs
Conseils document** — matching the visual identity of their existing reports.

#### First page — IC Ingénieurs Conseils branding requirements

The first page is the client-facing cover. It must include:
- **Logo IC Ingénieurs Conseils** — top left or top center
- **Document type** (large, prominent): e.g. "RAPPORT DE DIAGNOSTIC STRUCTURAL"
- **Service title**: `{{ titre_service }}`
- **Client block**: Nom client (`{{ client }}`), résidence (`{{ residence }}`)
- **Address**: `{{ adresse }}`
- **Reference / dossier**: `{{ ref_dossier }}`
- **Date de visite**: `{{ date_visite }}`
- IC Ingénieurs footer with address/contact

**Reference documents to study for the cover page design** (open in Word before
creating the template):

1. `plugins/edifice-mission-report/templates/ic-ingenieurs/suivi_chantier.docx`
   — already IC branded, same cover page structure. **Primary reference.**

2. The IC Ingénieurs reference template in the Edifice repo:
   `../edifice/agent/document-generator/organizations/ic-ingenieurs/templates/rapport-diag-template.docx`
   — contains the full IC diagnostic layout including cover page.
   Open it in Word to extract: logo placement, font sizes, color blocks, header/footer.

3. Real IC reports in Google Drive (reference only — do not include confidential data):
   ```
   ~/Library/CloudStorage/GoogleDrive-renaud@bluegreen.ai/
     Drive partagés/PARTENAIRES/IC Ingénieurs Conseils/Template IC/
   ```

**IC brand colors** (from `render_diagnostic.py`):
- `IC_BLUE = #1F3A5F` — headers, borders, cover background block
- `IC_ORANGE = #E86A1A` — IE badges, accent lines, section separators
- Alternating table row: `#F0F4F8`
- Font: Calibri (body), Calibri Bold (headings)

#### Body sections and docxtpl tags

```
[Page de garde — full page]
  [Logo block — top]
  [Color band or background — IC blue]
  RAPPORT DE DIAGNOSTIC STRUCTURAL
  {{ titre_service }}
  ─────────────────────────────────
  Client     : {{ client }}
  Résidence  : {{ residence }}
  Adresse    : {{ adresse }}
  Dossier    : {{ ref_dossier }}
  Date visite: {{ date_visite }}
  [Footer with IC contact]

[1. Objet de la mission]
  {{ objet_visite }}

[2. Présentation du bâtiment]
  {{ description_batiment }}

[3. Échelle d'évaluation IE]
  Static table (IE 1–5 with color-coded rows) — hardcoded in template, no tags
  | IE 1 | Risque de ruine immédiate | rouge |
  | IE 2 | Désordres graves          | orange |
  | IE 3 | Dégradation modérée       | jaune |
  | IE 4 | Dégradation légère        | vert clair |
  | IE 5 | Bon état                  | vert |

[4. Résultats de la visite]
  {% for obs in observations %}
  Row header: {{ obs.ref }} | {{ obs.zone }} | {{ obs.localisation }} | IE {{ obs.ie }}
  Row (merged): {{ obs.desordre }}
  Row (merged): {{ obs.photo_image }}   ← InlineImage(doc, path, width=Cm(8))
  Row (merged): Action : {{ obs.action }}
  {% endfor %}

[5. Synthèse]
  {{ synthese }}

[6. Conclusion et recommandations]
  {{ conclusion }}
```

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
from pathlib import Path

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
- Remove: `python-docx`, `lxml` (no longer needed)
- Add: `docxtpl>=0.18`
- Keep: `pillow`

### Step 4 — Create `templates/ic-ingenieurs/devis.docx` + migrate `render_devis.py`

Same approach as Step 2+3. Cover page follows the same IC branding rules.
Document type line: "RAPPORT PRÉLIMINAIRE — DEMANDE DE DEVIS".

**Sections and tags:**
```
[Page de garde]
  [IC logo + branding — same as diagnostic]
  RAPPORT PRÉLIMINAIRE — DEMANDE DE DEVIS
  {{ titre_service }}
  Client : {{ client }} | {{ adresse }} | {{ date_visite }} | Technicien : {{ technicien }}

[1. Contexte client]
  Tableau : {{ client }} | {{ type_acteur }} | {{ interlocuteur_nom }} | {{ interlocuteur_role }} | {{ interlocuteur_contact }}

[2. Mission]
  Tableau : {{ type_mission }} | {{ declencheur }} | {{ livrable }} | {{ urgence }}

[3. Bâtiment]
  Tableau : {{ adresse }} | {{ type_batiment }} | {{ annee_construction }} | {{ nb_etages }}
  {{ description_batiment }}

[4. Documents fournis]
  {% for d in documents_fournis %}
  {{ d.document }} | {{ "✓ Oui" if d.fourni else "✗ Non" }}
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
  Technicien : {{ technicien }} | Date visite : {{ date_visite }} | Date envoi : {{ date_envoi }}
```

### Step 5 — Update `render_report.py` for org-aware dispatch

```python
import os
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent

def _template_path(org: str, project_type: str) -> Path:
    path = PLUGIN_DIR / "templates" / org / f"{project_type}.docx"
    if not path.exists():
        raise SystemExit(f"Template not found: {path}\nSet EDIFICE_ORG or use --org flag.")
    return path

def render(context, photos_dir, output_path, org=None):
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

Add `--org` CLI flag to `argparse` in `main()`.

### Step 6 — Update `SKILL.md`

In the `/edifice report` section:
1. Template selection is automatic from `context.json.project_type`
2. Org override: `EDIFICE_ORG=ic-ingenieurs` env var or `--org ic-ingenieurs` flag
3. Update `uv run` invocation: `--with "docxtpl>=0.18"` replaces `--with "python-docx>=1.1"`
4. Add natural language triggers to `description:` field:
   - "génère le rapport", "generate the report", "create the report", "faire le rapport"

```bash
# Updated uv run command in SKILL.md
uv run \
  --with "docxtpl>=0.18" \
  --with pillow \
  python3 $PLUGIN_DIR/render_report.py \
  mission/context.json \
  --photos-dir mission/photos \
  --output mission/rapport.docx
```

---

## Test data

See `plugins/edifice-mission-report/tests/README.md` for full instructions.

### Test 1 — `diagnostic` (primary)

**Mission**: Diagnostic structurel planchers bois, Rue de Varenne, Paris 7e
**Format**: v2.0 (current — `observations[]`, top-level `project_type`)
**Path**:
```
~/Library/CloudStorage/GoogleDrive-renaud@bluegreen.ai/
  Drive partagés/PARTENAIRES/IC Ingénieurs Conseils/Dev-xxx-Diag rue de varenne/
  mission/context.json        ← 8 observations, synthèse rédigée
  mission/photos/             ← 28 photos terrain
```
**Validation**: compare output with `mission/rapport.docx` (current programmatic output).

### Test 2 — `suivi_chantier`

**Mission**: Visite chantier ferraillage bâtiment C, Le Gros Saule, Aulnay-sous-Bois (2026-04-17)
**Format**: ⚠️ **v1.0 (old)** — uses `notes[]` instead of `observations[]`, `project_type`
nested as `mission.type`
**Path**:
```
~/Library/CloudStorage/GoogleDrive-renaud@bluegreen.ai/
  Drive partagés/PARTENAIRES/IC Ingénieurs Conseils/
  IC-LeGrosSaule_Aulnay_2026/VisitesChantier/
  mission-2026-04-17-Visite-chantier---ferraillage-/
  context.json                ← 28 notes
  photos/                     ← 69 photos
```

**⚠️ v1.0 format handling required**: add `normalize_v1(ctx)` in `render_report.py`
that converts old format to v2.0 before dispatch:
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

**Reference IC suivi_chantier template** (study before creating the new one):
```
mission-2026-04-17-Visite-chantier---ferraillage-/template_cr_visite_aulnay.docx
```
This is Laurent's current working template. The new `templates/ic-ingenieurs/suivi_chantier.docx`
should match its visual style.

---

## Constraints

- `render_report.py` public interface (`render(context, photos_dir, output_path)`) must not change
- `render_diagnostic(context, photos_dir, output_path)` signature must be preserved
- `render_cr(context, photos_dir, output_path, template_path)` signature must be preserved
- `render_devis(context, photos_dir, output_path)` signature must be preserved
- `uv run` invocation in SKILL.md is the user-facing entry point — must stay working
- All `python-docx` imports must be removed from migrated renderers
- `requirements.txt` must reflect the new dep set

---

## What NOT to build

- No Blue Green templates (placeholder dir + `.gitkeep` only)
- No org auto-detection from Supabase profile (future improvement)
- No new CLI arguments beyond `--org`
- No changes to `pull_mission.py`, `push_mission.py`, `pair.py`
- No changes to the schema-contract (no Supabase schema touched)
- Do not add `devis` test data — skip devis validation for now (no rich test mission available)

---

## Key files to read before planning

| File | Why |
|------|-----|
| `plugins/edifice-mission-report/render_report.py` | Dispatcher — understand routing |
| `plugins/edifice-mission-report/render_cr_visite.py` | Reference docxtpl renderer (working) |
| `plugins/edifice-mission-report/render_diagnostic.py` | Source to migrate (python-docx) |
| `plugins/edifice-mission-report/render_devis.py` | Source to migrate (python-docx) |
| `plugins/edifice-mission-report/templates/suivi_chantier.docx` | Current IC template (before move) |
| `plugins/edifice-mission-report/requirements.txt` | Deps to update |
| `plugins/edifice-mission-report/skills/edifice/SKILL.md` | SKILL to update |
| `plugins/edifice-mission-report/tests/README.md` | Test data locations |
| `../edifice/agent/document-generator/organizations/ic-ingenieurs/templates/rapport-diag-template.docx` | IC cover page reference (open in Word) |

---

## Definition of done

- [ ] `templates/ic-ingenieurs/diagnostic.docx` — branded cover page + all sections + docxtpl tags
- [ ] `templates/ic-ingenieurs/suivi_chantier.docx` — moved from root, path updated in renderer
- [ ] `templates/ic-ingenieurs/devis.docx` — branded cover page + all sections + docxtpl tags
- [ ] `templates/blue-green/.gitkeep` — placeholder exists
- [ ] `render_diagnostic.py` — docxtpl only, zero python-docx imports
- [ ] `render_cr_visite.py` — updated to `templates/ic-ingenieurs/suivi_chantier.docx` path
- [ ] `render_devis.py` — docxtpl only, zero python-docx imports
- [ ] `render_report.py` — org-aware `_template_path()`, `normalize_v1()`, `--org` flag
- [ ] `requirements.txt` — `docxtpl>=0.18` + `pillow`, no `python-docx`, no `lxml`
- [ ] `SKILL.md` — `uv run` uses docxtpl, org override documented
- [ ] Test diagnostic: `uv run render_report.py mission/context.json` on Varenne data → clean DOCX
- [ ] Test suivi_chantier: runs on ferraillage v1.0 data after normalization → clean DOCX
