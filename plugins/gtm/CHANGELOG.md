# Changelog — gtm

All notable changes to this plugin are documented here.

## Versioning convention

`0.MINOR.PATCH` (pre-1.0):
- **PATCH** (`0.x.Y+1`) — bugfix, optional field, internal improvement with no interface impact
- **MINOR** (`0.X+1.0`) — interface change: new required field, renamed command, observable behaviour change

Requires the `hal` plugin, which carries the `hal-mcp` connector this plugin's skills call.

---

## [0.2.0] — 2026-08-14 — /crm log update

Add `/crm log update` to correct an already-logged interaction (`summary`, `transcript`,
`channel`, `occurred_at`, `contact_id`, `project_id`, `tags`) via the new `update_interaction`
hal-mcp tool (hal-mcp v60, deployed 2026-08-14). Previously a logged interaction was immutable —
the only "fix" was creating a duplicate via `/crm log`. `interaction_id` has no MCP lookup path
(`list_interactions` does not exist), so `/crm log` now echoes the created `interaction_id` and
`/crm log update` resolves it from conversation context only. No delete path — none is exposed.

Closes #27.

## [0.1.0] — 2026-08-02 — extract crm and linkedin from the hal monolith

## [0.0.0] — seed

Placeholder entry so version-sync stays green while `crm` and `linkedin` are being extracted
from the `hal` monolith (#66). Superseded by `0.1.0`, the first released version.
