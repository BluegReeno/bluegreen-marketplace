# Changelog — edifice

All notable changes to this plugin are documented here.

## Versioning convention

`0.MINOR.PATCH` (pre-1.0):
- **PATCH** (`0.x.Y+1`) — bugfix, optional field, internal improvement with no interface impact
- **MINOR** (`0.X+1.0`) — interface change: new required field, renamed command, observable behaviour change

Requires the `hal` plugin, which carries the `hal-mcp` connector this plugin's skill calls.

---

## [0.1.2] — 2026-09-03 — build_context carries the mission brief and stops swallowing the parse; /edifice push documented against hal-mcp v75

## [0.1.1] — 2026-08-28 — follow hal-mcp's list_edifice_missions envelope

`hal#119` stopped the three hal-mcp listing tools from silently truncating: they now return
`{items, total, returned, truncated}` instead of a bare array. `listMissions` was typed
`MissionSummary[]` and received an object, so the mission list rendered nothing from the moment
hal-mcp v64 was deployed.

Consumes the envelope, and renders a line when rows were withheld rather than dropping the
`truncated` flag on the floor — swallowing it would rebuild the very defect `hal#119` removed,
one layer up.

## [0.1.0] — 2026-08-02 — extract edifice from the hal monolith

## [0.0.0] — seed

Placeholder entry so version-sync stays green while the plugin is being extracted from the
`hal` monolith (#66). Superseded by `0.1.0`, the first released version.
