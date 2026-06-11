# Feature: hal Lot 2 — `/hal tasks` + NL task intents

**IMPORTANT — Run this plan from the `bluegreen-marketplace` repo root.**
All paths below are relative to `~/Projects/bluegreen-marketplace/`.
Open Claude Code in that directory before executing.

Pay close attention to the versioning policy in `CLAUDE.md`.

## Feature Description

Extend the `hal` skill (`plugins/hal/skills/hal/SKILL.md`) and the `/hal` command
(`plugins/hal/commands/hal.md`) with task management:

1. **`/hal tasks [workspace]`** — list tasks grouped by status (kanban texte)
2. **NL task intents** — extend `/hal update` intent table with create/update/sprint verbs
3. **Workspace default via env var** — `HAL_DEFAULT_WORKSPACE` — configurable per
   client, no hardcoded slug, transparent after first setup

No backend changes… except two prerequisites (see below).

## Prerequisites — hal-mcp changes needed first

Two changes must land in `hal/supabase/functions/hal-mcp/index.ts` **before**
executing this skill plan. They are small, targeted, and can be done in one PR.

### Prerequisite 1 — `update_task_status` must accept `workspace_slug`

Current schema:
```typescript
inputSchema: z.object({
  task_id: z.string(),
  status:  z.enum(TASK_STATUSES),
})
```

Required schema:
```typescript
inputSchema: z.object({
  workspace_slug: z.string(),   // add this
  task_id:        z.string(),
  status:         z.enum(TASK_STATUSES),
})
```

The handler can use `workspace_slug` to validate access before updating
(fetch the task and confirm `task.workspace_slug === workspace_slug`), or just
ignore it after validation — the RLS already enforces access via JWT. The slug
makes the call self-documenting and consistent with all other tools.

### Prerequisite 2 — `sprints_enabled = true` for `blue-green`

Migration WP5 (`20260622000000_halcrm_tasks_wp5.sql`) only set:
```sql
UPDATE halcrm_workspaces SET sprints_enabled = true
WHERE workspace_slug = 'ic-ingenieurs-conseils';
```

Add a new migration in `hal/supabase/migrations/` to enable sprints for blue-green:
```sql
UPDATE halcrm_workspaces SET sprints_enabled = true
WHERE workspace_slug = 'blue-green';
```

---

## Tools available (hal-mcp v28 — confirmed deployed)

### `create_task`
```
Input:
  workspace_slug: string      -- required
  title:          string      -- required
  project_id?:    UUID        -- link to a project
  assignee_email? string      -- must be a workspace member
  due_date?:      YYYY-MM-DD
  sprint_id?:     UUID
  description?:   string
Returns: created task row (status defaults to "todo")
```

### `list_tasks` — via RPC `get_tasks_with_assignee`
```
Input:
  workspace_slug:   string    -- required
  project_id?:      UUID      -- filter by project
  assignee_email?:  string    -- resolved to user_id via RPC then filtered
  status?:          string    -- todo | in_progress | done | blocked
  sprint_id?:       UUID      -- filter by sprint

Returns: array (max 100, ORDER BY created_at DESC)
  {
    id:               TEXT,
    workspace_slug:   TEXT,
    project_id:       TEXT | null,   -- UUID brut, no join on project_ref
    title:            TEXT,
    description:      TEXT | null,
    assignee_user_id: UUID | null,
    assignee_email:   TEXT | null,   -- surfaced from auth.users via LEFT JOIN
    document:         TEXT | null,
    due_date:         DATE | null,
    priority:         TEXT | null,
    status:           TEXT,          -- todo | in_progress | done | blocked
    sprint_id:        TEXT | null,
    created_at:       TIMESTAMPTZ,
    updated_at:       TIMESTAMPTZ,
  }
```

### `update_task_status` (after prerequisite 1)
```
Input:
  workspace_slug: string    -- required (after prerequisite)
  task_id:        UUID      -- required
  status:         enum      -- todo | in_progress | done | blocked
Returns: updated task row
```

### `create_sprint`
```
Input:
  workspace_slug: string   -- required
  name:           string   -- required
  sprint_number:  int      -- required
  status?:        enum     -- passes | dernier | actuel | suivant | a_venir (default: a_venir)
  starts_at?:     ISO date
  ends_at?:       ISO date
Note: server returns error if sprints_enabled = false on the workspace.
      After prerequisite 2, both blue-green and ic-ingenieurs-conseils are enabled.
```

### `assign_task_to_sprint`
```
Input:
  workspace_slug: string  -- required
  task_id:        UUID    -- required
  sprint_id:      UUID    -- required
Note: same sprints_enabled guard as create_sprint.
```

---

## User Stories

- Renaud (BG primary) : `/hal tasks` → kanban BG transparent, sans taper le slug
- Renaud (IC subcontractor) : `/hal tasks ic` → kanban IC explicite
- Laurent (IC) : `/hal tasks` → kanban IC par défaut, sans taper le slug
- Future client X : `/hal tasks` → kanban workspace X transparent via `HAL_DEFAULT_WORKSPACE`
- Renaud : "ajouter tâche relancer Valorem" → `create_task` sans frottement
- Renaud : "tâche relancer Valorem → done" → fuzzy match → `update_task_status`
- Laurent : "nouveau sprint S3 cette semaine" → `create_sprint` (sprints_enabled)
- Laurent : "assigne la tâche X au sprint actuel" → `assign_task_to_sprint`

---

## Feature Metadata

**Feature Type**: New capability (new command + NL intent extension)
**Estimated Complexity**: Low — même pure-instruction pattern que `/hal list`
**Skill version**: `hal` 0.4.1 → **0.5.0** (MINOR — nouveau command + NL interface)
**Plugin version**: 0.6.0 → **0.7.0**
**Primary files**:
- `plugins/hal/skills/hal/SKILL.md` — add `/hal tasks` section + extend intent table + workspace resolution
- `plugins/hal/commands/hal.md` — add `tasks` subcommand routing
- `plugins/hal/.claude-plugin/plugin.json` — bump to 0.7.0
- `.claude-plugin/marketplace.json` — bump to 0.7.0
- `plugins/hal/CHANGELOG.md` — entry `[0.7.0]`

---

## CONTEXT REFERENCES

### Relevant Codebase Files — READ BEFORE IMPLEMENTING

- `plugins/hal/skills/hal/SKILL.md` (entire file)
  → Structure existante : Pre-flight, `/hal list`, `/hal update`, intent table,
    entity resolution, guardrails, `/hal devis`, Out of scope.
  → Insérer `/hal tasks` **après `/hal list`** (read-only commands groupés en tête).
  → Étendre la section "Intent → tool mapping" avec les task intents.
  → Retirer la mention "Tasks and sprints — not yet available" dans "Out of scope".
  → Mettre à jour la résolution workspace (env var `HAL_DEFAULT_WORKSPACE`).

- `plugins/hal/commands/hal.md`
  → Ajouter `tasks` dans le routing table (même pattern que `list` et `update`).

- `plugins/hal/skills/edifice/SKILL.md` → référence `/edifice list` (même pattern affichage)
- `plugins/hal/CHANGELOG.md` (lignes 1–40) → format d'entrée
- `plugins/hal/.claude-plugin/plugin.json` → version actuelle `"0.6.0"`
- `.claude-plugin/marketplace.json` → doit rester en sync avec plugin.json

---

## IMPLEMENTATION PLAN

### Phase 0 — Workspace resolution pattern (applies to ALL commands)

Remplacer le pattern actuel "hard-coded `blue-green`" par une résolution via env var
dans **toutes les sections** du SKILL.md qui résolvent le workspace (list, tasks, update).

```
Workspace resolution (applies to every /hal command):

1. Explicit arg (`/hal tasks ic`, `/hal list blue-green`) → use that slug directly.
   Shorthand: `ic` → `ic-ingenieurs-conseils`.
2. No arg → read env var HAL_DEFAULT_WORKSPACE:
   - Available (non-empty) → use it as workspace_slug.
   - Not set → respond:
     > ❌ Workspace par défaut non configuré.
     > Ajoute `export HAL_DEFAULT_WORKSPACE=<ton-slug>` dans ton `~/.zshrc` (ou `.env`).
     > Relance la commande après.
```

The skill reads `HAL_DEFAULT_WORKSPACE` via an inline Bash step (already in
`allowed-tools: "Bash(python3 *)"`):

```bash
DEFAULT_WS=$(python3 -c "import os,sys; ws=os.environ.get('HAL_DEFAULT_WORKSPACE',''); print(ws) if ws else sys.exit(1)" 2>/dev/null)
if [ $? -ne 0 ]; then
  echo "HAL_DEFAULT_WORKSPACE not set — see setup instructions above"
  exit 1
fi
echo "Workspace: $DEFAULT_WS"
```

**Note**: `/hal list` currently hardcodes `blue-green` as default. This phase also
updates that section to use the same env var pattern.

**Renaud's setup** (already in his shell):
```bash
export HAL_DEFAULT_WORKSPACE=blue-green
```
Laurent (IC), other clients: set their own slug once → fully transparent.

---

### Phase 1 — Lire les fichiers cibles

Lire `plugins/hal/skills/hal/SKILL.md` et `plugins/hal/commands/hal.md` pour
comprendre la structure exacte avant toute modification.

Points à noter dans SKILL.md :
- Position des `## /hal *` sections (ordre exact)
- Position d'insertion de `/hal tasks` : après `## /hal list`, avant `## /hal update`
- Tableau "Intent → tool mapping" : où insérer les task intents
- Mention exacte à supprimer dans "Out of scope" : `"Tasks and sprints — server CRUD..."`
- Occurrences de `workspace_slug: "blue-green"` (hard-coded) à remplacer par
  la résolution env var dans les sections list et tasks

---

### Phase 2 — Mettre à jour la résolution workspace dans `/hal list`

Dans la section `## /hal list`, remplacer le step "Resolve workspace" pour utiliser
le pattern Phase 0 (env var) au lieu de `workspace_slug: "blue-green"` hard-coded.

---

### Phase 3 — Ajouter `/hal tasks` dans SKILL.md

Insérer après `## /hal list` :

```markdown
## /hal tasks `[workspace]` `[--mine]` `[--project <ref>]` `[--status <status>]`

Show tasks as a text kanban grouped by status.
Default workspace: resolved from `HAL_DEFAULT_WORKSPACE` env var (see workspace
resolution pattern at top of this skill).

### Steps

**1. Resolve workspace** — use the standard workspace resolution pattern.

**2. Resolve filters**

- `--mine` → add `assignee_email: "<user's own email, from conversation context>"`.
  If email is unknown, ask the user rather than guessing.
- `--project <ref>` → call `list_projects` to resolve `project_id` by name/ref,
  then add `project_id` filter to `list_tasks`.
- `--status <value>` → add `status` filter (todo|in_progress|done|blocked).
- No filters → retrieve all tasks in the workspace (no filter).

**3. Call MCP `list_tasks`**

Call with `workspace_slug` (+ resolved filters).

**4. Group and display**

Group by `status`. Fixed order: `todo` → `in_progress` → `blocked` → `done`.
`done` is terminal — prefix header with `✓ `.

Display format:

```
### todo (3)
- Relancer Valorem pour signature · renaud@bluegreen.ai · 2026-06-15
- Préparer propale VESTA · — · —
- Appeler Laurent IC · — · —

### in_progress (1)
- Rédiger rapport Varenne · — · 2026-06-20 [S]

### blocked (1)
- Accès chantier Aulnay · — · —

### ✓ done (5)
- Migration Supabase · renaud@bluegreen.ai · 2026-06-05
```

Line format per task:
`{title} · {assignee_email short or "—"} · {due_date or "—"} {[S] if sprint_id set}`

- `assignee_email short`: local part before `@` (e.g. `renaud` from `renaud@bluegreen.ai`).
  Show `—` if null.
- `[S]` marker if `sprint_id` is non-null (sprint name unknown without extra call).
- `priority` field exists in the response — show only if non-null and not "normal":
  prepend `⚡` for high priority.

**Note on `project_id`**: `list_tasks` returns a raw UUID. Without a `--project` filter
that pre-resolved the ref, show nothing in that column (use assignee instead).
A future improvement could join on project data — out of scope for this release.

**5. Edge cases**

- No tasks → `Aucune tâche dans le workspace <slug>.`
- Empty status group → skip that group entirely
- `HAL_DEFAULT_WORKSPACE` not set + no arg → surface setup instructions (see phase 0)
- Unknown workspace slug → surface `list_tasks` error verbatim
```

---

### Phase 4 — Étendre le tableau "Intent → tool mapping"

Dans `## Intent → tool mapping`, ajouter un bloc tâches + sprints :

```markdown
| "mes tâches", "todo list", "qu'est-ce que j'ai à faire" | `list_tasks` (workspace default) |
| "ajouter tâche X", "nouvelle tâche Y", "todo : Z", "créer une tâche" | `create_task` |
| "tâche X faite", "X → done", "X terminé", "c'est fait" | `list_tasks` → fuzzy match → `update_task_status` (done) |
| "X → in progress", "je commence X", "en cours : X" | `list_tasks` → fuzzy match → `update_task_status` (in_progress) |
| "X bloqué", "X → blocked" | `list_tasks` → fuzzy match → `update_task_status` (blocked) |
| "X → todo", "remettre X en attente" | `list_tasks` → fuzzy match → `update_task_status` (todo) |
| "nouveau sprint S<N>", "créer sprint" | `create_sprint` |
| "assigne tâche X au sprint Y", "tâche X dans sprint Y" | `list_tasks` → match task → `assign_task_to_sprint` |
```

---

### Phase 5 — Ajouter section `## Task resolution`

Ajouter après `## Entity resolution` :

```markdown
## Task resolution (fuzzy match)

Same thresholds as entity resolution (score > 80 / 50–80 / < 50).

- Match on `title`. Call `list_tasks` with **no `status` filter** — "X → done"
  must match tasks that are currently `todo` or `in_progress`.
- Ambiguity: multiple tasks at the same score → list candidates, ask to pick.
- `update_task_status` takes `workspace_slug`, `task_id`, and `status`.
  Always pass `workspace_slug` — resolved from arg or `HAL_DEFAULT_WORKSPACE`.
- **Never auto-create a task from an ambiguous match.** Score < 50 → propose creation.
- "c'est fait" / "done" said after completing a described action → propose the
  corresponding task write, don't auto-write.
- Sprint resolution: "sprint actuel" → call `list_tasks` with `sprint_id` filter
  after resolving the sprint (no `list_sprints` tool — ask the user for the UUID
  or sprint number if ambiguous).
```

---

### Phase 6 — Mettre à jour "Out of scope"

Supprimer :
```
- **Tasks and sprints** — server CRUD (`create_task`, `list_tasks`,
  `update_task`) not yet available. Coming in a future sprint (lot 2).
```

Remplacer par :
```
- **Task field updates** — only `status` can be updated via `update_task_status`.
  Title, due_date, assignee, description, priority cannot be edited after creation
  (server limitation — no `update_task` tool).
- **Sprint listing** — no `list_sprints` MCP tool. Sprint UUIDs must be provided
  by the user or resolved from a previous `create_sprint` response.
- **`project_id` join** — `list_tasks` returns a raw `project_id` UUID, not the
  project ref. A separate `list_projects` call resolves it — done automatically
  when `--project <ref>` filter is used, otherwise the column is omitted.
```

---

### Phase 7 — Mettre à jour commands/hal.md

Lire le fichier, puis ajouter `tasks` dans le routing. Format identique aux autres
subcommands (`list`, `update`, `devis`).

---

### Phase 8 — Version bumps

| File | Champ | Old | New | Raison |
|------|-------|-----|-----|--------|
| `plugins/hal/skills/hal/SKILL.md` | `version:` | `0.4.1` | `0.5.0` | MINOR — nouveau command + NL interface |
| `plugins/hal/.claude-plugin/plugin.json` | `"version"` | `"0.6.0"` | `"0.7.0"` | nouvelle release |
| `.claude-plugin/marketplace.json` | `plugins[0].version` | `"0.6.0"` | `"0.7.0"` | doit mirror plugin.json |

---

### Phase 9 — CHANGELOG entry

Prepend dans `plugins/hal/CHANGELOG.md` :

```markdown
## [0.7.0] — 2026-06-09 — Hal Lot 2 — tâches et sprints

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

### Prerequisites (hal-mcp changes, must be deployed before this skill release)
- `update_task_status` accepts `workspace_slug` (PR à faire dans hal repo)
- `sprints_enabled = true` pour workspace `blue-green` (migration à faire dans hal repo)
```

---

## STEP-BY-STEP TASKS

### Task 0 — Vérifier les prérequis hal-mcp

Avant d'implémenter le skill, confirmer que les 2 prérequis sont déployés :

```bash
# Check update_task_status schema dans hal-mcp
grep -A 10 '"update_task_status"' ~/Projects/hal/supabase/functions/hal-mcp/index.ts | grep workspace_slug
# Expected: workspace_slug présent

# Check sprints_enabled pour blue-green
# (via Supabase dashboard ou MCP supabase execute_sql)
# SELECT workspace_slug, sprints_enabled FROM halcrm_workspaces;
```

Si les prérequis ne sont pas là → ouvrir Claude Code dans `~/Projects/hal` et les
implémenter d'abord.

---

### Task 1 — READ les fichiers cibles

- `plugins/hal/skills/hal/SKILL.md` (complet)
- `plugins/hal/commands/hal.md` (complet)

Confirmer : version SKILL.md `0.4.1`, plugin.json `0.6.0`, ordre des sections.

---

### Task 2 — EDIT SKILL.md

1. Bump `version: 0.4.1` → `version: 0.5.0`
2. Ajouter/mettre à jour le bloc "Workspace resolution" en tête du skill
   (avant Pre-flight, ou intégré dans chaque section — choisir la forme la plus lisible)
3. Mettre à jour `/hal list` : remplacer `workspace_slug: "blue-green"` hardcoded
   par la résolution env var
4. Insérer `## /hal tasks` section après `## /hal list`
5. Étendre le tableau "Intent → tool mapping" avec les task intents
6. Ajouter section `## Task resolution`
7. Remplacer la ligne "Tasks and sprints" dans "Out of scope"

**Validate** :
```bash
grep "^version:" plugins/hal/skills/hal/SKILL.md
grep -n "^## /hal" plugins/hal/skills/hal/SKILL.md
```
Expected order : `list`, `tasks`, `update`, `devis`

---

### Task 3 — EDIT commands/hal.md

Lire le fichier, ajouter `tasks` dans le routing.

**Validate** :
```bash
grep -n "tasks" plugins/hal/commands/hal.md
```

---

### Task 4 — EDIT plugin.json

`"version": "0.6.0"` → `"version": "0.7.0"`

---

### Task 5 — EDIT marketplace.json

`plugins[0].version`: `"0.6.0"` → `"0.7.0"`

**Validate sync** :
```bash
python3 -c "
import json, pathlib
p = json.loads(pathlib.Path('plugins/hal/.claude-plugin/plugin.json').read_text())
m = json.loads(pathlib.Path('.claude-plugin/marketplace.json').read_text())
assert p['version'] == m['plugins'][0]['version'], f'MISMATCH: {p[\"version\"]} vs {m[\"plugins\"][0][\"version\"]}'
print(f'Sync OK: {p[\"version\"]}')
"
```

---

### Task 6 — PREPEND CHANGELOG entry

Prepend `[0.7.0]` dans `plugins/hal/CHANGELOG.md`.

---

### Task 7 — Final consistency check

```bash
echo "=== SKILL.md ===" && grep "^version:" plugins/hal/skills/hal/SKILL.md
echo "=== plugin.json ===" && python3 -c "import json; print(json.load(open('plugins/hal/.claude-plugin/plugin.json'))['version'])"
echo "=== marketplace.json ===" && python3 -c "import json; print(json.load(open('.claude-plugin/marketplace.json'))['plugins'][0]['version'])"
echo "=== Command sections ===" && grep -n "^## /hal" plugins/hal/skills/hal/SKILL.md
echo "=== tasks in commands ===" && grep -n "tasks" plugins/hal/commands/hal.md
echo "=== HAL_DEFAULT_WORKSPACE references ===" && grep -n "HAL_DEFAULT_WORKSPACE" plugins/hal/skills/hal/SKILL.md
```

---

## ACCEPTANCE CRITERIA

- [ ] Prérequis hal-mcp vérifiés : `update_task_status` a `workspace_slug`, `blue-green` a `sprints_enabled = true`
- [ ] Workspace resolution via `HAL_DEFAULT_WORKSPACE` dans `/hal list` ET `/hal tasks`
- [ ] `/hal tasks [workspace]` ajouté après `/hal list`, avant `/hal update`
- [ ] Affichage kanban : todo → in_progress → blocked → ✓ done
- [ ] Filtres documentés : `--mine`, `--project <ref>`, `--status`
- [ ] `priority` champ utilisé (`⚡` pour high, skip si normal/null)
- [ ] `[S]` marker si `sprint_id` non-null
- [ ] NL task intents dans "Intent → tool mapping" (create, update status, sprint)
- [ ] `## Task resolution` avec seuils fuzzy + règle workspace_slug dans update_task_status
- [ ] "Tasks and sprints — not yet available" supprimé de "Out of scope"
- [ ] "Out of scope" mis à jour : limitations réelles (no field update, no list_sprints, project_id)
- [ ] `tasks` subcommand dans commands/hal.md
- [ ] Skill `hal` : `0.4.1` → `0.5.0`
- [ ] plugin.json : `0.6.0` → `0.7.0`
- [ ] marketplace.json : `0.6.0` → `0.7.0` (sync)
- [ ] CHANGELOG `[0.7.0]` prependé
- [ ] STATUS.md mis à jour : Lot 2 → Done

---

## NOTES

### Pourquoi HAL_DEFAULT_WORKSPACE et pas une config file

Les skills s'exécutent dans des contextes variés (Claude Desktop, Cowork, IDE). Un
env var est la seule primitive universelle : lisible via `Bash(python3 *)` déjà dans
`allowed-tools`, persisté dans `~/.zshrc` pour Claude Desktop, injectable en
Cowork. Une config file nécessiterait de connaître le path — même complexité que
`PLUGIN_DIR` dans edifice, sans gain.

### Pas de `list_sprints` dans hal-mcp

Le tool n'existe pas. Pour assigner une tâche à un sprint, l'utilisateur doit
fournir le sprint_id (UUID) ou le sprint_number. Le skill peut proposer de créer
un sprint si aucun n'existe, ou demander le numéro.

### `project_id` = UUID brut dans `list_tasks`

Le RPC `get_tasks_with_assignee` ne joint pas sur `halcrm_projects`. Pour afficher
le ref projet (`DEV-168`), il faudrait un call `list_projects` séparé. Ce n'est
fait qu'à la demande (filter `--project <ref>` qui résout d'abord le project_id).
Sans filtre, la colonne est substituée par `assignee_email`.

### Confidence score

**8/10** — même pattern pur-instruction que `/hal list`. Les 2 prérequis hal-mcp
sont simples à implémenter. Le seul risque est la résolution workspace via env var
sur Cowork (env vars éphémères) — à tester post-release.
