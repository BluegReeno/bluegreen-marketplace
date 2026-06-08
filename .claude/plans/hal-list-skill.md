# Feature: /hal list [workspace] — skill bluegreen-marketplace

**IMPORTANT — Run this plan from the `bluegreen-marketplace` repo root.**
All paths below are relative to `~/Projects/bluegreen-marketplace/`.
Open Claude Code in that directory before executing.

Pay close attention to the versioning policy in `CLAUDE.md`
and to the `hal` skill's `allowed-tools` frontmatter constraint.

## Feature Description

Add a `/hal list [workspace]` command to the `hal` skill
(`plugins/hal/skills/hal/SKILL.md`). The command calls the existing
`list_projects` MCP tool and formats the result as a **text kanban** —
projects grouped by stage so the user sees the full pipeline at a glance.

No backend changes. `list_projects` already exists in
`hal/supabase/functions/hal-mcp/index.ts` (lines 345–382) and already
returns the right fields via the `get_project_list` RPC.

## User Story

As Renaud (Blue Green) or Laurent (IC Ingénieurs Conseils)  
I want to type `/hal list` and see all active CRM projects grouped by stage  
So that I can instantly understand the pipeline without opening Supabase

## Problem Statement

There is no read-only pipeline overview command. The only way to see projects
is to ask `/hal update "où en est [client]"` for a specific project —
there is no kanban-style all-projects view. For a weekly review or a
client call, there is no quick way to scan the full pipeline.

## Solution Statement

A pure-instruction command in `hal/SKILL.md`: call `list_projects` (no stage
filter, workspace from arg or default), group results by stage, format as a
compact text kanban with one line per project. No scripts, no Bash — pure
NL → MCP, identical architecture to `/hal update`.

## Feature Metadata

**Feature Type**: New Capability (new command in existing skill)
**Estimated Complexity**: Low
**Primary Systems Affected**: `plugins/hal/skills/hal/SKILL.md`
**Dependencies**: None — `list_projects` MCP tool already deployed (hal-mcp v27)

---

## CONTEXT REFERENCES

### Relevant Codebase Files — READ BEFORE IMPLEMENTING

- `plugins/hal/skills/hal/SKILL.md` (entire file)
  → This is the only file receiving a content change. Read it to understand
    the existing section format before adding `/hal list`.

- `plugins/hal/skills/edifice/SKILL.md`
  → Reference for the `/edifice list` command (added in plugin 0.4.0) —
    same pattern: MCP call → formatted output, no Bash.

- `plugins/hal/CHANGELOG.md` (lines 1–40)
  → Version format and entry template to follow.

- `plugins/hal/.claude-plugin/plugin.json`
  → Current version: `"0.4.0"`. Target for this release: `"0.5.0"`.

- `.claude-plugin/marketplace.json`
  → Must stay in sync with plugin.json version at all times.

- `CLAUDE.md`
  → Full versioning policy, bump rules, release process.

- `hal/supabase/functions/hal-mcp/index.ts` (lines 345–382)
  → `list_projects` tool: read to understand exact input schema and response.

### New Files to Create

None. This feature adds one section to an existing SKILL.md only.

### MCP Tool — `list_projects` (already deployed, no change needed)

```
Tool: list_projects
Input:
  workspace_slug: string          -- required
  kind?:          string          -- optional filter: "opportunity" | "client_project" | "internal"
  stage?:         string          -- optional filter: validated against workspace kind_stages

Response shape: JSON array from get_project_list RPC
[
  {
    "id":                   "uuid",
    "name":                 "Extension hangar VESTA",
    "stage":                "devis_envoye",
    "kind":                 "opportunity",
    "amount_ht":            12000,           // may be null
    "currency":             "EUR",
    "location":             "Laval (53)",    // may be null
    "description":          "...",           // may be long — do NOT display inline
    "due_date":             "2026-07-15",    // may be null
    "project_ref":          "DEV-168",       // may be null
    "edifice_building_id":  "uuid",          // may be null
    "edifice_mission_id":   "uuid",          // may be null
    "closed_at":            null,
    "created_at":           "2026-06-07T...",
    "updated_at":           "2026-06-07T...",
    "company":  { "name": "VESTA SA", "bg_id": "..." },   // may be null
    "contact":  { "name": "Jean Dupont", "email": "..." } // may be null
  },
  ...
]
```

**Stage values (Blue Green workspace):**

Active: `prospect`, `devis_a_rediger`, `devis_envoye`
Terminal: `solde`, `perdu`

Use `list_stages` MCP tool if unsure of valid values for other workspaces —
stages are per-kind in `halcrm_workspaces.kind_stages`.

---

## IMPLEMENTATION PLAN

### Phase 1: Understand the current SKILL.md structure

Read `plugins/hal/skills/hal/SKILL.md` end-to-end.
Identify:
- Where command sections begin (`## /hal update`, `## /hal devis`, etc.)
- The frontmatter format (name, description, version, allowed-tools)
- The "Out of scope" section at the bottom
- Insert position: add `/hal list` as the **first** command section,
  before `/hal update` — reading the pipeline is the logical first step

### Phase 2: Add `/hal list [workspace]` section to SKILL.md

Insert the new command section at the **top of the command sections**,
before `## /hal update`.

The section must:

1. Call `list_projects` via MCP with no `stage` filter (full pipeline view)
2. Group results by stage (active stages first, terminal stages last)
3. One line per project: `ref · company · amount · location`
4. Handle nulls gracefully (show `—` for missing fields)
5. Skip `description` — too verbose for a kanban overview
6. Support optional `stage=<value>` and `kind=<value>` filters
7. Default workspace: `blue-green`. Accept optional workspace arg.

**Output format (exact text — adapt if context requires):**

```markdown
## /hal list `[workspace]`

Show the CRM pipeline as a text kanban — projects grouped by stage.
Default workspace: `blue-green`.

### Steps

**1. Resolve workspace**

- If the user typed `/hal list ic` or `/hal list ic-ingenieurs-conseils` →
  use `workspace_slug: "ic-ingenieurs-conseils"`.
- Any other explicit arg → use as `workspace_slug` directly.
- No arg → `workspace_slug: "blue-green"`.

**2. Call MCP `list_projects`**

Call with:
- `workspace_slug` (resolved above)
- No `stage` filter — retrieve the full pipeline
- Optional: if the user passed `stage=<value>` or `kind=<value>`, add them

To know valid stages for a workspace call `list_stages` first if unsure.

**3. Group and display**

Group results by `stage`. Order: active stages first (in pipeline order),
then terminal stages. Within each stage, order by `created_at DESC`.

Display format:

```
### prospect (2)
- DEV-168 · VESTA SA · 12 000 € · Laval (53)
- — · Martin SARL · — · —

### devis_a_rediger (1)
- DEV-045 · IC Ingénieurs Conseils · 8 500 € · Paris (75)

### devis_envoye (3)
- DEV-121 · Valorem · 45 000 € · Bordeaux (33)
- DEV-099 · EDF · — · —
- DEV-088 · Greenta · 3 200 € · Lyon (69)

### ✓ solde (5)
- DEV-055 · Lacourt · 18 000 € — soldé 2026-05-12
```

Line format per project:
`{project_ref or "—"} · {company.name or "—"} · {amount_ht formatted or "—"} · {location or "—"}`

For terminal stages: append `— soldé {closed_at[:10]}` or `— perdu {closed_at[:10]}`
when `closed_at` is present.

**4. Handle edge cases**

- No projects in workspace → `Aucun projet dans le workspace <slug>.`
- Stage is empty → skip that stage in the output (don't show empty sections)
- `description` field received → ignore it (too verbose for kanban)
- `kind` filter passed → show only that kind; add `(kind: <value>)` to header
- `stage` filter passed → show only that stage; useful for "show me all prospects"
```

### Phase 3: Version bumps

Apply **all three** version bumps in the same edit pass:

| File | Old | New | Reason |
|------|-----|-----|--------|
| `plugins/hal/skills/hal/SKILL.md` frontmatter `version:` | `0.3.0` | `0.4.0` | MINOR — new command |
| `plugins/hal/.claude-plugin/plugin.json` `"version"` | `0.4.0` | `0.5.0` | new plugin release |
| `.claude-plugin/marketplace.json` `"version"` (inside plugins array) | `0.4.0` | `0.5.0` | must mirror plugin.json |

**plugin.json and marketplace.json MUST show the same version number. Always.**

### Phase 4: CHANGELOG entry

Prepend a new entry to `plugins/hal/CHANGELOG.md`:

```markdown
## [0.5.0] — 2026-06-08 — Skill `/hal list`

### Added
- **Skill `hal` 0.3.0 → 0.4.0** — `/hal list [workspace]` command: displays the CRM
  pipeline as a text kanban grouped by stage. Defaults to workspace `blue-green`;
  accepts an optional workspace slug arg (`ic`, `blue-green`, or any slug).
  Supports optional `stage=<value>` and `kind=<value>` filters.
  No scripts — pure MCP tool call via `list_projects`, zero cold-start cost.
```

---

## STEP-BY-STEP TASKS

### Task 1 — READ the current SKILL.md

**READ**: `plugins/hal/skills/hal/SKILL.md`

- Understand the exact structure (frontmatter, command sections, Out of scope)
- Confirm current version in frontmatter is `0.3.0`
- Identify insertion point for `/hal list` (before `## /hal update`)

**VALIDATE**: File loads cleanly, version confirmed.

---

### Task 2 — EDIT SKILL.md: add `/hal list` section + bump version

**UPDATE**: `plugins/hal/skills/hal/SKILL.md`

- **PATCH frontmatter**: `version: 0.3.0` → `version: 0.4.0`
- **INSERT** the `/hal list` section (see Phase 2 above) immediately before
  `## /hal update` — logical order: list first, then update

**GOTCHA**: `/hal list` needs **no new allowed-tools** — it only calls MCP tools
which are available from the connector. Do NOT modify the `allowed-tools` field.

**VALIDATE**:
```bash
grep "^version:" plugins/hal/skills/hal/SKILL.md
grep "## /hal list" plugins/hal/skills/hal/SKILL.md
```

---

### Task 3 — EDIT plugin.json: bump to 0.5.0

**UPDATE**: `plugins/hal/.claude-plugin/plugin.json`

- Change `"version": "0.4.0"` → `"version": "0.5.0"`

**VALIDATE**:
```bash
cat plugins/hal/.claude-plugin/plugin.json | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['version']=='0.5.0', d['version']; print('OK')"
```

---

### Task 4 — EDIT marketplace.json: bump to 0.5.0 (must match plugin.json)

**UPDATE**: `.claude-plugin/marketplace.json`

- Change `"version": "0.4.0"` → `"version": "0.5.0"` inside the `plugins[0]` object

**VALIDATE**:
```bash
cat .claude-plugin/marketplace.json | python3 -c "import json,sys; d=json.load(sys.stdin); v=d['plugins'][0]['version']; assert v=='0.5.0', v; print('OK')"
```

**CRITICAL**: also verify both files match:
```bash
python3 -c "
import json, pathlib
p = json.loads(pathlib.Path('plugins/hal/.claude-plugin/plugin.json').read_text())
m = json.loads(pathlib.Path('.claude-plugin/marketplace.json').read_text())
assert p['version'] == m['plugins'][0]['version'], f'MISMATCH: plugin={p[\"version\"]} market={m[\"plugins\"][0][\"version\"]}'
print(f'Versions match: {p[\"version\"]}')
"
```

---

### Task 5 — PREPEND CHANGELOG entry

**UPDATE**: `plugins/hal/CHANGELOG.md`

Prepend the `[0.5.0]` entry (see Phase 4 above) immediately after the file header
and versioning convention block, before the existing `[0.4.0]` entry.

**VALIDATE**:
```bash
head -30 plugins/hal/CHANGELOG.md | grep "\[0.5.0\]"
```

---

### Task 6 — Final consistency check

```bash
# All versions
echo "=== hal SKILL.md ===" && grep "^version:" plugins/hal/skills/hal/SKILL.md
echo "=== plugin.json ===" && python3 -c "import json; print(json.load(open('plugins/hal/.claude-plugin/plugin.json'))['version'])"
echo "=== marketplace.json ===" && python3 -c "import json; print(json.load(open('.claude-plugin/marketplace.json'))['plugins'][0]['version'])"

# /hal list section exists
grep -n "## /hal list" plugins/hal/skills/hal/SKILL.md

# /hal list comes before /hal update
python3 -c "
content = open('plugins/hal/skills/hal/SKILL.md').read()
li = content.index('## /hal list')
up = content.index('## /hal update')
assert li < up, f'list ({li}) must come before update ({up})'
print('Order OK: /hal list before /hal update')
"
```

---

## TESTING STRATEGY

### Manual smoke test (no CI)

This is a skill file (markdown instructions). Validation is:
1. File is valid markdown and loads cleanly
2. Section exists at the right position (before `/hal update`)
3. Version numbers are consistent across all three files
4. CHANGELOG entry is present

Functional test: run `/hal list` in Claude Cowork after plugin reinstall — out of
scope for this plan (done by the user post-release).

### Edge cases to document in the skill section

- No projects → `Aucun projet dans le workspace <slug>.`
- Empty stage → skip that stage header
- `amount_ht` null → show `—`
- `company` null → show `—` for company column
- `project_ref` null → show `—` as ref
- `description` received → ignore (never display in kanban)
- `closed_at` present on terminal stage → show date
- Unknown workspace slug → `list_projects` will return an error; surface it verbatim

---

## VALIDATION COMMANDS

### Level 1 — File consistency

```bash
grep "^version:" plugins/hal/skills/hal/SKILL.md
python3 -c "import json; print(json.load(open('plugins/hal/.claude-plugin/plugin.json'))['version'])"
python3 -c "import json; print(json.load(open('.claude-plugin/marketplace.json'))['plugins'][0]['version'])"
```

Expected: `0.4.0`, `0.5.0`, `0.5.0`

### Level 2 — Content check

```bash
grep -n "^## /hal" plugins/hal/skills/hal/SKILL.md
```

Expected output order: `list`, `update`, `devis`

### Level 3 — JSON validity

```bash
python3 -m json.tool plugins/hal/.claude-plugin/plugin.json > /dev/null && echo "plugin.json OK"
python3 -m json.tool .claude-plugin/marketplace.json > /dev/null && echo "marketplace.json OK"
```

### Level 4 — Version sync

```bash
python3 -c "
import json, pathlib
p = json.loads(pathlib.Path('plugins/hal/.claude-plugin/plugin.json').read_text())
m = json.loads(pathlib.Path('.claude-plugin/marketplace.json').read_text())
assert p['version'] == m['plugins'][0]['version']
print(f'Sync OK: {p[\"version\"]}')
"
```

---

## ACCEPTANCE CRITERIA

- [ ] `/hal list [workspace]` section added to `hal/SKILL.md`, ordered before `/hal update`
- [ ] Section calls `list_projects` MCP tool (no Bash, no scripts)
- [ ] Output: text kanban grouped by stage, active stages before terminal
- [ ] Line format: `ref · company · amount · location`
- [ ] `description` field NOT displayed
- [ ] Null fields show `—`
- [ ] Terminal stages show `closed_at` date when present
- [ ] Default workspace: `blue-green`; optional arg accepts slug or shorthand (`ic`)
- [ ] Optional filters documented: `stage=<value>` and `kind=<value>`
- [ ] `hal` skill version bumped: `0.3.0` → `0.4.0` in SKILL.md frontmatter
- [ ] plugin.json bumped to `0.5.0`
- [ ] marketplace.json bumped to `0.5.0` (matches plugin.json exactly)
- [ ] CHANGELOG entry for `[0.5.0]` prepended with correct date
- [ ] All validation commands pass

---

## COMPLETION CHECKLIST

- [ ] Task 1: SKILL.md read and structure understood
- [ ] Task 2: `/hal list` section inserted, version bumped to `0.4.0`
- [ ] Task 3: plugin.json bumped to `0.5.0`
- [ ] Task 4: marketplace.json bumped to `0.5.0`, sync verified
- [ ] Task 5: CHANGELOG `[0.5.0]` entry prepended
- [ ] Task 6: all validation commands pass
- [ ] `hal/.claude/STATUS.md` updated (move `/hal list` from Backlog to Done)

---

## NOTES

### Why no MCP server changes

`list_projects` (hal-mcp `index.ts` lines 345–382) already:
- Returns id, name, stage, kind, amount_ht, currency, location, project_ref,
  closed_at, created_at + joined company{name} and contact{name, email}
- Supports `workspace_slug`, `kind`, `stage` filters
- Orders by `created_at DESC`

No server-side changes needed.

### Why pure-instruction (no script)

`/hal update` is the reference: MCP tools from the connector are available
natively in Claude Code — no subprocess needed. Zero cold-start cost. This is
the canonical pattern for connector-backed commands in bluegreen-marketplace.

### Stage ordering in the kanban

Active stages order (Blue Green / IC): `prospect → devis_a_rediger → devis_envoye`
Terminal stages: `solde`, `perdu`

The skill must NOT hardcode these values — it must call `list_stages` to get
the canonical order, or derive the order from the projects returned (active
stages = those without `closed_at`, terminal = those with `closed_at`).
Simplest heuristic: group by stage value from the data, terminal = stages where
all projects have a non-null `closed_at`. Don't call an extra MCP if avoidable.

### Confidence score

**9/10** — single file edit + version bumps, tool already deployed and tested,
clear pattern from `/edifice list` (same release). Only risk: stage ordering
logic in the kanban (no server-side ordering by stage sequence — must derive
from data or hardcode active-before-terminal heuristic).
