# Tests — edifice-mission-report

Test data lives in Google Drive (not committed). Run `/edifice pull` to populate
a local `mission/` directory, or copy `context.json` + `photos/` manually.

---

## Test missions

### 1. `diagnostic` — Diagnostic structurel planchers bois, Rue de Varenne

**Mission dir** (local, already pulled):
```
~/Library/CloudStorage/GoogleDrive-renaud@bluegreen.ai/
  Drive partagés/PARTENAIRES/IC Ingénieurs Conseils/
  Dev-xxx-Diag rue de varenne/mission/
```

**Contents**: `context.json` (v2 format, 8 observations, synthèse rédigée) + `photos/` (28 photos)

**Briefing**: `Dev-xxx-Diag rue de varenne/mission-diag-structure-2026-04-28.edifice.md`

**Expected output**: `mission/rapport.docx` — compare with programmatic output already there.

---

### 2. `suivi_chantier` — Visite ferraillage bâtiment C, Le Gros Saule Aulnay

**Mission dir** (local, already available):
```
~/Library/CloudStorage/GoogleDrive-renaud@bluegreen.ai/
  Drive partagés/PARTENAIRES/IC Ingénieurs Conseils/
  IC-LeGrosSaule_Aulnay_2026/VisitesChantier/
  mission-2026-04-17-Visite-chantier---ferraillage-/
```

**Contents**: `context.json` (v1.0 format — see note below) + `photos/` (69 photos, 28 notes)

**⚠️ Format v1.0**: this `context.json` uses the old format:
- `notes[]` instead of `observations[]`
- `project_type` is nested: `mission.type` instead of top-level `project_type`
- No `participants` field

The renderer (or a pre-processing step) must handle v1.0 format.
Option A: add a `normalize_context(ctx)` function in `render_report.py` that upgrades v1.0 → v2.0.
Option B: convert the test file manually to v2.0 format before testing.

**Reference IC template** (already in this directory — study it):
```
mission-2026-04-17-Visite-chantier---ferraillage-/template_cr_visite_aulnay.docx
```
This is the current IC Ingénieurs suivi_chantier template used manually by Laurent.
The new `templates/ic-ingenieurs/suivi_chantier.docx` should follow the same visual style.

---

### 3. `devis` — (future test)

A `devis` context.json is available at:
```
~/Library/CloudStorage/GoogleDrive-renaud@bluegreen.ai/
  Drive partagés/PARTENAIRES/IC Ingénieurs Conseils/
  Marche2026/Demande de Devis/mission-2026-04-07-19-rue-dohi/context.json
```

---

## How to run a render test

```bash
# From the plugin directory
uv run \
  --with "docxtpl>=0.18" \
  --with pillow \
  python3 render_report.py \
  "<path-to-context.json>" \
  --photos-dir "<path-to-photos>" \
  --output tests/output_<type>.docx
```

Open the output in Word / LibreOffice to verify layout.
