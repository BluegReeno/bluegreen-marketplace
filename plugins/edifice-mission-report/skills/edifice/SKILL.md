---
name: edifice
description: >
  This skill should be used when the user is in a directory containing a
  *.edifice.md file, or asks to "pull an Edifice mission", "generate an
  Edifice report", "create a diagnostic report", "generate a devis", or
  "run edifice". Also activates when the user says "/edifice pair" or
  "pair edifice" or "connecter edifice" when the laptop has not been
  paired yet.
version: 0.5.0
allowed-tools: "Bash(uv *) Bash(pip *) Bash(python3 *) Bash(python *) Bash(curl *) Bash(chmod *) Bash(mkdir *) Bash(find *) Bash(ls *) Read Write Edit Glob"
---

# Edifice — Mission Workflow (Claude Code)

## Plugin directory

```bash
# Resolve PLUGIN_DIR — priority: config.json → env var → marketplace cache → known dev paths → error
PLUGIN_DIR=$(python3 - <<'PYEOF'
import json, os, pathlib, sys

home = pathlib.Path.home()

# 1. config.json explicit plugin_dir
cfg = home / '.edifice-mission-report' / 'config.json'
if cfg.exists():
    try:
        d = json.loads(cfg.read_text())
        pd = d.get('plugin_dir', '')
        if pd and pathlib.Path(pd, 'download_photos.py').exists():
            print(pd); sys.exit(0)
    except Exception:
        pass

# 2. env var
env = os.environ.get('EDIFICE_PLUGIN_DIR', '')
if env and pathlib.Path(env, 'download_photos.py').exists():
    print(env); sys.exit(0)

# 3. Claude Code marketplace cache (bluegreen-marketplace or legacy edifice-marketplace)
for _mkt in ['bluegreen-marketplace', 'edifice-marketplace']:
    cache_root = home / '.claude' / 'plugins' / 'cache' / _mkt / 'edifice-mission-report'
    if cache_root.exists():
        candidates = sorted(cache_root.glob('*/download_photos.py'), key=lambda p: p.stat().st_mtime, reverse=True)
        if candidates:
            print(str(candidates[0].parent)); sys.exit(0)

# 4. Cowork app sandbox: /sessions/*/mnt/.remote-plugins/plugin_*/download_photos.py
import glob as _glob
for pat in ['/sessions/*/mnt/.remote-plugins/*/download_photos.py']:
    matches = sorted(_glob.glob(pat), key=lambda p: os.path.getmtime(p), reverse=True)
    if matches:
        print(os.path.dirname(matches[0])); sys.exit(0)

# 5. Known dev paths (Mac + Windows)
for dev_path in [
    home / 'Projects' / 'edifice' / 'plugins' / 'edifice-mission-report',
    home / 'projects' / 'edifice' / 'plugins' / 'edifice-mission-report',
    pathlib.Path('C:/Users') / os.environ.get('USERNAME', '') / 'Projects' / 'edifice' / 'plugins' / 'edifice-mission-report',
]:
    if dev_path.joinpath('download_photos.py').exists():
        print(str(dev_path)); sys.exit(0)

print('PLUGIN_DIR_NOT_FOUND')
PYEOF
)
if [ "$PLUGIN_DIR" = "PLUGIN_DIR_NOT_FOUND" ]; then
  echo "ERROR: Plugin dir introuvable. Lance /edifice pair ou définis EDIFICE_PLUGIN_DIR."
  exit 1
fi
```

## Path resolution — run at the start of every command

```bash
# Briefing file in current directory
BRIEFING=$(find . -maxdepth 1 -name "*.edifice.md" | head -1)
echo "Briefing: $BRIEFING"

# Mission output dir (created by /edifice pull)
MISSION_DIR="./mission"
```

---

## /edifice pull

Pull mission data via the **hal-mcp** server. Reads the `*.edifice.md`
briefing, fetches project + building + notes + photos (with signed URLs) from
Supabase through the `get_mission_with_assets` MCP tool, writes
`mission/context.json`, then downloads the photos.

### Steps

**1. Parse mission ID from briefing**
```bash
BRIEFING=$(find . -maxdepth 1 -name "*.edifice.md" | head -1)
python3 -c "
import re, pathlib, sys
text = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')
m = re.search(r'edifice_mission_id:\s*([0-9a-f-]{36})', text)
print(m.group(1) if m else 'NOT_FOUND')
" "$BRIEFING"
```

**2. Call MCP tool `get_mission_with_assets`** with the mission UUID. The
response contains: `project`, `building`, `notes[]`, `photos[]` (each with
`signed_url` valid 1h), `note_count`, `photo_count`.

**3. Build `mission/context.json`** from the MCP response. Use the unified
vocabulary end-to-end (see `/edifice improve` below for the per-type schema).

- `project_type` ← `project.type` (`diagnostic` | `suivi_chantier` | `devis`)
- Header fields (`titre_service`, `client`, `residence`, `adresse`,
  `code_postal_ville`, `description_batiment`, `ref_dossier`, `date_visite`,
  `objet_visite`, `synthese`, `conclusion`) ← derived from
  `project.mission_context` + `building`
- `observations[]` ← `notes[]`, one per note, with the unified fields:
  `ref`, `note_id`, `name`, `zone`, `location`, `description`, `assessment`,
  `recommendations`, `metadata`. For each observation, attach `photos[]`
  (and `photo` for templates that take a single one) — the filenames of
  photos whose `note_id` matches the observation.
- `photos[]` ← the full photos array from the MCP response (with `signed_url`)
- `building_id` ← `project.building_id`

Write the result to `./mission/context.json` with the Write tool.

**4. Download photos via signed URLs**
```bash
python3 $PLUGIN_DIR/download_photos.py ./mission/context.json ./mission/photos/
```

No auth needed — signed URLs are pre-authorized.

**5. Display mission summary**

Print: mission name, type, building, note count, photo count, then one line
per observation: `ref | zone | assessment | name | description[:80]`.

Mention the mission type — it determines which template `/edifice report`
will use.

---

## /edifice improve

The user describes improvements to one or more observations. Claude reads
`mission/context.json`, edits the relevant entries directly, then confirms.

### How to handle the user's request

1. Read `mission/context.json` with the Read tool.
2. Understand what the user wants to change:
   - "note 3 doit mentionner une fissure de 3mm" → update `observations[2].description`
   - "groupe toutes les notes par zone APT/BAL/CAV/FAC et ajoute les assessments"
     → update `zone` and `assessment` fields for all observations, and rename
     `ref` (APT-01, etc.)
   - "améliore la description de l'observation APT-02" → enrich the `description`
   - "ajoute une synthèse globale" → update the `synthese` field
3. Edit `mission/context.json` with the Edit tool (or Write to replace entirely for
   large restructures).
4. Show the user a diff-style summary of what changed.

### Vocabulaire unifié — observations

Tous les types utilisent les mêmes noms de champs côté `observations[]` :

| Champ | Rôle |
|-------|------|
| `note_id` | UUID de la note source (requis pour `/edifice push`) |
| `ref` | Référence affichée (`OBS-01`, `V1-02`, `APT-03`, etc.) |
| `name` | Nom court de l'observation |
| `zone` | Zone / regroupement (`Chambre 1`, `APT`, `BAL`, etc.) |
| `location` | Localisation précise (`linteau fenêtre nord`, `10ème — Façade Est`) |
| `description` | Texte principal — désordre observé / commentaire |
| `assessment` | Qualification (voir tableau par service_type ci-dessous) |
| `recommendations` | Action / proposition de réparation |
| `metadata` | Données libres (JSONB) |

### Context.json — champs éditables par type

**`diagnostic`** — header : `description_batiment`, `objet_visite`, `synthese`, `conclusion`
Observations : `zone`, `location`, `description`, `assessment`, `recommendations`

**`suivi_chantier`** — header : `participants`, `objet_visite`, `synthese`, `conclusion`
Observations : `location`, `description`, `assessment`, `recommendations`

**`devis`** — header : `type_acteur`, `interlocuteur_nom`, `interlocuteur_role`,
`declencheur`, `livrable`, `urgence`, `description_batiment`, `documents_fournis`,
`proposition_mission`, `incertitudes`, `chiffrage`
Observations : `location`, `description`, `metadata.donnees_cles`, `metadata.ref_photo`

### Valeurs de `assessment` par service_type

| service_type | values |
|--------------|--------|
| `diagnostic` (note type=`disorder`) | `"1"`, `"2"`, `"3"`, `"4"`, `"-"` |
| `suivi_chantier` | `"observation"`, `"a_faire"`, `"reserve"` |
| `devis` | `null` / absent |

**Échelle diagnostic** :
- `"1"` = Risque de ruine immédiate → mise en sécurité immédiate
- `"2"` = Désordres graves sans ruine → réparation court terme
- `"3"` = Dégradation sans gravité → entretien moyen terme
- `"4"` = Dégradation légère → entretien long terme
- `"-"` = Non applicable / bon état

Source de vérité (mapping `assessment` → `condition_index`, labels, etc.) :
`organizations/ic-ingenieurs/assessment-config.json`.

---

## /edifice report

Generate the DOCX report from the current `mission/context.json`.
Uses `render_report.py` — a unified dispatcher that requires no Supabase connection.

### Steps

**1. Generate (all types — diagnostic, suivi_chantier, devis)**
```bash
uv run \
  --with "docxtpl>=0.18" \
  --with pillow \
  python3 $PLUGIN_DIR/render_report.py \
  mission/context.json \
  --photos-dir mission/photos \
  --output mission/rapport.docx
```

`render_report.py` reads `project_type` from `context.json` and routes automatically:
- `diagnostic`      → `render_diagnostic.py`  + `templates/ic-ingenieurs/diagnostic.docx`
- `suivi_chantier`  → `render_cr_visite.py`   + `templates/ic-ingenieurs/suivi_chantier.docx`
- `devis`           → `render_devis.py`        + `templates/ic-ingenieurs/devis.docx`

Org override: `--org ic-ingenieurs` (default) or env var `EDIFICE_ORG=ic-ingenieurs`.

**2. Confirm to user**
Tell the user: "Rapport généré : `mission/rapport.docx`" and provide the file path.

---

## Types de rapports — schemas JSON et renderers

### `diagnostic` — Rapport de diagnostic structurel
Renderer : `render_diagnostic.py` | docxtpl + `templates/ic-ingenieurs/diagnostic.docx`

```json
{
  "project_type": "diagnostic",
  "titre_service": "Diagnostic structurel planchers bois",
  "client": "",
  "residence": "Rue de varenne",
  "adresse": "46 Rue de Varenne 75007 Paris",
  "ref_dossier": "",
  "date_visite": "2026-04-28",
  "description_batiment": "Hôtel particulier XVIIIe siècle...",
  "objet_visite": "Dans le cadre d'une rénovation complète...",
  "synthese": "Le diagnostic révèle...",
  "conclusion": "",
  "observations": [
    {
      "ref": "OBS-01",
      "note_id": "uuid",
      "name": "Plancher fléchi chambre 1",
      "zone": "Chambre 1",
      "location": "Plancher — côté fenêtre",
      "description": "Flèche visible du plancher bois",
      "assessment": "3",
      "recommendations": "Contrôle des appuis des solives",
      "photo": "filename.jpg"
    }
  ]
}
```

Zones valides : libre (par pièce ou par type).
Assessment (diagnostic) : voir tableau dans `/edifice improve`.

### `suivi_chantier` — Compte-rendu de visite de chantier
Renderer : `render_cr_visite.py` + `templates/ic-ingenieurs/suivi_chantier.docx`

```json
{
  "project_type": "suivi_chantier",
  "titre_service": "Suivi réfection balcons",
  "client": "SDC ...",
  "residence": "Résidence ...",
  "batiments_visites": "Bâtiment A",
  "adresse": "...",
  "code_postal_ville": "93600 Aulnay-sous-Bois",
  "ref_dossier": "DE0328",
  "date_visite": "2026-04-28",
  "participants": [
    {"nom": "R. Laborbe", "fonction": "M.O", "entreprise": "IC Ingénieurs Conseils", "contact": "06 50 96 61 98"}
  ],
  "objet_visite": "IC Ingénieurs Conseils assure le suivi...",
  "synthese": "L'inspection a permis...",
  "conclusion": "La visite confirme...",
  "observations": [
    {
      "ref": "V1-01",
      "note_id": "uuid",
      "name": "Traces de truelle façade Est",
      "location": "10ème — Façade Est",
      "description": "Traces de truelle visibles",
      "assessment": "a_faire",
      "recommendations": "Reprendre les traces",
      "photo": "photo1.jpg"
    }
  ]
}
```

### `devis` — Rapport préliminaire / demande de devis
Renderer : `render_devis.py` | docxtpl + `templates/ic-ingenieurs/devis.docx`

```json
{
  "project_type": "devis",
  "titre_service": "Diagnostic structurel planchers bois",
  "client": "Nom du client",
  "type_acteur": "Particulier",
  "interlocuteur_nom": "Jean Dupont",
  "interlocuteur_role": "Propriétaire",
  "interlocuteur_contact": "email — tel",
  "type_mission": "Diagnostic",
  "declencheur": "Travaux de rénovation ayant révélé des dégradations structurelles",
  "livrable": "Rapport DOCX avec observations et recommandations",
  "urgence": "Normal",
  "adresse": "46 Rue de Varenne 75007 Paris",
  "type_batiment": "Immeuble résidentiel — hôtel particulier",
  "annee_construction": "XVIIIe siècle",
  "nb_etages": "R+2 + combles",
  "description_batiment": "...",
  "documents_fournis": [
    {"document": "Plans architecte", "fourni": false}
  ],
  "observations": [
    {
      "note_id": "uuid",
      "name": "Linteau dégradé chambre 1",
      "location": "Chambre 1",
      "description": "Linteau dégradé, pourriture avancée",
      "metadata": {
        "donnees_cles": "L=2,20m — section 25×25cm",
        "ref_photo": "P1"
      }
    }
  ],
  "proposition_mission": "Diagnostic structurel complet...",
  "incertitudes": "Accès conditionné à la dépose des faux-plafonds.",
  "chiffrage": [
    {"prestation": "Déplacement terrain", "nb_heures": "2", "montant_ht": ""},
    {"prestation": "Visite terrain", "nb_heures": "3", "montant_ht": ""},
    {"prestation": "Rédaction du rapport", "nb_heures": "4", "montant_ht": ""}
  ],
  "technicien": "R. Laborbe",
  "date_visite": "2026-04-28",
  "date_envoi": ""
}
```

---

## /edifice push

Push the updated `mission/context.json` observations back to Supabase
(`edifice_notes` table) via the **hal-mcp** `push_mission_context` tool.

### Steps

**1. Read `mission/context.json`** with the Read tool.

**2. Call MCP tool `push_mission_context`** with:
- `observations`: each observation that has a `note_id`, including any subset
  of `description`, `location`, `zone`, `assessment`, `recommendations`,
  `metadata` (only fields that were edited need to be sent — the MCP applies
  partial updates)
- `building_id` + `building_description`: include only if the building
  description was enriched

The MCP tool auto-maps `assessment` → `condition_index` for diagnostic
missions (`"1" | "2"` → `poor`, `"3"` → `medium`, `"4" | "-"` → `good`).

**3. Confirm to user**
Report `{ updated, skipped, errors }` from the MCP response.

