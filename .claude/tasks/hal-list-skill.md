# Feature: /hal list [workspace]

## Goal
Add `/hal list [workspace]` command to the hal skill — text kanban via `list_projects` MCP.

## Context
- **Plan Reference**: `.claude/plans/hal-list-skill.md`
- **Related Files**: `plugins/hal/skills/hal/SKILL.md`, `plugins/hal/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `plugins/hal/CHANGELOG.md`

## Tasks

### Phase 1: Read & Understand
- [x] Task 1: Read SKILL.md end-to-end, confirm version 0.3.0, identify insertion point ✓ 2026-06-08

### Phase 2: Implementation
- [x] Task 2: Edit SKILL.md — add `/hal list` section before `/hal update`, bump version 0.3.0 → 0.4.0 ✓ 2026-06-08
- [x] Task 3: Edit plugin.json — bump version 0.4.0 → 0.5.0 ✓ 2026-06-08
- [x] Task 4: Edit marketplace.json — bump version 0.4.0 → 0.5.0, verify sync ✓ 2026-06-08
- [x] Task 5: Prepend CHANGELOG entry [0.5.0] ✓ 2026-06-08

### Phase 3: Validation
- [x] Task 6: Run all validation commands (versions, content order, JSON validity) ✓ 2026-06-08

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `plugins/hal/skills/hal/SKILL.md` | Modify | Add `/hal list` section + bump version to 0.4.0 |
| `plugins/hal/.claude-plugin/plugin.json` | Modify | Bump version to 0.5.0 |
| `.claude-plugin/marketplace.json` | Modify | Bump version to 0.5.0 |
| `plugins/hal/CHANGELOG.md` | Modify | Prepend [0.5.0] entry |

## Notes
- No MCP server changes — `list_projects` already deployed in hal-mcp v27
- `allowed-tools` frontmatter NOT modified — list_projects available via connector
- Stage ordering heuristic: terminal = projects with non-null `closed_at`

## Completion
- **Started**: 2026-06-08
- **Completed**: 2026-06-08
- **Commit**: (link to commit when done)
