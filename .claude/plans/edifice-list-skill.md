# Feature: /edifice list — skill bluegreen-marketplace

The following plan should be complete. Validate file contents and version numbers
before starting — plugin.json has a known version mismatch documented below.

**IMPORTANT — Run this plan from the `bluegreen-marketplace` repo root.**
All paths below are relative to `~/Projects/bluegreen-marketplace/`.
Open Claude Code in that directory before executing.

Pay close attention to the versioning policy in `CLAUDE.md`
and to the `edifice` skill's `allowed-tools` frontmatter constraint.

## Feature Description

Add a `/edifice list` command to the `edifice` skill
(`plugins/hal/skills/edifice/SKILL.md`). The command calls
the existing `list_edifice_missions` MCP tool and formats the result so the
technician can immediately identify the right `mission_id` before running
`/edifice pull`.

No backend changes. The `list_edifice_missions` tool already exists in
`hal/supabase/functions/hal-mcp/index.ts` (lines 299–321) and already returns
the right fields, sorted `created_at DESC`.

## User Story

As a BET technician (Laurent / Steeve / Yani)  
I want to type `/edifice list` and see my missions sorted from newest to oldest  
So that I can instantly identify which `mission_id` to copy before `/edifice pull`

## Problem Statement

Before pulling a mission, the technician must know its UUID. Currently there is
no quick list command — the user has to look it up manually in Supabase or in
the `.edifice.md` briefing file. If the briefing file doesn't exist yet (new
session, different machine), there's no easy way to find the UUID.

## Solution Statement

A pure-instruction command in the `edifice` SKILL.md: call `list_edifice_missions`
via MCP, format the result as a human-readable table sorted by date (newest first),
and surface the `id` (UUID) for each mission. No scripts, no Bash — identical
architecture to `/hal update` in `hal/SKILL.md`.

## Feature Metadata

**Feature Type**: New Capability (new command in existing skill)  
**Estimated Complexity**: Low  
**Primary Systems Affected**: `plugins/hal/skills/edifice/SKILL.md`  
**Dependencies**: None — `list_edifice_missions` MCP tool already deployed (hal-mcp v26)

---

## CONTEXT REFERENCES

### Relevant Codebase Files — READ BEFORE IMPLEMENTING

- `plugins/hal/skills/edifice/SKILL.md` (entire file)
  → This is the only file receiving a content change. Read it to understand
    the existing command sections format before adding `/edifice list`.

- `plugins/hal/skills/hal/SKILL.md`
  → Reference for a pure-instruction skill section with no Bash (no `allowed-tools`
    extension needed). `/edifice list` follows the same pattern.

- `plugins/hal/CHANGELOG.md` (lines 1–40)
  → Version format and entry template to follow.

- `plugins/hal/.claude-plugin/plugin.json`
  → Current version: `"0.2.0"`. See Version Mismatch below.

- `.claude-plugin/marketplace.json`
  → Must stay in sync with plugin.json version at all times.

- `CLAUDE.md`
  → Full versioning policy, bump rules, release process.

- `hal/supabase/functions/hal-mcp/index.ts` (lines 299–321)
  → `list_edifice_missions` tool: read to understand the exact response schema.

### New Files to Create

None. This feature adds a section to an existing SKILL.md only.

### MCP Tool — `list_edifice_missions` (already deployed, no change needed)

```
Tool: list_edifice_missions
Input:
  status?: string   -- filter by status (e.g. "active", "completed"), optional
  limit?:  number   -- max results, default 50

Response shape (okResult → JSON array):
[
  {
    "id":              "uuid",          // ← this is the mission_id for /edifice pull
    "name":            "Diagnostic Varenne",
    "type":            "diagnostic",    // diagnostic | suivi_chantier | devis
    "status":          "active",
    "mission_context": "...",           // may be null or long text — do NOT display
    "created_at":      "2026-05-28T...",
    "building": {
      "name":    "Immeuble Varenne",
      "address": "46 Rue de Varenne 75007 Paris"
    }                                   // may be null if no building attached
  }
]
```

---

## VERSION MISMATCH — FIX FIRST

**Observed state** (verified in planning):

| File | Value |
|------|-------|
| `CHANGELOG.md` latest entry | `[0.3.0] — 2026-06-06` |
| `plugins/hal/.claude-plugin/plugin.json` | `"version": "0.2.0"` |
| `.claude-plugin/marketplace.json` | `"version": "0.2.0"` |
| `plugins/hal/skills/edifice/SKILL.md` frontmatter | `version: 0.2.0` |

The CHANGELOG was written for `0.3.0` but the json files were not bumped.
**Treat CHANGELOG as source of truth** — the last released version is `0.3.0`.

**Action for this release**: implement the feature and release as `0.4.0`.

---

## IMPLEMENTATION PLAN

### Phase 1: Understand the current SKILL.md structure

Read `plugins/hal/skills/edifice/SKILL.md` end-to-end.
Identify:
- Where the command sections begin (`## /edifice pull`, `## /edifice improve`, etc.)
- The frontmatter format (name, description, version, allowed-tools)
- Insert position for the new section (add `/edifice list` as the **first** section,
  before `/edifice pull` — it's the logical first step)

### Phase 2: Add `/edifice list` section to SKILL.md

Insert the new command section at the **top of the command sections**, between the
plugin directory + path resolution block and `## /edifice pull`.

The section must:

1. Call `list_edifice_missions` via MCP (no Bash, no scripts)
2. Display results as a formatted markdown table: **Date | Nom | Type | Statut | Bâtiment**
3. Date format: `YYYY-MM-DD` (extract from `created_at`)
4. Skip the `mission_context` field — too verbose, not useful for listing
5. Handle the case where `building` is null (show `—` in that column)
6. After the table, remind the user how to pull: show the UUID for the first/selected mission
7. Support optional filters: `status=<value>` and `limit=N` passed as free-text to the command

**Section to add** (exact text — adapt if context requires):

```markdown
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
| Date       | Nom                       | Type           | Statut    | Bâtiment / Adresse          |
|------------|---------------------------|----------------|-----------|-----------------------------|
| 2026-05-28 | Diagnostic Varenne        | diagnostic     | active    | 46 Rue de Varenne 75007 Paris |
| 2026-05-12 | Suivi chantier Aulnay     | suivi_chantier | completed | Résidence Les Tilleuls       |
```

**3. Surface the mission_id**

After the table, add:

```
Pour puller une mission : /edifice pull avec mission_id = <UUID>

Exemple : mission_id de "Diagnostic Varenne" = 2d3138cb-7bdb-4236-a29f-5ea51883b363
```

If only one result is returned (e.g. `limit=1`), show the UUID inline in the table
or directly below. If multiple results, list all UUIDs at the end or on request.
```

### Phase 3: Version bumps

Apply **all four** version bumps in the same edit pass:

| File | Old | New | Reason |
|------|-----|-----|--------|
| `plugins/hal/skills/edifice/SKILL.md` frontmatter `version:` | `0.2.0` | `0.3.0` | MINOR — new command |
| `plugins/hal/.claude-plugin/plugin.json` `"version"` | `0.2.0` | `0.4.0` | Fix 0.2→0.3 gap + this release |
| `.claude-plugin/marketplace.json` `"version"` (inside plugins array) | `0.2.0` | `0.4.0` | Must mirror plugin.json |

**plugin.json and marketplace.json MUST show the same version number. Always.**

### Phase 4: CHANGELOG entry

Prepend a new entry to `plugins/hal/CHANGELOG.md`:

```markdown
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
```

---

## STEP-BY-STEP TASKS

### Task 1 — READ the current SKILL.md

**READ**: `plugins/hal/skills/edifice/SKILL.md`

- Understand the exact structure (frontmatter block, plugin dir block, command sections)
- Confirm current version in frontmatter is `0.2.0`
- Identify the exact insertion point for `/edifice list`
  (after the path-resolution block and before `## /edifice pull`)

**VALIDATE**: File loads cleanly, version confirmed.

---

### Task 2 — EDIT SKILL.md: add `/edifice list` section + bump version

**UPDATE**: `plugins/hal/skills/edifice/SKILL.md`

- **PATCH frontmatter**: `version: 0.2.0` → `version: 0.3.0`
- **INSERT** the `/edifice list` section (see Phase 2 above) immediately before
  `## /edifice pull` — this is the logical order (list first, then pull)

**PATTERN**: Follow the existing section format (h2 header, short description,
numbered steps, code blocks for tool calls and output format)

**GOTCHA**: `/edifice list` needs **no new allowed-tools** — it only calls MCP tools
which are available from the connector. Do NOT modify the frontmatter `allowed-tools`
field (keep as-is — it exists for the Bash-heavy commands like `/edifice pull`
and `/edifice report`).

**VALIDATE**:
```bash
# Check the file is valid markdown and version is bumped
grep "^version:" plugins/hal/skills/edifice/SKILL.md
grep "## /edifice list" plugins/hal/skills/edifice/SKILL.md
```

---

### Task 3 — EDIT plugin.json: bump to 0.4.0

**UPDATE**: `plugins/hal/.claude-plugin/plugin.json`

- Change `"version": "0.2.0"` → `"version": "0.4.0"`

**VALIDATE**:
```bash
cat plugins/hal/.claude-plugin/plugin.json | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['version']=='0.4.0', d['version']; print('OK')"
```

---

### Task 4 — EDIT marketplace.json: bump to 0.4.0 (must match plugin.json)

**UPDATE**: `.claude-plugin/marketplace.json`

- Change `"version": "0.2.0"` → `"version": "0.4.0"` inside the `plugins[0]` object

**VALIDATE**:
```bash
cat .claude-plugin/marketplace.json | python3 -c "import json,sys; d=json.load(sys.stdin); v=d['plugins'][0]['version']; assert v=='0.4.0', v; print('OK')"
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

Prepend the `[0.4.0]` entry (see Phase 4 above) immediately after the file header
and versioning convention block, before the existing `[0.3.0]` entry.

**VALIDATE**:
```bash
head -30 plugins/hal/CHANGELOG.md | grep "\[0.4.0\]"
```

---

### Task 6 — Final consistency check

```bash
# All versions
echo "=== SKILL.md ===" && grep "^version:" plugins/hal/skills/edifice/SKILL.md
echo "=== plugin.json ===" && python3 -c "import json; print(json.load(open('plugins/hal/.claude-plugin/plugin.json'))['version'])"
echo "=== marketplace.json ===" && python3 -c "import json; print(json.load(open('.claude-plugin/marketplace.json'))['plugins'][0]['version'])"

# /edifice list section exists
grep -n "## /edifice list" plugins/hal/skills/edifice/SKILL.md

# /edifice list comes before /edifice pull
python3 -c "
content = open('plugins/hal/skills/edifice/SKILL.md').read()
li = content.index('## /edifice list')
pu = content.index('## /edifice pull')
assert li < pu, f'list ({li}) must come before pull ({pu})'
print('Order OK: /edifice list before /edifice pull')
"
```

---

## TESTING STRATEGY

### Manual smoke test (no CI)

This is a skill file (markdown instructions). The only validation is:
1. The file is valid markdown and loads cleanly
2. The section exists at the right position
3. The version numbers are consistent
4. The CHANGELOG entry is present

The functional test is running `/edifice list` in Claude Cowork after the plugin
is installed — out of scope for this plan (done by the user post-release).

### Edge cases to document in the skill section

- `building` is null → show `—` in the Bâtiment column
- 0 results → tell the user "Aucune mission trouvée" (no table)
- `mission_context` field received → ignore it (too verbose)
- User wants to filter → instruct to pass `status="active"` as MCP param
- User wants fewer results → instruct to pass `limit=10`

---

## VALIDATION COMMANDS

### Level 1 — File consistency

```bash
# All three version numbers match expectations
grep "^version:" plugins/hal/skills/edifice/SKILL.md
python3 -c "import json; print(json.load(open('plugins/hal/.claude-plugin/plugin.json'))['version'])"
python3 -c "import json; print(json.load(open('.claude-plugin/marketplace.json'))['plugins'][0]['version'])"
```

Expected: `0.3.0`, `0.4.0`, `0.4.0`

### Level 2 — Content check

```bash
# Section exists and is in the right order
grep -n "^## /edifice" plugins/hal/skills/edifice/SKILL.md
```

Expected output order: `list`, `pull`, `improve`, `report`, `push`

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

- [ ] `/edifice list` section added to `edifice/SKILL.md`, ordered before `/edifice pull`
- [ ] Section calls `list_edifice_missions` MCP tool (no Bash, no scripts)
- [ ] Output format: markdown table with Date / Nom / Type / Statut / Bâtiment columns
- [ ] `mission_context` field is NOT displayed
- [ ] Null building handled gracefully (shows `—`)
- [ ] `mission_id` (UUID) surfaced clearly after the table
- [ ] Optional filters documented: `status=<value>` and `limit=N`
- [ ] Edifice skill version bumped: `0.2.0` → `0.3.0` in SKILL.md frontmatter
- [ ] plugin.json bumped to `0.4.0`
- [ ] marketplace.json bumped to `0.4.0` (matches plugin.json exactly)
- [ ] CHANGELOG entry for `[0.4.0]` prepended with correct date
- [ ] All validation commands pass

---

## COMPLETION CHECKLIST

- [ ] Task 1: SKILL.md read and structure understood
- [ ] Task 2: `/edifice list` section inserted, version bumped to `0.3.0`
- [ ] Task 3: plugin.json bumped to `0.4.0`
- [ ] Task 4: marketplace.json bumped to `0.4.0`, sync verified
- [ ] Task 5: CHANGELOG `[0.4.0]` entry prepended
- [ ] Task 6: all validation commands pass
- [ ] `hal/.claude/STATUS.md` updated (move `/edifice list` from Backlog to Done)

---

## NOTES

### Why no MCP server changes

`list_edifice_missions` (hal-mcp `index.ts` lines 299–321) already:
- Returns `id, name, type, status, mission_context, created_at, building(name, address)`
- Orders by `created_at DESC`
- Supports `status` filter and `limit` param

No server-side changes needed. The tool was designed for exactly this use case
(`description: "Use this to find a mission_id before calling get_mission_with_assets"`).

### Why pure-instruction (no script)

The `hal` SKILL.md is the reference: MCP tools from the connector are available
natively in Claude Code — no subprocess needed. Zero cold-start cost. This is the
canonical pattern for connector-backed commands in bluegreen-marketplace.

### RLS — auth model

`list_edifice_missions` uses `getDb(extra)` (JWT-based client) — it reads only
rows the authenticated user's JWT can see via RLS. The tool does not use
`getDbAdmin` so the listing is correctly scoped to the user's org.

### Confidence score

**9/10** — single file edit + version bumps, tool already deployed and tested,
clear pattern from existing skills. Only risk: ensuring `/edifice list` is
inserted at exactly the right position in SKILL.md without disrupting the
plugin-dir / path-resolution block that precedes all command sections.
