# Brief — Ops 1 (bluegreen-marketplace): purge + 2-field version policy + CI

> **Context**: the `hal` plugin is lean and healthy. The repo carries dead
> placeholders, stale CLAUDE.md prose, a vendored copy of the Archon skill, and a
> 3-field version-sync ritual with no enforcement. Part of a multi-repo ops track;
> this brief is self-contained for this repo.
>
> Read `CLAUDE.md` before starting. Scope: deletions, version-policy
> simplification, CI bootstrap ONLY.

## Objective

Remove dead weight, reduce the version invariant to two enforced fields, and add a
CI workflow that enforces it plus the existing tests.

## Non-goals (do NOT implement)

- No skill behavior changes (`/pm`, `/crm`, `/edifice`, `/linkedin` untouched
  beyond frontmatter).
- No release automation script (separate brief, Ops 2).
- No changes under `plugins/hal/scripts/` logic.
- `plugins/edifice-mission-report/` is untracked local cruft handled manually —
  do not reference it.

**Deletion safety rule:** grep before deleting; still referenced ⇒ keep + report.

## Deliverables

### D1 — Delete dead placeholders and stale prose

- `plugins/hal-crm/` (empty `.gitkeep` placeholder) — delete it and the "future
  sprint" prose about it in CLAUDE.md.
- CLAUDE.md: remove stale `/hal` command references (renamed `/pm` in PR #24) and
  the contradictory "private repos edifice and hal" development claim.
- Archive one-off planning docs to `docs/_archive/`: `docs/brief-hal-vault-skill.md`,
  `docs/brief-hal-whoami-skill-migration.md`, `docs/loop-2-hal-tasks-skill.md`,
  root `hal-crm-spec.md`.
- Delete vendored `.claude/skills/archon/` (Archon is installed globally; this is
  ~200K of dev-tooling copy, not distributed plugin content).

### D2 — Simplify the version policy (2 fields, not 3+)

Drop the `version:` field from every `plugins/hal/skills/*/SKILL.md` frontmatter
and from the documented sync rule. The enforced invariant becomes:
`plugin.json.version == marketplace.json plugin entry`, plus the top-level
monotonic counter. Rewrite CLAUDE.md §Versioning Policy accordingly.

### D3 — Version-sync check + CI

- `scripts/check_version_sync.sh` (adapt from renaud-marketplace's script of the
  same name): exit 1 if plugin.json ≠ marketplace entry; exit 1 if CHANGELOG.md
  has no entry for the current version.
- `.github/workflows/ci.yml` on `pull_request` + `push` to main:
  `bash scripts/check_version_sync.sh`, plus run the existing pytest suites under
  `plugins/hal/tests/` (invoke them the same way CLAUDE.md documents running them
  today).

## Acceptance criteria

```bash
test ! -d plugins/hal-crm && test ! -d .claude/skills/archon
grep -rn "^version:" plugins/hal/skills/*/SKILL.md | wc -l   # 0
bash scripts/check_version_sync.sh                            # exit 0
ls .github/workflows/ci.yml
grep -rn "/hal " CLAUDE.md | wc -l                            # 0 stale command refs
```

## Final reminders

- No placeholder tests, no TODO comments.
- CI must fail on failure — no `|| true`, no `continue-on-error`.
- PR description lists every deletion and every CLAUDE.md correction.
