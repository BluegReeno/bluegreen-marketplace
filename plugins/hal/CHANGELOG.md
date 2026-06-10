# Changelog — hal

All notable changes to this plugin are documented here.

## Versioning convention

Per-component versioning (see repo `CLAUDE.md`). Each component (plugin, skill `edifice`,
skill `hal`, MCP `hal-mcp`) tracks its own SemVer-ish version. Plugin PATCH bumps once per
release; component PATCH bumps only when that component changes.

`0.MINOR.PATCH` (pré-1.0) :
- **PATCH** (`0.x.Y+1`) — bugfix, ajout de champ optionnel, amélioration interne sans impact sur l'interface
- **MINOR** (`0.X+1.0`) — changement d'interface utilisateur : nouveau champ obligatoire dans le JSON, renommage de commande CLI, changement de comportement observable

Règle : les refactors internes (changement de librairie, restructuration code) qui ne modifient pas l'interface publique → PATCH, pas MINOR.

---

## [0.7.0] — 2026-06-10 — Hal Lot 2 — tâches et sprints

### Added
- **Skill `hal` 0.4.1 → 0.5.0** — Lot 2 tâches :
  - `/hal tasks [workspace]` — liste les tâches en kanban texte groupé par statut
    (todo → in_progress → blocked → ✓ done). Filtres : `--mine`, `--project <ref>`,
    `--status`. Pur MCP, zéro script.
  - NL task intents dans `/hal update` : créer (`create_task`), mettre à jour
    (`update_task_status`), assigner à un sprint (`assign_task_to_sprint`).
  - `create_sprint` — disponible sur tout workspace avec `sprints_enabled = true`.
  - Workspace resolution via `HAL_DEFAULT_WORKSPACE` env var — plus de hardcode
    `blue-green`. Chaque client configure son workspace par défaut une seule fois.
- **`commands/hal.md`** — `tasks` subcommand ajouté au routing.

### Changed
- `/hal list` — workspace resolution migré de `blue-green` hardcodé vers
  `HAL_DEFAULT_WORKSPACE` env var (même pattern que `/hal tasks`).

### Removed
- "Tasks and sprints — not yet available" dans "Out of scope" — replaced by
  real current limitations (no task field update, no list_sprints, project_id join).

### Prerequisites (hal-mcp — deployed v28, PRs #38 #39 — 2026-06-08)
- `update_task_status` accepts `workspace_slug` ✅
- `sprints_enabled = true` for `blue-green` workspace ✅

---

## [0.6.0] — 2026-06-08 — Direct `/hal` + `/edifice` commands + MCP pre-flight

### Added
- **`commands/hal.md`** — registers `/hal` as a first-class slash command. Enables
  `/hal list`, `/hal update`, `/hal devis` without `hal:hal` prefix or semantic trigger.
  Self-contained: includes routing table and MCP pre-flight inline.
- **`commands/edifice.md`** — same for `/edifice`: `list`, `pull`, `improve`, `report`, `push`.
  MCP check for network-dependent subcommands; `improve` and `report` skip the check.
- **Skill `hal` 0.4.0 → 0.4.1** — MCP pre-flight check section added: verify hal-mcp via
  `list_stages` before any CRM operation; surface reconnection instructions (Claude Desktop
  GUI only, no terminal) if unavailable.
- **Skill `edifice` 0.3.0 → 0.3.1** — same MCP pre-flight check added (`list_edifice_missions`).
- **`docs/skills-mcp-guide.md`** — reference: skill vs command architecture, MCP detection
  pattern, agentskills.io cross-platform spec, version field notes, validation commands.
- **`CLAUDE.md`** — `commands/` added to repo structure; skills-vs-commands section added.

---

## [0.5.0] — 2026-06-08 — Skill `/hal list`

### Added
- **Skill `hal` 0.3.0 → 0.4.0** — `/hal list [workspace]` command: displays the CRM
  pipeline as a text kanban grouped by stage. Defaults to workspace `blue-green`;
  accepts an optional workspace slug arg (`ic`, `blue-green`, or any slug).
  Supports optional `stage=<value>` and `kind=<value>` filters.
  No scripts — pure MCP tool call via `list_projects`, zero cold-start cost.

---

## [0.4.0] — 2026-06-06 — Skill `/edifice list` + fix plugin.json version gap

### Added
- **Skill `edifice` 0.2.0 → 0.3.0** — `/edifice list` command: lists Edifice missions
  sorted newest-first via MCP `list_edifice_missions`. Displays date, name, type,
  status, building address, and mission UUID. Supports optional `status=<value>` and
  `limit=N` filters. No scripts — pure MCP tool call, zero cold-start cost.

### Fixed
- `plugin.json` and `marketplace.json` bumped from `0.2.0` to `0.4.0` to match
  the CHANGELOG (the `0.3.0` entry was written but the json files were not updated
  in that session).

---

## [0.3.0] — 2026-06-06 — Skill `/edifice pull` server-side export via Storage

### Changed (interface — MINOR bump)
- **Skill `edifice` 0.1.1 → 0.2.0** — `/edifice pull` step 2 changed: `get_mission_with_assets`
  now returns `{ download_url, note_count, photo_count, expires_in }` instead of the full JSON payload.
  Skill now runs `curl -s "$DOWNLOAD_URL" > mission/mcp_response.json` immediately after the MCP call.
  The URL expires in 300 s. No change to `/edifice push`, `/edifice improve`, or `/edifice report`.

---

## [0.2.0] — 2026-06-05 — Skill `/hal` routes BG-CRM writes to Supabase via hal-mcp

### Changed (interface — MINOR bump)
- **Skill `hal` 0.1.0 → 0.2.0** — full rewrite. `/hal update` no longer writes to the
  Obsidian vault. Natural-language instructions are routed to the `hal-mcp` MCP
  connector (Supabase backend) for the BlueGreen CRM workspace (`workspace_slug:
  "blue-green"`, hard-coded).
- **Skill is now 100% instructions** — zero scripts, zero Bash. The `allowed-tools`
  frontmatter field is intentionally removed (validated 2026-06-05). MCP tools come
  from the user-level connector and are available as soon as the server is connected.

### Removed
- `scripts/hal_update.py` — replaced by direct MCP tool calls
  (`list_missions` → `update_mission_stage`, `log_interaction`, `create_company`,
  `create_contact`, `create_mission`, `list_companies`, `list_contacts`). Git
  history is the only archive.
- Vault path resolution (`VAULT_PATH`), plugin path resolution (`PLUGIN_DIR`),
  vault folder structure reference, and NL→frontmatter field mapping from
  `SKILL.md` — none of it applies to the Supabase routing.

### Architecture
- **BlueGreen CRM** (missions / contacts / companies / interactions) lives in
  Supabase and is reached only through `hal-mcp`. `/hal` is its natural-language
  front-end.
- **Job Search** stays in the Obsidian vault, handled by `obsidian-crm`. `/hal`
  never touches the vault — no routing, no exceptions.
- Entity resolution is client-side fuzzy matching on `list_*` results (server has
  no search endpoint): score > 80 → write, 50–80 → propose candidates, < 50 →
  propose creation (never auto-create). Match on mission name (company can be
  null and often hosts many missions); always filter `list_missions` by `stage`
  to keep payloads small.

### Scope (lot 1 only)
- In: missions, companies, contacts, interactions.
- Out (lot 2, waiting on server CRUD): tasks and sprints
  (`create_task` / `list_tasks` / `update_task` not yet on the MCP surface).
- Out (server limitation): field updates outside `stage` on companies / contacts
  / missions.

### Plugin
- Plugin `hal` 0.1.2 → **0.2.0** (interface change in the `hal` skill).
- Marketplace registry aligned to 0.2.0.

---

## [0.1.1] — 2026-05-30 — IGN 2D map in diagnostic reports (Plan C)

### Added
- `build_context.py`: `build_building_context()` — attaches 2D map to context.json.
  Strategy: `building_2d_map_url` → download; lat/lon fallback → IGN WMS PLANIGNV2; else None.
- `render_diagnostic.py`: `_building_block()` — converts local path to `InlineImage` for docxtpl.
- `templates/ic-ingenieurs/diagnostic.docx`: `{%p if building.image_2d %}` block — 2D map section.

### Fixed
- `build_building_context()`: fallback log now correctly distinguishes "URL absent" from "download failed" to simplify debugging when `building_2d_map_url` is set but the download fails (expired signed URL, network error).

---

## [0.1.0] — 2026-05-28 — HAL plugin : renommage + skill /hal (Obsidian vault)

### Changed
- Plugin renommé `edifice-mission-report` → `hal`.
- Scripts edifice déplacés à la racine du plugin → `scripts/` pour aligner avec la structure mixte (edifice + hal). Le `PLUGIN_DIR` reste la racine du plugin ; les renderers résolvent désormais `templates/` via `__file__.parent.parent`.
- Skill `edifice` : version reset à 0.1.0 sous le plugin renommé (l'historique précédent reste documenté ci-dessous).
- `EDIFICE_PLUGIN_DIR` env var → `HAL_PLUGIN_DIR`.

### Added
- Skill `hal` v0.1.0 — `/hal update` : mise à jour du vault Obsidian SecondLife depuis une instruction en langage naturel.
- `scripts/hal_update.py` — NL parser + orchestrateur des writes via les scripts `obsidian-crm`.
- `scripts/obsidian/` — bundle des scripts `obsidian-crm` (vault I/O, source de vérité unique pour le plugin) + `references/schemas.md` (11 types de notes CRM).
- `requirements.txt` : `rapidfuzz>=3.0` pour le fuzzy matching des titres de notes.
- `.mcp.json` : champ `version: 0.1.0` sur l'entrée `hal-mcp` (versioning explicite du MCP).

### Architecture
- Politique de versioning par composant documentée dans `CLAUDE.md` (plugin / skill / MCP indépendants).
- `/hal` v0.2.0 (future) — migration data layer Obsidian → Supabase via les outils CRM `hal-mcp`, quand la migration sera prête.

---

## Legacy — edifice-mission-report

Historique avant le renommage en `hal`.

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
