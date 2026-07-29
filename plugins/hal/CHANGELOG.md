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

## [0.11.5] — 2026-07-29 — linkedin: use an allowed workspace tag

### Fixed
- **`linkedin`** — `idea`, `backlog`, `draft`, and `log` all filtered/created tasks with
  `tags: ["linkedin"]`, but `linkedin` is not in the `blue-green` workspace's `allowed_tags`
  vocabulary (`client`, `commercial`, `finance`, `hr`, `legal`, `marketing`, `memory`,
  `operations`, `other`, `product`). `create_task` rejected every call. Switched to
  `tags: ["marketing"]`, which is allowed and matches the editorial-content nature of the task.

## [0.11.4] — 2026-07-28 — edifice-front: full tool ids as literals — Cowork regenerates the meta block

**Cowork regenerates `cowork-artifact-meta` when it publishes an artifact**, deriving
`mcpTools` from the ids it finds in the code. The artifact read its ids back from that
same block — circular. Its bundle named no tool literally, so the published artifact got
`mcpTools: []`: nothing to resolve, and no access either, since that block is the
permission manifest the user approves.

Observed in a live Cowork session on hal 0.11.3: the error reported `name: "Edifice Front"`
and an empty tool list, while the source file the skill wrote to disk still carried
`name: "edifice-front"` and the three correct ids. The published artifact and the source
file are distinct objects — diffing the downloaded source had wrongly cleared the platform.

### Fixed
- **`edifice`** — the three ids are full literals in the bundle, each carrying the
  `PLACEHOLDER_HAL_MCP_UUID` the skill substitutes. This matches the one artifact known to
  work (`docs/reference-cowork-artifact-command-center.html`). `readMeta()` is gone; the
  meta block stays in the HTML as platform input.
- **`edifice`** — `SKILL.md` step 3 said « 3 occurrences, all inside the meta block ». It is
  6 now, and hydrating only the meta block was the bug. Step 5 warns that an artifact from
  an earlier run lingers in the gallery under a humanized name and silently serves the old build.

### Changed
- **`edifice`** — error code `bad_meta` (introduced in 0.11.3) → `not_hydrated`, the only
  failure this path can still produce.

## [0.11.3] — 2026-07-28 — edifice-front: self-diagnosing error when the meta block declares no hal-mcp tools

A stale artifact left open in the Cowork gallery produced the same message as a
genuine hydration failure — « Outil MCP … absent du bloc meta ». Telling the two apart
required downloading the published artifact and diffing it against the committed source.
The message now carries the evidence.

### Fixed
- **`edifice`** — `resolveToolName()` now reports the running artifact's meta `name` and
  the `mcpTools` it actually declares (or `liste vide` / `champ mcpTools absent ou
  non-tableau`), plus the shape of a valid id. `readMeta()` catches `JSON.parse` instead
  of letting a `SyntaxError` escape.
- **`edifice`** — new error code `bad_meta`, split out of `no_cowork`: the artifact *is*
  running in Cowork, so the old banner (« ne fonctionne que dans Claude Cowork ») pointed
  at the wrong cause. Its banner now says to regenerate with `/edifice front` and delete
  the stale artifact from the gallery.

Diagnostics only — no change to how tools are resolved or called.

## [0.11.2] — 2026-07-28 — /edifice front: read the hal-mcp connector UUID via ListConnectors

`/edifice front` shipped broken in 0.11.0. Step 2 derived the connector UUID from the
session's own MCP tool names, expecting Cowork's `mcp__<uuid>__<tool>` convention — but
Cowork exposes hal-mcp under its short name, so the meta block was hydrated with
`hal-mcp` and the artifact refused to load. Found on a real Cowork run.

### Fixed
- **`edifice`** — `/edifice front` step 2 now reads `installedServerId` from
  `ListConnectors(keywords: ["hal"])`, the only id `window.cowork.callMcpTool` resolves;
  it stops with a clear message when the `hal-mcp` entry is missing, `connected: false`,
  or `enabledInChat: false`. `ToolSearch` and `ListConnectors` added to `allowed-tools`.
  Both "verify in Cowork" TODOs removed — the route was run end-to-end on 2026-07-28.

## [0.11.1] — 2026-07-28 — escape XML (&, <, >) in docx renderer contexts

An `&` in any free-text field broke the docx render: docxtpl interpolates values straight
into the document's XML with no autoescaping, so `Dupont & Fils` produced an invalid file.
Found on a real `/edifice pull → improve → report → push` run. All three renderers were
affected, so a **devis** and a **CR de visite** failed the same way — not just the edifice
report.

### Fixed
- **`edifice`**, **`crm`** — new shared `plugins/hal/scripts/xml_escape.py`, applied in
  `render_diagnostic.py`, `render_devis.py` and `render_cr_visite.py` before `doc.render()`.
  It escapes `str` leaves only and recurses through `dict`/`list`, passing every other type
  through untouched — `InlineImage` photos and `None` values keep working, which is the
  regression the tests guard against.

## [0.11.0] — 2026-07-28 — `/edifice front`: read-only Cowork live artifact for mission viewing

New command: `/edifice front` generates a self-contained live-artifact HTML
(`plugins/hal/artifacts/edifice-front.html`, ~430 KB, built from `ui/edifice-front/`)
that renders a mission's notes and photos entirely through `hal-mcp`'s Edifice tools —
no signed URLs, no external network calls, CSP-safe. The skill hydrates a per-desktop
connector UUID into the template's meta block and writes the result to a working
directory (never back into the plugin root).

### Added
- **`edifice`** — `/edifice front` command + skill route: reads the committed
  artifact template, extracts the hal-mcp connector UUID from the invoking session's
  own MCP tool names, and writes the hydrated HTML.
- `ui/edifice-front/` — React 19 + Vite app consuming `@bluegreeno/annotation-core`
  (mission list, Infos/Notes/Photos tabs, `PhotoGallery` for photo viewing). MCP calls
  are gated behind user clicks (mission select, Photos tab) rather than fired
  automatically on load, to limit the artifact load-time permission-dialog risk.
- `plugins/hal/.mcp.json` — bumped to hal-mcp `0.3.0` (adds `get_mission_context` and
  `get_mission_photo`, the two tools this artifact depends on).

### Known limitations (Phase 1, read-only)
- Rotate/crop/annotate affordances inherited from `PhotoGallery` are visually present
  but not wired to persistence — changes are local to the browser tab only. Phase 2
  wires `push_mission_context`.
- The permission-dialog behavior for MCP calls made from within a live artifact has
  not been verified in a real Cowork session — see `<!-- TODO: verify in Cowork -->`
  markers in `plugins/hal/skills/edifice/SKILL.md` and `ui/edifice-front/src/cowork-mcp.ts`.

## [0.10.5] — 2026-07-25 — fix `/edifice pull` clobbering unpushed `context.json` edits

`build_context.py` rewrote `mission/context.json` unconditionally on every
`/edifice pull`, with no check for an existing file. Any edits made via
`/edifice improve` that had not yet been pushed to the server (e.g. after a
partial `/edifice push` failure) were silently destroyed — the script still
printed its usual success summary.

### Fixed
- **`edifice`** — `build_context.py` now renames an existing `context.json` to
  `context.json.bak-<timestamp>` before writing the new one, and prints a
  warning with the backup path. A first pull (no existing `context.json`)
  behaves exactly as before.

## [0.10.4] — 2026-07-24 — document known `push_mission_context` project_id bug

`/edifice push` fails deterministically with `null value in column "project_id" of
relation "edifice_notes" violates not-null constraint` — the `hal-mcp`
`push_mission_context` tool upserts instead of updating existing rows by
`note_id`, dropping `project_id`. The fix belongs in the private `hal-mcp` repo
(replace upsert with a targeted UPDATE by `note_id`, preserving `project_id`);
this release only documents the known error in the skill so users aren't misled
into thinking their `observations` payload is malformed.

### Fixed
- **`edifice`** — added a "Known issue" note under `/edifice push` explaining the
  `project_id` not-null error is a backend bug, not a payload problem, and that
  it should be reported rather than retried with different `note_id`/`type`
  values (closes #31).

## [0.10.3] — 2026-07-23 — declare hal-mcp tools in allowed-tools for all 4 skills

Each of `crm`, `pm`, `edifice`, `linkedin` calls `hal-mcp` MCP tools from prose in the
skill body without ever declaring them in `allowed-tools`, so every MCP call
triggered a permission prompt instead of being pre-approved for the invoking turn.

### Fixed
- **`crm`** — added `whoami`, `list_projects`, `create_project`, `update_project`,
  `list_stages`, `update_project_stage`, `list_companies`, `create_company`,
  `list_contacts`, `create_contact`, `update_contact`, `log_interaction`,
  `save_document` to `allowed-tools` as `mcp__plugin_hal_hal-mcp__<tool>`.
- **`pm`** — added `whoami`, `list_projects`, `list_tasks`, `list_sprints`,
  `create_project`, `create_task`, `update_task`, `update_task_status`,
  `assign_task_to_sprint`, `create_sprint`, `update_sprint`, `log_interaction`,
  `save_document`.
- **`edifice`** — added `list_edifice_missions`, `get_mission_with_assets`,
  `push_mission_context`.
- **`linkedin`** — added `whoami`, `create_task`, `list_tasks`,
  `update_task_status`, `save_document`, `log_interaction` (the Bright Data
  tools used by `/linkedin trend` belong to a separate MCP server and are out
  of scope here).

## [0.10.2] — 2026-07-23 — pre-flight recovery now points at /mcp → plugin:hal:hal-mcp → authenticate

## [0.10.1] — 2026-07-05 — Edifice phase 3: crop_region & annotations pass-through

### Added
- **`build_context.py`** — `_count_local_workspace_data(photos)` private helper: counts photos
  carrying non-null `crop_region` or non-empty `annotations` from the MCP response.
- **`build_context.py` `main()`** — conditional summary line after the existing `✅ context.json →`
  block: prints `local-workspace → N photo(s) recadrée(s) | M photo(s) annotée(s)` only when
  counts > 0.
- **6 unit tests** (`TestCountLocalWorkspaceData`): crop-present, crop-absent,
  annotations-present, annotations-empty/absent, empty list, combined crop+annotations.
  Suite: 14 passed (8 pre-existing + 6 new).

### Documentation
- **Skill `edifice` (0.3.2)** — `/edifice pull` step 3: paragraph clarifying that `crop_region`
  and `annotations` are verbatim MCP pass-through fields managed exclusively by the
  local-workspace desktop tool. Corrected to note Cowork reads them for diagnostic console
  output only.

---

## [0.10.0] — 2026-06-25 — New skill /linkedin — editorial content pipeline

### Added
- **Skill `linkedin` (0.1.0)** — new skill covering the full LinkedIn content cycle:
  - `/linkedin idea <titre>` — capture content idea as hal task tagged `linkedin`
  - `/linkedin backlog [workspace]` — view editorial pipeline grouped by status
  - `/linkedin trend [sujet]` — research trending topics via Bright Data (`search_engine` + `web_data_linkedin_posts`)
  - `/linkedin draft <titre>` — write and save a post draft via `save_document`, marks task in_progress
  - `/linkedin log <titre>` — mark post as published (`update_task_status` done + `log_interaction`)
- **`commands/linkedin.md`** — bare `/linkedin` slash command (self-contained routing logic)
- **`marketplace.json`** — added `./plugins/hal/skills/linkedin` to skill list; version bumped to 0.10.0

### Notes
- LinkedIn ideas stored as hal tasks with tag `linkedin` — no new Supabase table
- `trend` command uses Bright Data MCP tools only (no hal-mcp pre-flight required)
- V2 backend (dedicated table, hal-mcp tools for posts) tracked as separate issue
- Closes #28 (MVP)

---

## [0.9.0] — 2026-06-17 — New skill /crm — commercial pipeline with BANT

### Added
- **Skill `crm` (0.1.0)** — new skill covering the full commercial cycle:
  - `/crm list` — pipeline kanban by stage (opportunities = projects with `kind: "opportunity"`)
  - `/crm new <nom>` — create opportunity at stage Prospect
  - `/crm qualify <nom>` — BANT extraction from conversation context, stored in project description
  - `/crm log <note ou CR>` — log structured meeting CR via `log_interaction`, with automatic BANT extraction
  - `/crm update <texte>` — update stage (`update_project_stage`), amount, name; routes to qualify for BANT updates
  - `/crm contact new/update` — manage contacts and companies
  - `/crm doc <url>` — attach document to opportunity via `save_document`
- **`commands/crm.md`** — bare `/crm` slash command (self-contained routing logic)
- **`marketplace.json`** — added `./plugins/hal/skills/crm` to skill list; version bumped to 0.9.0

### Notes
- BANT fields stored in `description` of projects until a dedicated Supabase column ships
- Supersedes issues #17 (BANT) and #18 (CR ingestion), closes #20

---

## [0.8.0] — 2026-06-17 — Rename /hal → /pm; PM scope extracted

### Changed
- **Skill `hal` → `pm` (0.7.2 → 0.8.0)** — renamed and refocused on internal
  project management only:
  - Removed CRM-commercial scope (pipeline kanban, stage updates, company/contact
    creation, `log_interaction` for prospects, devis generation) — these will live
    in the upcoming `/crm` skill (issue #20).
  - Kept: `tasks`, `list` (projects), `update` (tasks + sprints), workspace
    resolution, pre-flight `whoami`, fuzzy match engine.
  - Added new PM-specific subcommands: `new <projet>`, `task <titre>`,
    `log <note>`, `doc <url>`, `sprint`.
- **`commands/hal.md` → `commands/pm.md`** — `/hal` replaced by `/pm`.
- **`marketplace.json` + `plugin.json`** — updated skill path and version to 0.8.0.
- **`CLAUDE.md`** — all references updated from `hal` skill to `pm` skill.

### Migration
Users running `/hal` will need to switch to `/pm`. The CRM scope
(`/hal list`, `/hal update` for prospects/stages, `/hal devis`) is temporarily
unavailable until `/crm` ships (issue #20).

---

## [0.7.1] — 2026-06-13 — PM tags: --tag filter + tags in output

### Added
- **Skill `hal` 0.7.0 → 0.7.1** — tags support:
  - `/hal tasks --tag <value>` — filter tasks by tag; passes `tags=[value]` to
    `list_tasks` (hal-mcp v39). Enters explicit-query mode (skips sprint scope).
    Combinable with `--mine`. Scope header: `**Tag : <value>** · workspace <slug>`.
  - Task line format extended: `#tag1 #tag2` appended when `tags` is non-empty.
  - `/hal list` — project line format extended: `#tag1 #tag2` appended when
    project `tags` is non-empty.
- **`commands/hal.md`** — `--tag <tag>` added to argument-hint and tasks routing.
- **`README.md`** — unified tag vocabulary documented (commercial, client,
  marketing, product, operations, hr, finance, legal, other) with link to
  `hal/docs/tag-vocabulary.md`; hal-mcp version updated to v39.

---

## [0.7.0] — 2026-06-11 — Hal Lot 2 — tâches et sprints + workspace résolution server-side

### Added
- **Skill `hal` 0.4.1 → 0.7.0** — Lot 2 tâches :
  - `/hal tasks [workspace]` — kanban texte groupé par statut
    (todo → in_progress → blocked → ✓ done). **Scope par défaut : le sprint
    actuel**, résolu via `list_sprints(workspace_slug, status="actuel")`. Aucun
    sprint actuel → message explicite + fallback sur les tâches ouvertes du
    workspace (jamais de board vide silencieux). Filtres : `--mine`,
    `--project <ref>`, `--status`, `--all` (échappe au scope sprint). Pur MCP,
    zéro script.
  - NL task intents dans `/hal update` — trois writers à responsabilité unique :
    créer (`create_task`), éditer les attributs (`update_task` — `title`,
    `description`, `due_date`, `project_id`, `assignee_email`, `priority`,
    `external_ref`), changer le statut (`update_task_status`), assigner à un
    sprint (`assign_task_to_sprint`). `update_task` ne touche **ni** au statut
    **ni** au sprint.
  - `create_sprint` — disponible sur tout workspace avec `sprints_enabled = true`.
- **`commands/hal.md`** — `tasks` subcommand (scope sprint par défaut) + intent
  `update_task` ajoutés au routing.

### Changed (interface — MINOR bump)
- **Workspace resolution server-side via `whoami`** — le pré-flight appelle
  désormais l'outil MCP `whoami` (au lieu de `list_stages(blue-green)`). Le
  workspace par défaut vient de `whoami.default_workspace_slug` (résolu côté
  Supabase depuis `workspace_members.is_default`). Plus aucun hardcode
  `blue-green` côté skill, plus aucune config client (env var supprimée).
  Si l'utilisateur appartient à plusieurs workspaces sans flag par défaut, le
  skill demande lequel utiliser ; s'il n'en a aucun, il invite à contacter
  l'admin — jamais de fallback vers un slug hardcodé.
- `/hal list` — workspace résolu via `whoami.default_workspace_slug` (même
  pattern que `/hal tasks`).
- `/hal tasks --mine` — `assignee_email` vient de `whoami.user_email`,
  l'utilisateur n'est plus interrogé.
- `README.md` — section "Set your default workspace" supprimée ; nouvelle
  procédure d'onboarding : l'admin ajoute l'utilisateur dans
  `workspace_members` et flag son défaut (`is_default = true`). Zero
  client-side config.

### Removed
- **Workspace env var (config client)** — supprimée intégralement (fix-forward,
  pas de shim de compat). Migration : l'admin renseigne `is_default` dans
  Supabase `workspace_members` ; aucune action côté utilisateur.
- Mention "Tasks and sprints — not yet available" dans la section "Out of scope" —
  remplacée par les limitations réelles : pas d'édition des champs
  company/contact/projet (hors `stage`), pas de jointure sur `project_id`. Les
  champs de tâche, eux, sont éditables via `update_task`.

### Prerequisites
- **hal-mcp v29+ (PR #41 — déployé prod 2026-06-11)** — outil `whoami` exposé
  par le serveur MCP. Le skill ne fonctionne pas sans cette version.
- **Migration Supabase `workspace_members.is_default`** (hal repo,
  `20260611000000_workspace_members_is_default.sql`) — colonne lue par
  `whoami` pour servir le workspace par défaut.
- hal-mcp v28 (PRs #38 #39, 2026-06-08) — `update_task_status` accepte
  `workspace_slug` ✅, `sprints_enabled = true` sur `blue-green` ✅.

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
