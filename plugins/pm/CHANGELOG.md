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

Neither dependency is removed here — `Skill(jobsearch-vault)` and the gmail-mcp tool stay in
`allowed-tools` — but as of 0.1.1 both skills degrade gracefully (`jobsearch:DOWN`, mirroring the
pre-existing `gmail:DOWN` pattern) instead of silently showing misleading zero-activity metrics
when the `jobsearch` plugin is absent, which is the expected shape for an installer who only wants
`/pm`. A generic vertical-extension mechanism (so `pm` can declare optional verticals — `edifice`,
`jobsearch` — instead of hardcoding tool/skill names per skill) is still undesigned; Claude Code
has no `optionalDependencies` primitive in `plugin.json` to build it on. Tracked in
[#65](https://github.com/BluegReeno/bluegreen-marketplace/issues/65).

---

## [0.1.4] — 2026-08-14 — route sprint rollover through `transition_sprint`, derive sprint number from MAX

**Skill half of a two-repo fix; the server half (`hal#99`, hal-mcp v61) landed first.** The
backend now enforces `UNIQUE (workspace_slug, sprint_number)`, a CHECK on `status`, and a
partial unique index guaranteeing at most one sprint `status="actuel"` per workspace —
`update_sprint` rejects any attempt to set a second `actuel`. A new tool,
`transition_sprint(workspace_slug, incoming_sprint_id)`, demotes the outgoing `actuel` to
`dernier` and promotes the incoming sprint to `actuel` in one transaction; it is now the only
correct rollover path.

- `pm`, `sprint-planner`: added `mcp__plugin_hal_hal-mcp__transition_sprint` to `allowed-tools`.
- `pm` (SKILL + `commands/pm.md`): routing a sprint to `status="actuel"` ("le sprint est
  actuel", "passe le sprint X en actuel") now calls `transition_sprint`, never `update_sprint`.
  All other status/field changes keep using `update_sprint` unchanged.
- `sprint-planner`: ÉTAPE 6 no longer derives the next sprint number from the current sprint's
  `sprint_number + 1` — three past duplicate-number cleanups renumbered sprints to free slots
  instead of resequencing the whole series (the number is embedded in the sprint name), leaving
  gaps (`blue-green` 31→33, `renaud` 7→8-9). The next number now comes from
  `MAX(sprint_number)` across **all** sprints in the workspace (any status), computed in the
  same `list_sprints` call ÉTAPE 6a already needed for idempotence. ÉTAPE 6b's old
  close-then-create sequence (`list_sprints(status="actuel")` + a loop of
  `update_sprint(status="passes")`, which also demoted to the wrong semantic status —
  `passes` instead of `dernier`) is replaced by `transition_sprint` when a conflicting
  `actuel` sprint already exists.

Not changed, per explicit backend-scope decision on 2026-08-14: no automatic closure of expired
sprints, `starts_at`/`ends_at` stay nullable, `status` stays explicit rather than derived from
dates. A skill must still surface the absence of a current sprint explicitly rather than picking
one arbitrarily — zero sprints in `status="actuel"` remains possible even though at most one now
is.

Closes [#68](https://github.com/BluegReeno/bluegreen-marketplace/issues/68).

## [0.1.3] — 2026-08-14 — normalize `priority` against a closed vocabulary

`priority` was written and read as free text. Real workspace data mixed `"normal"`,
`"high"`, `"medium"`, `"Haute"` (French, capitalized), and `null` on the same board, so
the `⚡` kanban marker (strict match on `priority=high`) silently missed tasks. `/pm
task`, `/pm update`, and `/pm tasks` now normalize `priority` against a closed
`urgent`/`high`/`medium`/`low` vocabulary — on write via a lookup table (unknown input →
ask, never write free text) and on read.

**This is the skill half of a two-repo fix, and the server half landed first.** Since
2026-08-14, `hal#97` (hal-mcp **v60**) rejects any non-conforming `priority` on
`create_task` / `update_task` with `Priority '<value>' not allowed. Valid: urgent, high,
medium, low`, backed by a CHECK constraint that binds every other client too; the same
migration normalized the 39 non-conforming rows (`normal` → `medium`, `Haute`/`haute` →
`high`). So this skill does not stand in for a missing server guard — it normalizes French
input ahead of a server that only speaks the canonical form, and surfaces the server's
message unchanged when something slips through.

## [0.1.2] — 2026-08-13 — fix sprint-planner/sprint-review date comparisons — >= / <= inside [ ] silently failed in bash and zsh, all jobsearch metrics read 0

## [0.1.1] — 2026-08-08 — graceful degradation when jobsearch is absent

- `sprint-planner`, `sprint-review`: added `jobsearch:DOWN` handling (mirrors `gmail:DOWN`) so both
  skills skip their jobsearch-dependent sections cleanly — instead of silently rendering
  zero-activity metrics — when the vault isn't mounted or the `jobsearch:jobsearch-vault` skill
  isn't available. Sprint-critical date computation (`SPRINT_STATUS`, `NEXT_MON`, `NEXT_FRI`) no
  longer lives inside the vault-dependent branch, so it still runs when jobsearch is down.
- `commands/sprint-planner.md`, `commands/sprint-review.md`: fixed a stale reference to the
  `briefing` plugin (leftover from the #66 adoption) — both commands now correctly point at the
  `pm` plugin skill.

## [0.1.0] — 2026-08-02 — extract pm, adopt sprint-planner and sprint-review

## [0.0.0] — seed

Placeholder entry so version-sync stays green while `pm` is being extracted from the `hal`
monolith and the two sprint skills are adopted from `briefing` (#66). Superseded by `0.1.0`,
the first released version.
