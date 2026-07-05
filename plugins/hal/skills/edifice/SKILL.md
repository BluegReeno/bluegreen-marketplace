---
name: edifice
description: >
  This skill should be used when the user is in a directory containing a
  *.edifice.md file, or asks to "pull an Edifice mission", "generate an
  Edifice report", "create a diagnostic report", "generate a devis", or
  "run edifice".
version: 0.3.2
allowed-tools: "Bash(uv *) Bash(pip *) Bash(python3 *) Bash(python *) Bash(curl *) Bash(chmod *) Bash(mkdir *) Bash(find *) Bash(ls *) Read Write Edit Glob"
---

# Edifice — Mission Workflow (Claude Code)

## Plugin directory

```bash
# Resolve PLUGIN_DIR — priority: config.json → env var → marketplace cache → known dev paths → error
PLUGIN_DIR=$(python3 - <<'PYEOF'
import json, os, pathlib, sys

home = pathlib.Path.home()

# 1. env var
env = os.environ.get('HAL_PLUGIN_DIR', '')
if env and pathlib.Path(env, 'scripts', 'build_context.py').exists():
    print(env); sys.exit(0)

# 2. Claude Code marketplace cache (bluegreen-marketplace)
for _mkt in ['bluegreen-marketplace']:
    cache_root = home / '.claude' / 'plugins' / 'cache' / _mkt / 'hal'
    if cache_root.exists():
        candidates = sorted(cache_root.glob('*/scripts/build_context.py'), key=lambda p: p.stat().st_mtime, reverse=True)
        if candidates:
            print(str(candidates[0].parent.parent)); sys.exit(0)

# 3. Cowork app sandbox: /sessions/*/mnt/.remote-plugins/plugin_*/scripts/build_context.py
import glob as _glob
for pat in ['/sessions/*/mnt/.remote-plugins/*/scripts/build_context.py']:
    matches = sorted(_glob.glob(pat), key=lambda p: os.path.getmtime(p), reverse=True)
    if matches:
        print(os.path.dirname(os.path.dirname(matches[0]))); sys.exit(0)

# 4. Known dev paths (Mac + Windows)
for dev_path in [
    home / 'Projects' / 'bluegreen-marketplace' / 'plugins' / 'hal',
    home / 'projects' / 'bluegreen-marketplace' / 'plugins' / 'hal',
    pathlib.Path('C:/Users') / os.environ.get('USERNAME', '') / 'Projects' / 'bluegreen-marketplace' / 'plugins' / 'hal',
]:
    if dev_path.joinpath('scripts', 'build_context.py').exists():
        print(str(dev_path)); sys.exit(0)

print('PLUGIN_DIR_NOT_FOUND')
PYEOF
)
if [ "$PLUGIN_DIR" = "PLUGIN_DIR_NOT_FOUND" ]; then
  echo "ERROR: Plugin dir introuvable. Définis HAL_PLUGIN_DIR=<chemin> dans ton shell."
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

## Pre-flight : vérifier hal-mcp

Requis pour `list`, `pull`, et `push`. Pas nécessaire pour `improve` et `report`.

1. Appeler `list_edifice_missions` avec `limit: 1`
2. **Succès** → continuer normalement
3. **Échec** (outil indisponible / connexion refusée / timeout) :

> ❌ **hal-mcp non connecté.**
> Reconnexion : **Claude Desktop → Paramètres → Connexions → hal-mcp → Activer**
> ⚠️ Ne pas lancer de commandes terminal — interface graphique uniquement.

---

## /edifice list

List Edifice missions sorted from newest to oldest. Use this to find the
`mission_id` before running `/edifice pull`.

### Steps

**1. Call MCP `list_edifice_missions`**

Optional filters the user can provide:
- `status=<value>` — e.g. `active`, `completed`
- `limit=N` — max results (default 50)

If the user typed `/edifice list active`, pass `status: "active"`.
If the user typed `/edifice list` with no arguments, call with no filters.

**2. Format and display**

Format the response as a markdown table. The `building` field may be null —
show `—` in that case. The `mission_context` field must NOT be displayed.

```
| Date       | Nom                       | Type           | Statut    | Bâtiment / Adresse              |
|------------|---------------------------|----------------|-----------|---------------------------------|
| 2026-05-28 | Diagnostic Varenne        | diagnostic     | active    | 46 Rue de Varenne 75007 Paris   |
| 2026-05-12 | Suivi chantier Aulnay     | suivi_chantier | completed | Résidence Les Tilleuls          |
```

Extract the date as `YYYY-MM-DD` from the `created_at` ISO timestamp.
If `building` is null, show `—` in the Bâtiment column.
If 0 results are returned, tell the user "Aucune mission trouvée."

**3. Surface the mission_id**

After the table, add:

```
Pour puller une mission : /edifice pull avec mission_id = <UUID>

Exemple : mission_id de "Diagnostic Varenne" = 2d3138cb-7bdb-4236-a29f-5ea51883b363
```

If only one result is returned (e.g. `limit=1`), show the UUID inline below the table.
If multiple results, list all UUIDs at the end or on request.

---

## /edifice pull

Three steps. Claude does only step 2 (one MCP call + one file write).
The script handles everything else deterministically.

### Steps

**1. Parse mission ID from briefing**
```bash
BRIEFING=$(find . -maxdepth 1 -name "*.edifice.md" | head -1)
MISSION_ID=$(python3 -c "
import re, pathlib, sys
text = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')
m = re.search(r'edifice_mission_id:\s*([0-9a-f-]{36})', text)
print(m.group(1) if m else 'NOT_FOUND')
" "$BRIEFING")
echo "Mission ID: $MISSION_ID"
```

**2. Call MCP `get_mission_with_assets`** with `MISSION_ID`.
The result has shape `{ download_url, note_count, photo_count, expires_in }`.
Set `DOWNLOAD_URL` to the `download_url` value. Then:
```bash
mkdir -p mission
curl -s "$DOWNLOAD_URL" > mission/mcp_response.json
```
The URL expires in 300 s — run `curl` immediately after the MCP call.

**3. Run build_context.py**
```bash
mkdir -p mission
python3 $PLUGIN_DIR/scripts/build_context.py mission/mcp_response.json ./mission --photos-dir ./mission/photos
```

The script builds `mission/context.json` with all fields pre-filled for the
mission's `project_type`, maps notes → observations, and downloads all photos
from their signed URLs. It prints the summary.

Each entry in `photos[]` is a verbatim pass-through from the MCP response and
may carry `crop_region` and `annotations` when the technician has previously
used edifice's local-workspace desktop tool (a separate offline app, not part of
this skill) to crop or annotate photos. These fields are informational passthrough
only — Cowork reads them solely to print a diagnostic count in the console
(`_count_local_workspace_data`), but does not write or offer any UI for
`crop_region` / `annotations`; editing them is exclusively local-workspace's
responsibility.

---

## /edifice improve

This is the intelligence step. The user reviews notes and photos with Claude,
qualifies observations, and reclassifies notes if needed. Claude reads
`mission/context.json`, edits entries directly, then confirms.

### How to handle the user's request

1. Read `mission/context.json` with the Read tool.
2. Understand what the user wants:
   - "note 3 doit mentionner une fissure de 3mm" → update `observations[2].description`
   - "groupe par zone APT/BAL/CAV/FAC et ajoute les IE" → update `zone` + `assessment` for all observations, rename `ref`
   - "améliore la description de OBS-02" → enrich the `description`
   - "ajoute une synthèse globale" → update the `synthese` field
3. Edit `mission/context.json` with the Edit tool (Write for large restructures).
4. Show the user a diff-style summary of what changed.

### Reclassifying notes ↔ observations

Context: `observations[]` = structured notes (disorder/reservation, need qualification).
`notes[]` = free notes (reminders, context — no required fields).

The technicien classifies note types on the PWA during field capture, but they
can be wrong or uncertain. During `/edifice improve`, review photos together and
reclassify if needed:

**From `notes[]` → `observations[]`** (e.g. a facade photo that is actually a structural defect):
- Move the entry from `notes[]` to `observations[]`
- Add the required fields for the mission type (zone + assessment + recommendations for diagnostic)
- Set `type` to `"disorder"` (diagnostic) or `"reservation"` (suivi_chantier)

**From `observations[]` → `notes[]`** (e.g. a note logged as disorder that is just context):
- Move the entry to `notes[]`, remove structured fields
- Set `type` to `"note"`

`/edifice push` will persist the reclassification (`type` field) back to Supabase,
so future pulls will route correctly automatically.

### Methodo tags — notes de méthodologie (diagnostic uniquement)

Notes dont `metadata.tag` est `methodo:visite_terrain` ou `methodo:moyens` sont rendues
automatiquement dans la section Méthodologie du rapport diagnostic :

| Tag | Section du rapport |
|-----|-------------------|
| `methodo:visite_terrain` | Visites terrain réalisées |
| `methodo:moyens` | Moyens mis en œuvre |

Ces notes restent dans `notes[]` (pas reclassées en `observations[]`). Une photo par note,
rendue à taille moyenne. Pour taguer une note depuis `/edifice improve` :

```
notes[n].metadata.tag = "methodo:visite_terrain"
```

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
  python3 $PLUGIN_DIR/scripts/render_report.py \
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

