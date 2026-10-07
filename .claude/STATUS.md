# STATUS — bluegreen-marketplace

Last updated: 2026-10-07

> History up to 2026-09-09 lives in [`STATUS-ARCHIVE.md`](./STATUS-ARCHIVE.md), verbatim and in
> French. Nothing below repeats it.

## Current Focus

Three plugins live — `hal` 0.12.0 (connector only), `gtm` 0.2.6, `pm` 0.3.0, top-level 0.10.34
(`marketplace.json`); `edifice` archived at tag `archive/edifice-plugin`. Next: land the two open PRs.

## In Progress

- [ ] PR [#101](https://github.com/BluegReeno/bluegreen-marketplace/pull/101) — `gtm:call`, `/crm log`
      retired (`hal#192` phase B). Written against `gtm` 0.3.0 / top-level 0.10.31, both overtaken
      by the 2026-10-07 releases: rebase, renumber, then release through `release.sh`. No CI run.
- [ ] PR [#103](https://github.com/BluegReeno/bluegreen-marketplace/pull/103) — new `docs` plugin
      (`brand`, `study-report`, `proposal`). CI green. Merging it adds a fourth plugin: update
      `BLUEGREEN_MAP.md` and this file's plugin list in the same session.
- [ ] **Local branch `wip/edifice-front-mcp` can go.** Its unfinished exploration targeted
      `ui/edifice-front/`, archived on 2026-10-07; deleting it also drops the 28 contaminated blobs
      left in the local object store (residual accepted when `#95` was closed). Renaud's call.

## Backlog

- [ ] Decide on a single install channel for `hal` and `pm`: today both reach a Claude Code session twice, via the CLI install (`~/.claude/plugins/cache/bluegreen-marketplace/`) and via the Claude Desktop sync (`~/.claude/plugins/synced/…/{hal,pm}~g2`); versions matched on 2026-09-30 after a manual `claude plugin update`, but the CLI copy had silently stayed on `pm` 0.1.9 for a month

**Open issues**

- [ ] [#97](https://github.com/BluegReeno/bluegreen-marketplace/issues/97) — `crm`: the opportunity
      carries an aggregated, traceable BANT; the call report keeps only the meeting. Overlaps
      PR #101 (`gtm:call` writes BANT bullets to the opportunity) — re-scope after it merges
- [ ] [#35](https://github.com/BluegReeno/bluegreen-marketplace/issues/35) — `/linkedin stats`
      subcommand: analyse and log a post
- [ ] [#21](https://github.com/BluegReeno/bluegreen-marketplace/issues/21) — link internal projects
      to commercial opportunities, consolidated view (needs a hal migration)
- [ ] [#13](https://github.com/BluegReeno/bluegreen-marketplace/issues/13) — connect `hal-mcp` to
      Gemini Enterprise (console steps, do from the desktop)

**Traps that have bitten and are not fixed**

- CI checks that `allowed-tools` is *present*, never that its names *resolve*. A dead MCP prefix
  goes green (`rm#88`, 2026-08-09). `pm` depends on `briefing` being installed, no longer on
  `jobsearch` — nothing enforces that.
- `skill-improve`'s release contract was fixed (`archon-workflows#30`, closed 2026-09-04), but it
  still cannot create a plugin, ignores issue comments, and has no "no action" exit. Fine on a
  corrected issue body; do not use it for structural work.
- Two publications can land in a single top-level increment with no conflict: git merges identical
  edits silently, and `check_version_sync.sh` does not look at the top-level counter.

## Done (current sprint)

- [x] Released `pm` **0.3.0** (`sprint-review` retired, q12) and `gtm` **0.2.6** (no `/edifice` routing); `edifice` archived (#106, tag `archive/edifice-plugin`) — 2026-10-07
- [x] `#100` — `sprint-planner` no longer names any appointment: capacity is 35h minus the job-search blocks, the LinkedIn post and the events actually read from the declared calendars (the IC Ingénieurs weekly meeting, stopped end of August, was still costing 1h and pushing Monday's block). Planned-week dates now derive from the weekday, with catch-up of a week left without a sprint; `pm` **0.2.1**, top-level **0.10.31**. `sprint-review` kept the old `next monday` / `next friday` lines until it was retired in `pm` 0.3.0 — 2026-09-30
- [x] `/doctor` audit of the marketplace skills: 5 `404: Not Found` files and the unused `.claude/rules/` removed, `/handoff` pointer replaced by `session:wrap-up`, repo tree and Release Process trimmed out of CLAUDE.md (release procedure now in `.claude/skills/release/`), `Bash(pip *)` dropped from `edifice` allowed-tools, `sprint-planner` / `sprint-review` descriptions shortened — 2026-09-30
