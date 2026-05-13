# Feature: bootstrap-marketplace-remaining-tasks

The following plan should be complete, but validate the current state of each file before executing — some tasks may already be done in a prior session.

Pay special attention to the two-repo nature of this work: `bluegreen-marketplace` (public) and `edifice` (private). Both repos are at `~/Projects/`.

## Feature Description

This plan covers the **remaining tasks** to complete the `bluegreen-marketplace` bootstrap sprint. The bluegreen-marketplace repo is already largely bootstrapped (plugin files, schema-contract mirror, CHANGELOG, marketplace.json at v0.3.3). What remains is exclusively in the `edifice` private repo plus one small CHANGELOG fix in the marketplace.

## User Story

As a Blue Green developer releasing an Edifice plugin update,
I want a `schema-contract.json` in the edifice repo, a release log, and a cleaned-up CLAUDE.md rule,
So that future releases are self-documenting, the old marketplace.json is gone, and the contract enforcement rule is in place.

## Problem Statement

The `edifice` private repo still has:
1. No `plugins/edifice-mission-report/schema-contract.json` (source of truth is missing — only the mirror in `bluegreen-marketplace` exists)
2. No `docs/plugin-release-log.md` (no release traceability)
3. No schema-contract enforcement rule in `CLAUDE.md`
4. An outdated `.claude-plugin/marketplace.json` pointing to the old edifice-marketplace (should be deleted — replaced by bluegreen-marketplace)

Additionally, `bluegreen-marketplace/plugins/edifice-mission-report/CHANGELOG.md` incorrectly says "Supabase SDK" when `pull_mission.py` uses stdlib `urllib`.

## Solution Statement

Execute 5 targeted tasks (4 in `edifice`, 1 in `bluegreen-marketplace`) to complete the sprint. No new architecture — pure content creation and cleanup.

## Feature Metadata

**Feature Type**: Bootstrap / Infrastructure
**Estimated Complexity**: Low
**Primary Systems Affected**: `edifice` repo (4 files), `bluegreen-marketplace` (1 file fix)
**Dependencies**: None (content/config only — no code, no packages)

---

## CONTEXT REFERENCES

### Relevant Codebase Files — READ THESE BEFORE IMPLEMENTING

- `/Users/renaud/Projects/bluegreen-marketplace/plugins/edifice-mission-report/schema-contract.json` — Mirror already in place. Copy this content to edifice (source of truth). Verified content: plugin v0.3.3, 4 tables (edifice_projects, edifice_buildings, edifice_notes, edifice_photos), hal_mcp_tools with get_mission_with_assets.
- `/Users/renaud/Projects/edifice/CLAUDE.md` (last ~50 lines) — Append schema-contract rule after the existing "Session Management" section.
- `/Users/renaud/Projects/edifice/.claude-plugin/marketplace.json` — DELETE. Confirmed it points to the old `edifice-marketplace` (not bluegreen-marketplace). File has `"name": "edifice-marketplace"` and `"version": "0.2.0"`.
- `/Users/renaud/Projects/bluegreen-marketplace/plugins/edifice-mission-report/CHANGELOG.md` (line 13) — Fix: "Supabase SDK + refresh token" → "stdlib urllib — no SDK required"

### New Files to Create

- `/Users/renaud/Projects/edifice/plugins/edifice-mission-report/schema-contract.json` — Source of truth (same content as marketplace mirror + `_note` field)
- `/Users/renaud/Projects/edifice/docs/plugin-release-log.md` — Release traceability log, v0.3.3 entry

### Patterns to Follow

**schema-contract.json format** — copy from marketplace mirror, which is already correct:
```json
{
  "plugin": "edifice-mission-report",
  "plugin_version": "0.3.3",
  "supabase_tables": {
    "edifice_projects": ["id", "name", "status", "type", "mission_context", "organization_ids", "building_id", "created_at"],
    "edifice_buildings": ["id", "name", "address", "building_type", "description"],
    "edifice_notes": ["id", "name", "content", "zone", "localisation", "ie", "created_at", "updated_at"],
    "edifice_photos": ["id", "filename", "storage_path", "note_id", "created_at"]
  },
  "hal_mcp_tools": [
    { "name": "get_mission_with_assets", "hal_mcp_min_version": "1.0.0" }
  ],
  "_note": "Any Supabase migration that changes a column listed here must update this file and bump plugin_version in the same commit."
}
```

**plugin-release-log.md format** — append-only, from docs/brief.md:
```markdown
## YYYY-MM-DD — plugin-name vX.Y.Z (description)
- What changed
- Migrations landed: list SQL files if any
- schema-contract.json: updated / unchanged
```

**CLAUDE.md schema-contract rule** — from docs/brief.md, verbatim:
```
> Any Supabase migration that adds, removes, or renames a column listed in any plugin's `schema-contract.json` **must** update `schema-contract.json` + bump `plugin_version` in the same commit. No migration lands without updating its contract.
```

---

## IMPLEMENTATION PLAN

### Phase 1: edifice repo — source of truth files

Create `schema-contract.json` and `plugin-release-log.md` in the `edifice` repo.

### Phase 2: edifice repo — CLAUDE.md rule

Append the schema-contract enforcement rule to `edifice/CLAUDE.md`.

### Phase 3: edifice repo — remove old marketplace.json

Delete `.claude-plugin/marketplace.json` from `edifice`. This file duplicated the plugin registry but pointed to the old private `edifice-marketplace`. It is replaced by `bluegreen-marketplace`.

### Phase 4: bluegreen-marketplace — fix CHANGELOG

Correct the factually wrong description of `pull_mission.py` in the CHANGELOG.

### Phase 5: Commit both repos

Commit changes in `edifice` and `bluegreen-marketplace` separately.

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

### CREATE `/Users/renaud/Projects/edifice/plugins/edifice-mission-report/schema-contract.json`

- **IMPLEMENT**: Create the source-of-truth schema-contract. Identical to the marketplace mirror but this is the authoritative copy.
- **CONTENT**: Exact JSON from the pattern above (plugin v0.3.3, 4 tables, hal_mcp_tools, _note field).
- **GOTCHA**: `hal_mcp_min_version` not `hal_mcp_version` — match the marketplace mirror exactly (the brief shows `>=1.0.0` format but the marketplace file uses `"hal_mcp_min_version": "1.0.0"` — use the marketplace file's format as source of truth).
- **VALIDATE**: `python3 -c "import json; json.load(open('/Users/renaud/Projects/edifice/plugins/edifice-mission-report/schema-contract.json')); print('valid JSON')"` → prints "valid JSON"
- **CROSS-CHECK**: `diff /Users/renaud/Projects/edifice/plugins/edifice-mission-report/schema-contract.json /Users/renaud/Projects/bluegreen-marketplace/plugins/edifice-mission-report/schema-contract.json` → zero diff (files must be identical)

### CREATE `/Users/renaud/Projects/edifice/docs/plugin-release-log.md`

- **IMPLEMENT**: Create the append-only release log. First entry for v0.3.3 (2026-05-13).
- **CONTENT**:
  ```markdown
  # Plugin Release Log

  Append-only. One entry per release. Format: date — plugin vX.Y.Z — what changed.

  ---

  ## 2026-05-13 — edifice-mission-report v0.3.3 (initial marketplace publish)

  - Initial publication to bluegreen-marketplace
  - hal-mcp: get_mission_with_assets deployed on prod (Phase 1 MCP ✅)
  - schema-contract.json: matches current prod Supabase tables (added this sprint)
  ```
- **VALIDATE**: `cat /Users/renaud/Projects/edifice/docs/plugin-release-log.md` → shows header + v0.3.3 entry

### UPDATE `/Users/renaud/Projects/edifice/CLAUDE.md` — append schema-contract rule

- **IMPLEMENT**: Append a new section after the existing "Session Management" section (currently the last section).
- **CONTENT to append**:
  ```markdown

  ---

  ## Plugin Schema Contract Rule

  > Any Supabase migration that adds, removes, or renames a column listed in any plugin's `schema-contract.json` **must** update `schema-contract.json` + bump `plugin_version` in the same commit. No migration lands without updating its contract.

  The contract file lives at: `plugins/<plugin-name>/schema-contract.json`
  The mirror lives in `bluegreen-marketplace/plugins/<plugin-name>/schema-contract.json` — keep them in sync on release.
  ```
- **VALIDATE**: `grep -c "schema-contract" /Users/renaud/Projects/edifice/CLAUDE.md` → returns >= 2 (rule is present)

### DELETE `/Users/renaud/Projects/edifice/.claude-plugin/marketplace.json`

- **IMPLEMENT**: Remove the file. Confirmed it contains `"name": "edifice-marketplace"` (old private registry, now replaced by bluegreen-marketplace).
- **EXECUTE**: `rm /Users/renaud/Projects/edifice/.claude-plugin/marketplace.json`
- **GOTCHA**: Check if `.claude-plugin/` directory is now empty — if so, the directory itself can also be removed (or left, check git status). If `plugin.json` also exists at that path for the plugin itself, do NOT delete that.
- **VALIDATE**: `ls /Users/renaud/Projects/edifice/.claude-plugin/` → `marketplace.json` should no longer appear
- **NOTE**: The per-plugin `.claude-plugin/plugin.json` at `edifice/plugins/edifice-mission-report/.claude-plugin/plugin.json` must NOT be touched.

### UPDATE CHANGELOG — fix pull_mission.py description

- **FILE**: `/Users/renaud/Projects/bluegreen-marketplace/plugins/edifice-mission-report/CHANGELOG.md` line 13
- **OLD**: `- `/edifice pull` — pull mission data via `pull_mission.py` (Supabase SDK + refresh token)`
- **NEW**: `- `/edifice pull` — pull mission data via `pull_mission.py` (stdlib urllib — no SDK required)`
- **VALIDATE**: `grep "pull_mission" /Users/renaud/Projects/bluegreen-marketplace/plugins/edifice-mission-report/CHANGELOG.md` → shows "stdlib urllib"

### COMMIT edifice repo changes

- **IN**: `/Users/renaud/Projects/edifice`
- **STAGE**: `schema-contract.json`, `docs/plugin-release-log.md`, `CLAUDE.md`, deletion of `.claude-plugin/marketplace.json`
- **MESSAGE**: `chore: add schema-contract, release log, and schema rule for v0.3.3 marketplace publish`

### COMMIT bluegreen-marketplace changes

- **IN**: `/Users/renaud/Projects/bluegreen-marketplace`
- **STAGE**: `plugins/edifice-mission-report/CHANGELOG.md`
- **MESSAGE**: `fix: correct pull_mission.py dependency description in CHANGELOG`

---

## VALIDATION COMMANDS

### Level 1: JSON validity

```bash
python3 -c "import json; json.load(open('/Users/renaud/Projects/edifice/plugins/edifice-mission-report/schema-contract.json')); print('edifice schema-contract: valid JSON')"
python3 -c "import json; json.load(open('/Users/renaud/Projects/bluegreen-marketplace/plugins/edifice-mission-report/schema-contract.json')); print('marketplace schema-contract: valid JSON')"
```

### Level 2: Schema-contract parity

```bash
diff \
  /Users/renaud/Projects/edifice/plugins/edifice-mission-report/schema-contract.json \
  /Users/renaud/Projects/bluegreen-marketplace/plugins/edifice-mission-report/schema-contract.json
# Expected: zero output (files identical)
```

### Level 3: marketplace.json version === plugin.json version

```bash
python3 -c "
import json
m = json.load(open('/Users/renaud/Projects/bluegreen-marketplace/.claude-plugin/marketplace.json'))
p = json.load(open('/Users/renaud/Projects/bluegreen-marketplace/plugins/edifice-mission-report/.claude-plugin/plugin.json'))
mv = next(x['version'] for x in m['plugins'] if x['name']=='edifice-mission-report')
pv = p['version']
assert mv == pv, f'VERSION MISMATCH: marketplace={mv} plugin={pv}'
print(f'Version check OK: {mv}')
"
```

### Level 4: Files exist / deleted as expected

```bash
# These must exist:
test -f /Users/renaud/Projects/edifice/plugins/edifice-mission-report/schema-contract.json && echo "schema-contract OK" || echo "MISSING"
test -f /Users/renaud/Projects/edifice/docs/plugin-release-log.md && echo "release-log OK" || echo "MISSING"

# This must NOT exist:
test ! -f /Users/renaud/Projects/edifice/.claude-plugin/marketplace.json && echo "old marketplace.json deleted OK" || echo "STILL EXISTS — delete it"

# Schema rule in CLAUDE.md:
grep -q "schema-contract" /Users/renaud/Projects/edifice/CLAUDE.md && echo "schema rule in CLAUDE.md OK" || echo "MISSING rule"
```

### Level 5: CHANGELOG fix verified

```bash
grep "pull_mission" /Users/renaud/Projects/bluegreen-marketplace/plugins/edifice-mission-report/CHANGELOG.md
# Must NOT contain "Supabase SDK"
# Must contain "stdlib urllib"
```

---

## ACCEPTANCE CRITERIA

- [ ] `edifice/plugins/edifice-mission-report/schema-contract.json` exists and is valid JSON
- [ ] `diff` between edifice and marketplace `schema-contract.json` returns zero output
- [ ] `edifice/docs/plugin-release-log.md` exists with the v0.3.3 entry and correct marketplace commit SHA
- [ ] `edifice/CLAUDE.md` contains the schema-contract enforcement rule
- [ ] `edifice/.claude-plugin/marketplace.json` is deleted
- [ ] CHANGELOG no longer says "Supabase SDK" — says "stdlib urllib"
- [ ] `marketplace.json` version (0.3.3) === `plugin.json` version (0.3.3) ✅ (already true, verify unchanged)
- [ ] Both repos committed cleanly

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Level 1: schema-contract JSON validity passes
- [ ] Level 2: schema-contract diff returns zero
- [ ] Level 3: version parity check passes
- [ ] Level 4: file existence / deletion checks pass
- [ ] Level 5: CHANGELOG fix verified
- [ ] `edifice` repo committed
- [ ] `bluegreen-marketplace` repo committed

---

## NOTES

**What's already done in bluegreen-marketplace** (do NOT re-create):
- `CLAUDE.md`, `README.md`, `docs/INSTALL.md`, `docs/brief.md` — all in place
- `.claude-plugin/marketplace.json` — v0.3.3, correct
- All Python scripts (`pull_mission.py`, `push_mission.py`, `render_*.py`, `pair.py`)
- `plugins/edifice-mission-report/schema-contract.json` — mirror, already correct
- `plugins/edifice-mission-report/CHANGELOG.md` — exists, just needs the one-line fix
- `plugins/hal-crm/.gitkeep` — exists

**Out of scope** (per brief, do NOT implement):
- GitHub Actions CI workflow (deliberate: manual sync chosen for low release cadence)
- hal-crm plugin (future sprint)
- Multiple DOCX template versions

**Confidence Score**: 9/10 — all tasks are content creation/deletion with zero code logic. Single risk: the marketplace commit SHA in the release log (get it from `git log` before writing).
