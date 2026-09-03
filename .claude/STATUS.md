# STATUS — bluegreen-marketplace

Last updated: 2026-09-03

> History up to 2026-08-29 lives in [`STATUS-ARCHIVE.md`](./STATUS-ARCHIVE.md), verbatim and in
> French. Nothing below repeats it.

## Current Focus

Four plugins published — `hal` **0.12.0** (the connector alone: `.mcp.json` and nothing else),
`edifice` **0.1.2**, `gtm` **0.2.4**, `pm` **0.2.0**, marketplace top-level **0.10.28** (read from
`marketplace.json`). In flight: PR for `#93`, catching the `edifice` plugin up to hal-mcp v75/v76.

## In Progress

- [ ] [#93](https://github.com/BluegReeno/bluegreen-marketplace/issues/93) — `edifice` **0.1.2**
      opened as a PR: `build_context.py` carries the mission brief instead of swallowing the parse,
      and `/edifice push` is documented against hal-mcp v75. Awaiting review.

## Backlog

**Open issues**

- [ ] [#84](https://github.com/BluegReeno/bluegreen-marketplace/issues/84) — no parity check between
      `build_context.py` and its TypeScript port in `hal-mcp`
- [ ] [#49](https://github.com/BluegReeno/bluegreen-marketplace/issues/49) — `/edifice`: help the
      technician write the report from the front (phase 2, the write path)
- [ ] [#35](https://github.com/BluegReeno/bluegreen-marketplace/issues/35) — `/linkedin stats`
      subcommand: analyse and log a post
- [ ] [#21](https://github.com/BluegReeno/bluegreen-marketplace/issues/21) — link internal projects
      to commercial opportunities, consolidated view (needs a hal migration)
- [ ] [#13](https://github.com/BluegReeno/bluegreen-marketplace/issues/13) — connect `hal-mcp` to
      Gemini Enterprise (console steps, do from the desktop)

**Unfiled, proposed** — `ui/edifice-front/` ships no tests. Three were proposed on 2026-07-28
(`fragment` target, size-ceiling boundary, `check_artifact_sync.sh` hand-edit detection); they are
one gap and deserve one issue.

**Traps that have bitten and are not fixed**

- CI checks that `allowed-tools` is *present*, never that its names *resolve*. A dead MCP prefix
  goes green (`rm#88`, 2026-08-09). `pm` depends on `briefing` being installed, no longer on
  `jobsearch` — nothing enforces that.
- `skill-improve` still requires the `version:` frontmatter of `SKILL.md`, dropped from this repo
  on 2026-08-02, and its `verify-all-versions` node is told to repair the divergence *and push*.
  Runs have refused on their own judgement. Filed as
  [`archon-workflows#30`](https://github.com/BluegReeno/archon-workflows/issues/30). A run on a
  corrected issue body is fine; do not use it for structural work.
- Two publications can land in a single top-level increment with no conflict: git merges identical
  edits silently, and `check_version_sync.sh` does not look at the top-level counter.

## Done (current sprint)

- [x] `867e028` — `/pm new` sends `kind` and `stage`, both required by `create_project` since
      `hal#161`; `pm` **0.2.0**. Landed straight on `main` without `release.sh`, so the top-level
      counter was not bumped for it — that is the third trap below, observed — 2026-09-02
- [x] `#89` / PR #90 — `hal#135` lot D: the tag doctrine became a one-line pointer in 8 files;
      `gtm` **0.2.4** / `pm` **0.1.9**, top-level **0.10.27**. Same pass defused the `kind_stages`
      trap in `gtm/skills/crm/SKILL.md` ahead of `hal#137` — 2026-08-29
- [x] `#79` / PR #80 — `sprint-planner` followed `gmail-mcp` from `jobsearch` to `briefing`, merged
      *before* the PR opposite so no window existed where the step pointed nowhere — 2026-08-18
- [x] `#81` / PR #82 — `list_tasks` returns `{tasks, total, returned, truncated}`; `sprint-review`
      now shows the truncation instead of publishing wrong figures — 2026-08-18
