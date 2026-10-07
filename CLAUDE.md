# CLAUDE.md — bluegreen-marketplace

## Language Policy

- **Conversations**: French OK
- **Code, filenames, commits**: English only
- **Documentation** (`docs/*.md`, `README.md`, `CHANGELOG.md`): English

---

## Project Overview

**bluegreen-marketplace** is the public distribution layer for all BlueGreen Claude Code plugins. It decouples plugin distribution (public — this repo, where the three plugins are developed) from the private backend they depend on (`hal-mcp` — the Supabase/MCP server, kept in the private `hal` repo).

Clients install plugins via:
```
/plugin marketplace add BluegReeno/bluegreen-marketplace
```

**Distribution channel**: Renaud uses **Claude Desktop** (Customize → Plugins personnels → Hal).
Updates appear as a "Mettre à jour" button when the remote version > installed version.
Claude Desktop reads versions from `marketplace.json` → the plugin's `version` entry and compares
with the cached installed version. **This is why version bumps in every release are mandatory** —
without a version bump, Claude Desktop won't surface the update and clients stay on the old code.

### The three plugins — split by installable audience, not by theme

| Plugin | Directory | Skills | Who installs it |
|--------|-----------|--------|-----------------|
| `hal` | `plugins/hal/` | — (connector only) | **everyone** — carries `.mcp.json`, the mandatory base |
| `pm` | `plugins/pm/` | `pm`, `sprint-planner` | anyone running projects and sprints |
| `gtm` | `plugins/gtm/` | `crm`, `linkedin` | Blue Green go-to-market |

Split in #66 (`hal` 0.12.0), because a client who needs `/pm` should not download `/edifice`,
`/crm`, `/linkedin` and ten Python scripts along with it.

**`hal` is the only carrier of the MCP connector** — the two others declare no `.mcp.json` and
call the same server through it. Because `hal` kept its name, the tool prefix stays
`mcp__plugin_hal_hal-mcp__`: no `allowed-tools` list anywhere in the portfolio needs rewriting.
Same model as `briefing` in `renaud-marketplace`, which has consumed this connector without
carrying it since before the split.

---

## Repo Structure

Every plugin has the same three mandatory files — `.claude-plugin/plugin.json`, `CHANGELOG.md`,
and an entry in `marketplace.json`. Creating a plugin means creating all three at once, otherwise
`check_version_sync.sh` fails and **every** release is blocked, not just that plugin's.

What `ls plugins/*/` does not show:

- `plugins/hal/.mcp.json` is the **only** connector in the repo — see § Common Gotchas.
- `plugins/pm/CHANGELOG.md` documents the two unresolved cross-repo couplings.
- `tests/` at the repo root holds every test — never inside a plugin.

### Skills vs Commands — why both exist

Claude Code has two separate invocation systems:

| System | Directory | Invocation |
|--------|----------|-----------|
| **Skill** | `skills/<name>/SKILL.md` | Semantic trigger OR `plugin:skill` menu (e.g., `pm:pm`) |
| **Command** | `commands/<name>.md` | Direct slash syntax: `/pm`, `/sprint-planner` |

Skills are always namespaced by their **plugin** (`pm:pm`, `gtm:crm`, `pm:sprint-planner`) — typing
`/pm` raw looks for a **command**, not a skill. Each plugin's `commands/` files register the bare
slash commands.
The command file must be self-contained — the skill body is NOT pre-loaded when a command fires.

See `docs/skills-mcp-guide.md` for the full reference (MCP detection, cross-platform).

---

### The `edifice` plugin is archived

Removed from `main` on 2026-10-07 (hal audit q20): hal-mcp no longer serves its six tools (hal#267).
The plugin, its vault scripts, the `ui/` artifact build workspace and its render tests are kept at
the git tag `archive/edifice-plugin` — `git checkout archive/edifice-plugin -- <path>` restores any of them.

---

## Versioning Policy

**Two fields are enforced.** `scripts/check_version_sync.sh` checks them on every PR/push
(CI runs it — see `.github/workflows/ci.yml`), iterating over **every** `plugins/*/` — so a single
broken plugin blocks all releases, not just its own:

1. `plugin.json.version` **==** the marketplace plugin entry (`plugins[name].version`) — always identical.
2. `plugins/<name>/CHANGELOG.md` has a `## [<plugin_ver>]` entry for that version.

The marketplace **top-level** `version` is a monotonic PATCH+1 counter, bumped once per release.

| Component | Version field | File | Enforced |
|-----------|--------------|------|:--------:|
| Each plugin | `"version"` | `plugins/<name>/.claude-plugin/plugin.json` | ✅ (== marketplace entry) |
| Marketplace plugin entry | `plugins[name].version` | `.claude-plugin/marketplace.json` | ✅ (== plugin.json) |
| Marketplace top-level | `version` | `.claude-plugin/marketplace.json` | monotonic counter |
| MCP `hal-mcp` | `"version"` | `plugins/hal/.mcp.json` | tracked, not sync-enforced |

**Plugins version independently.** They share only the top-level counter, which every release
increments by one PATCH whichever plugin it targets. Never quote a current version from this
file — read `.claude-plugin/marketplace.json`, which is the enforced source of truth. This
paragraph used to pin one and was four releases stale.

Skills (`SKILL.md`) no longer carry a `version:` field — there is no per-skill bump ritual.

**Bump rule per release:**
- Plugin → PATCH+1 once per release; the marketplace plugin entry moves with it (stay identical).
- Marketplace top-level `version` → monotonic PATCH+1 on every release, independent of the plugin version.
- Add a `## [<new-version>]` entry to that plugin's `CHANGELOG.md` — CI fails without it.
- `MINOR` (`0.x.0`) for interface changes (new command, new required field); `PATCH` (`0.0.x`) for bugfixes and internal improvements.

**Example:**

Illustrative only — the numbers below are a worked example, not repo state:

| Release | Plugin | What changed | plugin.json | marketplace entry | marketplace top-level |
|---------|--------|-------------|:-----------:|:-----------------:|:---------------------:|
| starting point | `gtm` | — | 0.1.0 | 0.1.0 | 0.10.16 |
| then — gtm bugfix | `gtm` | skill logic | **0.1.1** | **0.1.1** | **0.10.17** |
| then — new `/pm` field | `pm` | pm interface | **0.2.0** | **0.2.0** | **0.10.18** |

---

## Release Process (one command)

Releases are intentional and infrequent (~1-2/month), and stay a deliberate human act — CI only
enforces the invariant. `scripts/release.sh <plugin> <version> "<changelog line>"` performs the
whole bump in one validated pass and commits — **no push, no merge, no tag**. The full procedure
and its refusal cases live in the `release` skill (`.claude/skills/release/SKILL.md`).
## Core Principles

- **Fix forward** — no backward compatibility, remove deprecated code immediately
- **KISS / YAGNI** — this repo is a distribution layer, not a development environment
- **Clean comments** — describe functionality, not history

---

## Plugin Skill Constraint — Cowork Ephemeral Sandboxes

Claude Cowork mounts a **fresh ephemeral directory each session** — nothing is pre-installed. Every dependency is downloaded from scratch. A slow cold start breaks the UX.

**Rules (non-negotiable for every plugin skill):**
- No `pip install -r requirements.txt` step — ever
- Use stdlib (`urllib`, `json`, `pathlib`, `re`…) wherever possible
- When a package is unavoidable: `uv run --with pkg1 --with pkg2 script.py` — keep the list as short as possible
- `uv` is the only allowed package manager at runtime. `pip`, `pipenv`, `poetry` are forbidden in skill scripts
- `requirements.txt` is a human-readable manifest only — never executed at runtime

See `docs/brief.md` → "Plugin skill constraints" for full rationale and decision tree.

---

## Common Gotchas

- `marketplace.json` **plugin entry** (`plugins[name].version`) must match `plugin.json` version — always in sync (enforced by `scripts/check_version_sync.sh`). The **top-level** `version` is a separate monotonic counter, incremented by one PATCH on every release.
- The three plugins are developed directly in this repo, under `plugins/<name>/`
- **Creating a plugin = three files at once** — `plugin.json`, `CHANGELOG.md` with a matching `## [<version>]` entry, and a `marketplace.json` entry. Miss one and `check_version_sync.sh` blocks every plugin's release, not just the new one
- Only `hal` carries a `.mcp.json`. Adding one to another plugin would create a second connector and a second tool prefix — the skills' `allowed-tools` lists all assume `mcp__plugin_hal_hal-mcp__`

---

## Archon Workflows — Correct invocation from Claude Code

Archon works fine inside Claude Code sessions. The `CLAUDECODE` warning is cosmetic —
Archon already strips that env var before spawning any Claude subprocess.

**Two rules to avoid silent failures:**

1. **Never pipe `archon workflow run` output** — `| head`, `| tee`, etc. send SIGPIPE and kill
   Archon before any workflow node executes. Worktrees get created but stay empty.

2. **Launch workflows sequentially** — Archon uses SQLite; simultaneous launches race on the
   db lock and all but one will fail with `database is locked`.

```bash
# Correct: redirect output to a log file, one at a time
ARCHON_SUPPRESS_NESTED_CLAUDE_WARNING=1 archon workflow run skill-improve "19" > /tmp/archon-19.log 2>&1 &

# Monitor:
archon workflow status
tail -f /tmp/archon-19.log

# Launch the next one only after the first is running (status: running confirmed):
ARCHON_SUPPRESS_NESTED_CLAUDE_WARNING=1 archon workflow run skill-improve "20" > /tmp/archon-20.log 2>&1 &
```

For `ai-improvable`-labeled issues: `archon workflow run skill-improve "<issue_number>"`.

---

## Session Management

- Use `session:wrap-up` before ending a session
- Use `/commit` with the `Context:` section when AI context files change
- After any plugin sync: verify `marketplace.json` version === `plugin.json` version
