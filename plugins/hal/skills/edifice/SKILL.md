---
name: edifice
description: >
  This skill should be used when the user is in a directory containing a
  *.edifice.md file, or asks to "pull an Edifice mission", "generate an
  Edifice report", "create a diagnostic report", "generate a devis",
  "open the edifice front", "show the mission viewer artifact", or
  "run edifice".
allowed-tools: "Bash(uv *) Bash(pip *) Bash(python3 *) Bash(python *) Bash(curl *) Bash(chmod *) Bash(mkdir *) Bash(find *) Bash(ls *) Read Write Edit Glob ToolSearch ListConnectors mcp__plugin_hal_hal-mcp__list_edifice_missions mcp__plugin_hal_hal-mcp__get_mission_with_assets mcp__plugin_hal_hal-mcp__push_mission_context"
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
> Le serveur est fourni par le plugin `hal` (`plugin:hal:hal-mcp`).
> Reconnexion : `/mcp` → `plugin:hal:hal-mcp` → `authenticate`.
> Relancer la commande après reconnexion.

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

**Existing `context.json` is never silently overwritten.** If `mission/context.json`
already exists (e.g. from a previous `/edifice improve` session not yet pushed),
the script renames it to `mission/context.json.bak-<timestamp>` before writing the
new one, and prints `⚠️  Existing context.json preserved → …`. If you see that
warning, check the backup file for unpushed edits before discarding it.

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

**Known issue — `null value in column "project_id"`**
If `errors` contains `null value in column "project_id" of relation "edifice_notes"
violates not-null constraint`, this is a **backend bug** in `push_mission_context`
(hal-mcp), not a problem with the `observations` payload — do not retry with a
different `note_id` or `type`. `push_mission_context` must UPDATE existing
`edifice_notes` rows by `note_id` (preserving their `project_id`), never INSERT.
Report the error to the user and point them to the `hal-mcp` repo for a fix; this
skill's contract (partial updates keyed by `note_id`) is unaffected.

---

## /edifice front

Generates and **publishes a read-only Claude Cowork live artifact** for browsing Edifice
missions (mission list, notes, photos) — a ported slice of the `edifice` monorepo's
`local-workspace` annotation UI, built from `ui/edifice-front/` and consuming
`@bluegreeno/annotation-core`. Full architecture (MCP invocation API, sandbox
constraints, why this is Cowork-only in v1): `docs/artifact-front-ends.md` and issue #50.
Root-cause history for why this route never worked before this fix: issues #54, #56, #60
and PRs #55, #57, #58, #59 (closed unmerged — do not reopen its approach, see step 4).

**Precondition**: this route only works in a **local** Claude Cowork session — one running
on the user's machine. Step 0 below stops it before anything is generated in a cloud/remote
session. It also depends on step 2 reading the connector registry through Cowork's
`ListConnectors` tool, which Claude Code CLI does not expose. The UUID it returns is the only
id `window.cowork.callMcpTool` can resolve; the session's own MCP tool names are **not** a
source for it (in Cowork hal-mcp is exposed under its short name,
`mcp__hal-mcp__list_edifice_missions`, so deriving the UUID from tool names yields
`hal-mcp` and the artifact fails to load).

### Steps

**0. Guard — refuse cloud/remote sessions before generating anything**

Check the tool names available in this session. If any is prefixed `mcp__remote-devices__`
(e.g. `mcp__remote-devices__create_artifact`), this is a **cloud Cowork session**, not a
local one — stop immediately, before reading the template or writing anything:

> ❌ `/edifice front` ne peut pas publier depuis une session cloud. Les serveurs MCP
> locaux/projet (dont hal-mcp) ne tournent pas côté session distante, et l'outil de
> persistance cloud ne transporte pas la déclaration `mcp_tools` faite à la publication —
> la page publiée ne pourrait de toute façon jamais appeler hal-mcp.
> Relancez cette tâche en local (sélecteur « Run this task » → machine locale), puis
> relancez `/edifice front`.

This is not a precaution against a hypothetical bug: verified three ways in the 2026-07-28
session, `mcp__remote-devices__create_artifact` / `update_artifact` never transport the
`mcp_tools` declaration made at publish time — the stored artifact always comes back with
`mcpTools: []`. Worse, calling either against an **existing** artifact overwrites its
working version (this happened to `edifice-front` during diagnosis). **Never call
`create_artifact` / `update_artifact` via `mcp__remote-devices__*` for this route** — guard
or no guard, there is no scenario where that path produces a working artifact.

**1. Read the committed template**

Read `$PLUGIN_DIR/artifacts/edifice-front.html` with the Read tool. Treat it as
read-only input — never write back into `$PLUGIN_DIR`.

**2. Read the hal-mcp connector UUID via `ListConnectors`**

Load the tool schema first — `ToolSearch { query: "select:ListConnectors" }` — then call
`ListConnectors { keywords: ["hal"] }` and take the entry whose server name is `hal-mcp`.
Its `installedServerId` (a UUID, e.g. `7898d523-…`) is `<uuid>` for the steps below. This
value is per-desktop and must never be hardcoded — always re-read it live, every time this
command runs.

Stop and tell the user — without generating a file with an unresolved placeholder — if:

- no `hal-mcp` entry comes back, or
- the entry has `connected: false` or `enabledInChat: false`:

> ❌ hal-mcp non connecté dans cette session Cowork. Activez le connecteur hal-mcp,
> puis relancez `/edifice front`.

**3. Approve the connector — call `list_edifice_missions` once**

Before hydrating or publishing, call `mcp__<uuid>__list_edifice_missions` (the `<uuid>` from
step 2) with `limit: 1`. The returned data is not the point — this call resolves the tool's
real full name once in this live session and approves the hal-mcp connector for use by a
live artifact. Per the recipe confirmed by the session that produced the working "Command
Center" reference artifact, **a live artifact can only use connectors already approved at
creation/update time** — skipping this call is a known way for step 5's publish to grant an
allowlist that resolves nothing at runtime even though every id is spelled correctly.

**4. Hydrate the tool ids**

Replace **every** occurrence of the literal string `PLACEHOLDER_HAL_MCP_UUID` in the
template with the `<uuid>` from step 2 — currently 6: three in the
`<script id="cowork-artifact-meta">` block and three in the bundled JS, which carries
each `mcp__<uuid>__<tool>` id as a full literal. Do not count them and stop; replace
all occurrences, the build may change how many there are.

Never rely on the meta block alone to grant access. Cowork **regenerates**
`cowork-artifact-meta` when it publishes the artifact — the block in the published preamble
is an *output* the platform writes after the publish call, not an input it reads (this was
tested directly in PR #59, closed unmerged: moving/editing that block changes nothing about
the resulting allowlist). What grants access is step 5's `mcp_tools` declaration at publish
time, not any content of the HTML file.

**5. Publish the live artifact — declare `mcp_tools` at publish time**

Publish the hydrated HTML as a Cowork live artifact, using this **local** session's own
artifact-creation tool (search with `ToolSearch` if its schema isn't already loaded — it is
**not** `mcp__remote-devices__create_artifact` / `update_artifact`, forbidden by step 0).
Declare all three full tool ids from step 2 as the artifact's allowed MCP tools:

```
["mcp__<uuid>__list_edifice_missions",
 "mcp__<uuid>__get_mission_context",
 "mcp__<uuid>__get_mission_photo"]
```

**`mcpTools` is a host-enforced allowlist, checked server-side by Cowork — it is not config
read from the HTML.** An empty allowlist refuses every call at runtime no matter how
correctly a tool name is reconstructed inside the bundle (this is exactly the failure mode
step 4 describes). It is declared as a parameter of the publish call itself. Write this step
at the intentional level — "publish this artifact, declaring these three ids as its allowed
MCP tools" — and let Claude map that onto whichever publish tool this session actually
exposes, the same way step 2 maps onto `ListConnectors` without this file hardcoding its
schema.

<!-- TODO: verify in Cowork — the exact name and parameter shape of the local publish tool
     are not confirmed anywhere in this repo or in Anthropic's public docs as of 2026-07-30.
     Do not guess or hardcode a tool name/schema here until a live local Cowork session has
     surfaced it (e.g. by unfolding the "Create an artifact" permission prompt, or asking
     in-session which tool publishes a live artifact and which parameter declares allowed
     MCP tools). -->

<!-- TODO: verify in Cowork — hal-mcp is currently installed as a plugin-level MCP server
     (`plugins/hal/.mcp.json`), not as a claude.ai account-level connector. Anthropic's
     "Artifacts call your MCP connectors" docs (CLI v2.1.209+) state published pages can only
     call account-level connectors, not project/local MCP servers — if that constraint
     applies to this publish path, hal-mcp may also need to be added under
     Settings → Connectors (see docs/connectors-and-skills.md §1b) before this step can work
     at all. Confirm before relying on the recipe above; do not assume it is unnecessary. -->

If no local publish tool that accepts an `mcp_tools`-style declaration can be found or
confirmed, **stop and tell the user**, quoting what was tried — a static HTML file the user
opens and connects manually is not an acceptable substitute for this route (issue #60 §1).

**6. Tell the user**

> Artefact publié : « Edifice Front » — c'est un live artifact Cowork connecté à hal-mcp,
> pas un fichier à ouvrir manuellement. Vérifiez que la liste des missions se charge.

If the publish call returns a viewer URL or artifact id, include it in the message.

### Known Phase 1 scope (read-only)

- Mission list (`list_edifice_missions`), then per-mission Infos/Notes/Photos tabs.
  Only one MCP call happens automatically on artifact open (the mission list); a
  mission's `get_mission_context` and its photos' `get_mission_photo` calls are each
  gated behind a user click (selecting a mission, then opening its Photos tab) — this
  minimizes the load-time permission-dialog risk documented in issue #50, rather than
  eagerly fetching everything on open.
- Rotate/crop/annotate affordances inherited from `@bluegreeno/annotation-core`'s
  `PhotoGallery` are visually present but **not wired to persistence** — any change is
  local to the browser tab and lost on reload. Phase 2 (`push_mission_context`) wires
  real persistence; do not tell users their edits are saved.
- `needs_reauth` / `server_not_connected` errors are never auto-retried; only
  `server_unavailable` offers a retry, once per session — per the error-handling
  contract in `ui/edifice-front/src/cowork-mcp.ts`.

### Validation limit — do not claim this route works until it is proven

This chain can only be proven in a **local Cowork session with a genuinely published
artifact**. A headless run (including the one that wrote this section) can write and reason
about these steps but cannot observe whether Cowork's allowlist honours a declared
`mcp_tools`, whether the step 0 guard fires the way described here, or whether hal-mcp needs
to also be an account-level connector (see step 5's second TODO). Do not report `/edifice
front` as fixed based on a headless run or on reading this file. Any PR touching this section
stays in **draft** until a human has run `/edifice front` in a real local Cowork session and
confirmed a hal-mcp call returns live mission data.

