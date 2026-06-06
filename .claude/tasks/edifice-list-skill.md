# Feature: /edifice list — new command in edifice skill

## Goal
Add `/edifice list` command to `plugins/hal/skills/edifice/SKILL.md` so technicians can list missions and find `mission_id` before `/edifice pull`.

## Context
- **Plan Reference**: `.claude/plans/edifice-list-skill.md`
- **Related Files**: `plugins/hal/skills/edifice/SKILL.md`, `plugins/hal/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `plugins/hal/CHANGELOG.md`

## Tasks

### Implementation
- [x] Task 1: READ SKILL.md — understand structure, confirm version `0.2.0`, identify insertion point @claude ✓ 2026-06-06
- [x] Task 2: EDIT SKILL.md — insert `/edifice list` section before `/edifice pull` + bump version `0.2.0` → `0.3.0` ✓ 2026-06-06
- [x] Task 3: EDIT plugin.json — bump version `0.2.0` → `0.4.0` ✓ 2026-06-06
- [x] Task 4: EDIT marketplace.json — bump version `0.2.0` → `0.4.0`, verify sync ✓ 2026-06-06
- [x] Task 5: PREPEND CHANGELOG entry for `[0.4.0]` ✓ 2026-06-06

### Validation
- [x] Task 6: Run all validation commands (versions, order, JSON validity, sync) ✓ 2026-06-06

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `plugins/hal/skills/edifice/SKILL.md` | Modify | Add `/edifice list` section + bump version to `0.3.0` |
| `plugins/hal/.claude-plugin/plugin.json` | Modify | Bump version to `0.4.0` |
| `.claude-plugin/marketplace.json` | Modify | Bump version to `0.4.0` |
| `plugins/hal/CHANGELOG.md` | Modify | Prepend `[0.4.0]` entry |

## Notes
- VERSION MISMATCH: CHANGELOG already has `[0.3.0]` entry but plugin.json/marketplace.json are still `0.2.0`. Treat CHANGELOG as source of truth → release as `0.4.0`.
- `/edifice list` uses MCP only (no Bash) — do NOT modify `allowed-tools` frontmatter.
- plugin.json and marketplace.json MUST always show the same version.

## Completion
- **Started**: 2026-06-06
- **Completed**: 2026-06-06
- **Commit**: (pending /commit)
