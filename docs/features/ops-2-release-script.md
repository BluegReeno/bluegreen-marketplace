# Brief — Ops 2 (bluegreen-marketplace): one-command release

> **Context**: releasing the `hal` plugin is a manual multi-location version bump; a
> missed bump silently strands Claude Desktop clients on the old version. Ops 1
> (merged) reduced the invariant to two enforced fields + the top-level counter.
> This brief automates the bump. Part of a multi-repo ops track; self-contained.
>
> Read `CLAUDE.md` (§Versioning Policy, §Release Process) first.

## Objective

`scripts/release.sh <plugin> <new-version> "<changelog line>"` performs a complete,
validated release commit.

## Non-goals

- No CI-driven releases, no auto-push, no auto-tag.
- No changes to skills or scripts beyond the release tooling.
- `.mcp.json` server version is NOT bumped by default — only with an explicit
  `--mcp-version <v>` flag (the server version changes only when the Edge Function
  changes).

## Deliverables

### D1 — `scripts/release.sh <plugin> <new-version> "<changelog line>"`

Validate everything before writing anything (all edits or none):

1. Update `plugins/<plugin>/.claude-plugin/plugin.json` `version`.
2. Update the matching plugin entry in `.claude-plugin/marketplace.json`.
3. Bump the top-level `marketplace.json` monotonic counter (patch +1).
4. Prepend a dated entry to `CHANGELOG.md` with the provided line.
5. Run `scripts/check_version_sync.sh` — abort (no commit) if it fails.
6. `git commit -m "chore(<plugin>): release v<new-version>"` — no push; the human
   pushes.

Refuse with exit 1 and a clear message if: plugin unknown; new version not
strictly greater (semver compare); working tree dirty; CHANGELOG already contains
the version; no changelog line given.

### D2 — CLAUDE.md §Release Process update

The manual multi-location checklist is replaced by `scripts/release.sh` + push.
Keep the explanation of why the top-level counter matters (it triggers Claude
Desktop's "Mettre à jour" button).

## Acceptance criteria

```bash
# on a throwaway branch:
bash scripts/release.sh hal <next-patch> "test release" && bash scripts/check_version_sync.sh
git log -1 --format=%s                    # chore(hal): release v<next-patch>
git reset --hard HEAD~1
bash scripts/release.sh hal 0.0.1 "x"; echo $?    # 1 (version not greater)
bash scripts/release.sh; echo $?                   # 1 + usage message
```

## Final reminders

- `set -euo pipefail`; loud, actionable error messages; no partial writes.
- The script never pushes and never merges.
