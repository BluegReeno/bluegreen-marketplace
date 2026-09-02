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
- `mcp__plugin_briefing_gmail-mcp__search_emails` — declared by `sprint-planner` only; the MCP
  server moved from the `jobsearch` plugin to `briefing` in `renaud-marketplace`
  ([rm#96](https://github.com/BluegReeno/renaud-marketplace/pull/96)) — `sprint-planner` now
  requires `briefing` co-installed to reach the perso inbox, not `jobsearch`.

Neither dependency is removed here — `Skill(jobsearch-vault)` and the gmail-mcp tool stay in
`allowed-tools` — but as of 0.1.1 both skills degrade gracefully (`jobsearch:DOWN`, mirroring the
pre-existing `gmail:DOWN` pattern) instead of silently showing misleading zero-activity metrics
when the `jobsearch` plugin is absent, which is the expected shape for an installer who only wants
`/pm`. A generic vertical-extension mechanism (so `pm` can declare optional verticals — `edifice`,
`jobsearch` — instead of hardcoding tool/skill names per skill) is still undesigned; Claude Code
has no `optionalDependencies` primitive in `plugin.json` to build it on. Tracked in
[#65](https://github.com/BluegReeno/bluegreen-marketplace/issues/65).

---

## [0.2.0] — 2026-09-02 — `/pm new` sends the `kind` and the `stage` `create_project` has always demanded

`hal#161` made `create_project.kind` required. It had been declared optional in the tool schema
and written as `kind ?? null` against a `NOT NULL` column, so the advertised optionality was
unreachable: every `/pm new` without a kind already failed, with an opaque `23502` naming a
column no skill mentions. hal now refuses it by name instead.

Fixing that surfaced a second, older gap in this plugin: `stage` was **never** optional in
`create_project` (`z.string()`, no `.optional()`), and neither `commands/pm.md` nor
`skills/pm/SKILL.md` mentioned it at all. `/pm new` was therefore broken on two counts, not one,
and had been since the command was written.

Both sites now send `kind: "project"` — `/pm new` creates an internal project; a commercial
opportunity goes through `/crm new`, which already sent `kind: "opportunity"` and was unaffected —
and read `stage` from `kind_stages.project.active` via `whoami` rather than hard-coding it, because
the stage vocabulary is per workspace and changes without a redeploy.

Requires hal-mcp **v74** or later. `halcrm_projects.stage` is also guarded in Postgres now
(`halcrm_projects_stage_guard`, applied 2026-09-02), so an illegal stage is refused even on a path
that does not cross the edge function.

MINOR per this file's own convention: a new required field.

## [0.1.9] — 2026-08-29 — the `tags` doctrine points at hal-mcp instead of promising a dead resource

`hal#135` (scope D) decided the `tags` doctrine's carrier is hal-mcp itself — its server
`instructions` now state the full rule. The 523-character paragraph duplicated in
`commands/pm.md`, `skills/pm/SKILL.md`, `skills/sprint-planner/SKILL.md` and
`skills/sprint-review/SKILL.md` still promised a `hal://vocabulary` MCP resource that `#135`
ruled out for good — the round-trip cost (`resources/list` + `resources/read`) buys nothing
`whoami` doesn't already give every skill that writes to hal. Reduced to a one-line pointer;
since claude.ai/Cowork never surface a server's `instructions` and Claude Code truncates them
at 2KB, the pointer carries the enforceable minimum itself rather than relying on the
truncated/invisible source.

Closes [#89](https://github.com/BluegReeno/bluegreen-marketplace/issues/89).

## [0.1.8] — 2026-08-28 — every `tags` writer picks from the workspace vocabulary

`whoami` already returns each workspace's `allowed_tags`, but no skill spelled out the rule for
using it — tool descriptions only said tags "must belong to `allowed_tags`" without telling the
model where to find the list. Measured on prod: 67 tag values outside the workspace vocabulary
across 28 rows (`architecte`, `BET-terrain`, `EDF`, `relance`, …), while columns backed by an
explicit rule (`tasks.tags` written by `sprint-planner`, `projects.tags`) stayed clean.

- `pm` (SKILL + `commands/pm.md`), `sprint-planner`, `sprint-review`: added one verbatim
  `Tags.` rule — `tags` means functional domain, pick only from the calling workspace's
  `allowed_tags` (via `whoami`), fall back to `other`, never invent a value, and never
  duplicate what `company_id`/`role`/`channel`/`project_id` already carry. `sprint-planner`
  §6d's ad hoc one-liner is replaced by this same wording so a grep for it finds every writer.
- `sprint-review` **is** a writer: `save_document(domain=…)` writes `documents.domain`, one of
  the three vocabulary columns measured clean on prod. Its own §5b `domain="memory"` rule is
  correct and stays; the shared rule now sits above it so the fleet-wide grep finds this file
  too.
- The rule does **not** claim `hal://vocabulary` exists. That MCP resource is proposed
  (`BluegReeno/hal#123`) and unimplemented, and `ListMcpResourcesTool` currently fails against
  HTTP-transport MCP servers (`anthropics/claude-code#11292`) — which `hal-mcp` is. The wording
  points at `whoami` and is byte-identical to `renaud-marketplace`'s (`rm#107`).

Closes [#86](https://github.com/BluegReeno/bluegreen-marketplace/issues/86).

## [0.1.7] — 2026-08-18 — follow `list_tasks`' new `{tasks, total, returned, truncated}` shape

`hal#105` (`hal-mcp` PR #107) changed `list_tasks` from returning a bare array to
`{ tasks, total, returned, truncated }`, with `limit` now an accepted parameter (server
default: 100 rows). hal-mcp is **not yet deployed** — `make deploy` stays held on
[hal#108](https://github.com/BluegReeno/hal/issues/108) until every consumer, including this
one, is updated; this is the `bluegreen-marketplace` half (the other is
[renaud-marketplace#99](https://github.com/BluegReeno/renaud-marketplace/issues/99)). These
skills describe the call in prose, not code, so the prose is what the model follows — a
documented shape that no longer matched the server would have been a live defect, not a
documentation nit.

- `pm` (SKILL + `commands/pm.md`): every `list_tasks` call site now reads `.tasks`, never the
  raw response. A new shared section documents the shape and the `truncated` contract. `/pm
  tasks --all` — which explicitly wants everything — re-calls with `limit=<total>` on
  `truncated=true` instead of just warning; every other mode (sprint scope, `--status`,
  `--project`, `--tag`, task-resolution fuzzy match) surfaces
  `⚠️ Résultat tronqué : <returned>/<total> tâches affichées.` rather than silently reporting
  on a partial page.
- `sprint-planner`: ÉTAPE 1a and the ÉTAPE 5 backlog `list_tasks` call read `.tasks` and carry
  `truncated[w]`; a truncated workspace gets an explicit warning line in the ÉTAPE 1c bilan
  instead of folding into `taux_global` unannounced.
- `sprint-review`: this is the skill the issue singled out, because its numbers were already
  known to be wrong for one reason (`hal#98`'s `❌ ANNULÉ`-prefix inflation, untouched here)
  and this change could have quietly stacked a second, worse one on top — the workspace this
  runs against holds 111 tasks against a 100-row default, so a review reading "all tasks" was
  silently missing the 11 oldest. ÉTAPE 1's per-workspace bilan and the aggregate "Score
  global" now carry an explicit `⚠️ Résultat tronqué` / `⚠️ Score global partiel` line whenever
  `truncated=true`, and ÉTAPE 4's backlog scan for the next-sprint shortlist warns the same way
  before presenting candidates as the full backlog.

Closes [#81](https://github.com/BluegReeno/bluegreen-marketplace/issues/81).

## [0.1.6] — 2026-08-18 — follow gmail-mcp's move from jobsearch to briefing

`renaud-marketplace#96` moved the `gmail-mcp` connector declaration from the `jobsearch` plugin
to `briefing`, so its tool prefix moved with it:
`mcp__plugin_jobsearch_gmail-mcp__*` → `mcp__plugin_briefing_gmail-mcp__*`. `sprint-planner` was
the one consumer of this tool left outside `renaud-marketplace` (which fixed its own three
consumers in the same PR) — unpatched, its ÉTAPE 3 LinkedIn-alerts step would have called an
unresolvable tool name the moment rm#96 merged.

- `sprint-planner` (SKILL): renamed the tool in `allowed-tools`, the ÉTAPE 3 prose, and the
  actual call; the YAML `description` now names `briefing` as the plugin carrying `gmail-mcp`.
- The dependency itself is unchanged, only its owning plugin: `sprint-planner` now requires
  `briefing` co-installed (not `jobsearch`) to reach the perso inbox for LinkedIn alerts. The
  other cross-repo coupling, `Skill(jobsearch-vault)`, still lives in `jobsearch` and is untouched
  here — see "Cross-repo couplings" above.

Closes [#79](https://github.com/BluegReeno/bluegreen-marketplace/issues/79).

## [0.1.5] — 2026-08-17 — route sprint rollover through `transition_sprint`, derive sprint number from MAX

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

## [0.1.4] — 2026-08-17 — distinguish a cancelled task from a done one

`update_task_status` gained a fifth value on the server side (`hal#98`, hal-mcp **v61**):
`cancelled`, plus an optional `cancelled_reason` accepted only when `status="cancelled"`,
and a `completed_at` column stamped on transitions to `done` (never on `cancelled`). The
skill-side gap this closes: `pm`, `sprint-planner`, and `sprint-review` previously only
knew `done` vs. everything-else, so an abandoned task had no honest home — the workaround
in production was prefixing the title with `❌ ANNULÉ (date, motif) — ` and marking it
`done`, which silently counted backlog cleanup as delivered work (measured impact: `done`
dropped from 158 to 128 once 30 such tasks were properly migrated to `cancelled`, a fifth
of the reported completion count). That title-prefix convention is retired, not
documented — this fix makes the three-bucket distinction (`done` / open / `cancelled`)
structural instead of a naming discipline:

- `pm`: `/pm tasks` kanban gets a dedicated `cancelled` column (always last, never merged
  into `done`), showing `cancelled_reason` when present. `/pm update` and the intent→tool
  table route "annule X" / "X annulée" to `update_task_status(cancelled, cancelled_reason?)`.
  `--status cancelled` is a valid filter. Task-resolution writers document the five-value
  `status` enum.
- `sprint-review`: completion counters (`taux`, `X/Y`) exclude `cancelled` from both
  numerator and denominator — a cancelled task is neither done nor open. Cancelled tasks
  render on their own `🚫 Annulées : N` line, always shown, never folded into `✅`/`⏳`.
- `sprint-planner`: `taux_global` excludes `cancelled` the same way. A `cancelled` task is
  never asked about at ÉTAPE 1c (report/abandon) and never carried into the next sprint —
  it's a terminal state, distinct from `done`.

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
