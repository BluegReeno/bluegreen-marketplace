# Changelog — pm

All notable changes to this plugin are documented here.

## Versioning convention

`0.MINOR.PATCH` (pre-1.0):
- **PATCH** (`0.x.Y+1`) — bugfix, optional field, internal improvement with no interface impact
- **MINOR** (`0.X+1.0`) — interface change: new required field, renamed command, observable behaviour change

Requires the `hal` plugin, which carries the `hal-mcp` connector this plugin's skills call.

## Cross-repo couplings — unresolved

`sprint-planner` and `sprint-review` were adopted from `briefing` (`renaud-marketplace`) and still
declare two dependencies owned by that repo:

- `Skill(jobsearch-vault)` — declared by **both** skills; the skill lives in the `jobsearch`
  plugin of `renaud-marketplace`.
- `mcp__plugin_jobsearch_gmail-mcp__search_emails` — declared by `sprint-planner` only; the MCP
  server is carried by the same `jobsearch` plugin.

Neither is resolved here (decision D8 of #66): both skills degrade gracefully when the `jobsearch`
plugin is absent, which is the expected shape for an installer who only wants `/pm`. Tracked in
[#65](https://github.com/BluegReeno/bluegreen-marketplace/issues/65).

---

## [0.0.0] — seed

Placeholder entry so version-sync stays green while `pm` is being extracted from the `hal`
monolith and the two sprint skills are adopted from `briefing` (#66). Superseded by `0.1.0`,
the first released version.
