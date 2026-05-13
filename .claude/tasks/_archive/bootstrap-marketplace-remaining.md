# Feature: bootstrap-marketplace-remaining

## Goal
Complete the bluegreen-marketplace bootstrap sprint: add schema-contract + release log to edifice, enforce schema rule in CLAUDE.md, remove old marketplace.json from edifice, fix CHANGELOG in bluegreen-marketplace.

## Context
- **Plan**: `.agents/plans/bootstrap-marketplace-remaining-tasks.md`
- **Two repos**: `~/Projects/edifice` (private) and `~/Projects/bluegreen-marketplace` (public)

## Tasks

### Phase 1: edifice repo — source of truth files
- [x] Create `edifice/plugins/edifice-mission-report/schema-contract.json` ✓ 2026-05-13
- [x] Create `edifice/docs/plugin-release-log.md` ✓ 2026-05-13

### Phase 2: edifice repo — CLAUDE.md rule
- [x] Append schema-contract enforcement rule to `edifice/CLAUDE.md` ✓ 2026-05-13

### Phase 3: edifice repo — remove old marketplace.json
- [x] Delete `edifice/.claude-plugin/marketplace.json` ✓ 2026-05-13

### Phase 4: bluegreen-marketplace — fix CHANGELOG
- [x] Fix pull_mission.py description: "Supabase SDK" → "stdlib urllib" ✓ 2026-05-13

### Phase 5: Validation
- [x] Level 1: JSON validity (both schema-contract files) ✓ 2026-05-13
- [x] Level 2: diff between edifice and marketplace schema-contract returns zero ✓ 2026-05-13
- [x] Level 3: marketplace.json version === plugin.json version ✓ 2026-05-13
- [x] Level 4: file existence / deletion checks ✓ 2026-05-13
- [x] Level 5: CHANGELOG fix verified ✓ 2026-05-13

### Phase 6: Commits
- [x] Commit edifice repo changes ✓ 2026-05-13 (79b52b591)
- [x] Commit bluegreen-marketplace changes ✓ 2026-05-13 (ffa41f8)

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `edifice/plugins/edifice-mission-report/schema-contract.json` | Create | Source of truth (mirror of marketplace version) |
| `edifice/docs/plugin-release-log.md` | Create | Append-only release log, v0.3.3 entry |
| `edifice/CLAUDE.md` | Modify | Append schema-contract enforcement rule |
| `edifice/.claude-plugin/marketplace.json` | Delete | Old private registry, replaced by bluegreen-marketplace |
| `bluegreen-marketplace/plugins/edifice-mission-report/CHANGELOG.md` | Modify | Fix pull_mission.py description (line 12) |

## Notes
- schema-contract.json in edifice must be identical to the marketplace mirror (diff = zero)
- The `_note` field is present in both files
- Do NOT touch `edifice/plugins/edifice-mission-report/.claude-plugin/plugin.json`

## Completion
- **Started**: 2026-05-13
- **Completed**: 2026-05-13
- **Commit**: edifice `79b52b591` / bluegreen-marketplace `ffa41f8`
