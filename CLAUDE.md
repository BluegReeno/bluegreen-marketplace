# CLAUDE.md — bluegreen-marketplace

## Language Policy

- **Conversations**: French OK
- **Code, filenames, commits**: English only
- **Documentation** (`docs/*.md`, `README.md`, `CHANGELOG.md`): English

---

## Project Overview

**bluegreen-marketplace** is the public distribution layer for all BlueGreen Claude Code plugins. It decouples plugin distribution (public — this repo, where the four plugins are developed) from the private backend they depend on (`edifice`/`hal-mcp` — the Supabase/MCP server, kept in a separate private repo).

Clients install plugins via:
```
/plugin marketplace add BluegReeno/bluegreen-marketplace
```

**Distribution channel**: Renaud uses **Claude Desktop** (Customize → Plugins personnels → Hal).
Updates appear as a "Mettre à jour" button when the remote version > installed version.
Claude Desktop reads versions from `marketplace.json` → the plugin's `version` entry and compares
with the cached installed version. **This is why version bumps in every release are mandatory** —
without a version bump, Claude Desktop won't surface the update and clients stay on the old code.

### The four plugins — split by installable audience, not by theme

| Plugin | Directory | Skills | Who installs it |
|--------|-----------|--------|-----------------|
| `hal` | `plugins/hal/` | — (connector only) | **everyone** — carries `.mcp.json`, the mandatory base |
| `edifice` | `plugins/edifice/` | `edifice` | IC Ingénieurs Conseils — building inspection missions |
| `pm` | `plugins/pm/` | `pm`, `sprint-planner`, `sprint-review` | anyone running projects and sprints |
| `gtm` | `plugins/gtm/` | `crm`, `linkedin` | Blue Green go-to-market |

Split in #66 (`hal` 0.12.0), because a client who needs `/pm` should not download `/edifice`,
`/crm`, `/linkedin` and ten Python scripts along with it.

**`hal` is the only carrier of the MCP connector** — the three others declare no `.mcp.json` and
call the same server through it. Because `hal` kept its name, the tool prefix stays
`mcp__plugin_hal_hal-mcp__`: no `allowed-tools` list anywhere in the portfolio needs rewriting.
Same model as `briefing` in `renaud-marketplace`, which has consumed this connector without
carrying it since before the split.

---

## Repo Structure

Every plugin has the same three mandatory files — `.claude-plugin/plugin.json`, `CHANGELOG.md`,
and an entry in `marketplace.json`. Creating a plugin means creating all three at once, otherwise
`check_version_sync.sh` fails and **every** release is blocked, not just that plugin's.

```
bluegreen-marketplace/
├── .claude-plugin/
│   └── marketplace.json          # registry entry point (Anthropic schema) — one entry per plugin
├── plugins/
│   ├── hal/                      # the connector — no skill, no command
│   │   ├── .claude-plugin/plugin.json
│   │   ├── .mcp.json             # hal-mcp HTTP server + version ← the only one in the repo
│   │   ├── README.md
│   │   └── CHANGELOG.md
│   ├── edifice/                  # the only plugin carrying scripts, templates and artifacts
│   │   ├── .claude-plugin/plugin.json
│   │   ├── skills/edifice/SKILL.md   # /edifice list | pull | improve | report | push | front
│   │   ├── commands/edifice.md
│   │   ├── scripts/
│   │   │   ├── *.py              # build_context, render_*, download_photos, xml_escape
│   │   │   └── obsidian/         # bundled obsidian-crm scripts ← source of truth ★
│   │   ├── templates/ic-ingenieurs/  # *.docx report templates
│   │   ├── organizations/ic-ingenieurs/  # client config — gitignored, not public
│   │   ├── artifacts/            # committed artifact-front-end HTML — see § Artifact front-ends
│   │   ├── tests/README.md       # points at tests/ at the repo root
│   │   ├── requirements.txt      # human-readable manifest only — never executed
│   │   └── CHANGELOG.md
│   ├── pm/
│   │   ├── .claude-plugin/plugin.json
│   │   ├── skills/
│   │   │   ├── pm/SKILL.md            # /pm list | tasks | new | task | log | doc | sprint | update
│   │   │   ├── sprint-planner/SKILL.md   # adopted from briefing@renaud-marketplace
│   │   │   └── sprint-review/SKILL.md    # idem
│   │   ├── commands/{pm,sprint-planner,sprint-review}.md
│   │   └── CHANGELOG.md          # ← documents the two unresolved cross-repo couplings
│   └── gtm/
│       ├── .claude-plugin/plugin.json
│       ├── skills/
│       │   ├── crm/SKILL.md      # /crm list | new | qualify | log | update | contact | doc
│       │   └── linkedin/SKILL.md # /linkedin idea | backlog | trend | draft | log
│       ├── commands/{crm,linkedin}.md
│       └── CHANGELOG.md
├── tests/                         # ALL tests live here, at the root — never inside a plugin
├── ui/                            # artifact front-end build workspace — see § Artifact front-ends
├── scripts/                       # check_version_sync.sh, check_artifact_sync.sh, release.sh
├── docs/
│   ├── brief.md                  # sprint brief and architectural decisions
│   ├── INSTALL.md                # one-liner install instructions
│   ├── skills-mcp-guide.md       # skill vs command architecture, MCP check, cross-platform
│   └── artifact-front-ends.md    # how a skill consumes a bundled artifact
└── README.md                     # public-facing install guide
```

### Skills vs Commands — why both exist

Claude Code has two separate invocation systems:

| System | Directory | Invocation |
|--------|----------|-----------|
| **Skill** | `skills/<name>/SKILL.md` | Semantic trigger OR `plugin:skill` menu (e.g., `pm:pm`) |
| **Command** | `commands/<name>.md` | Direct slash syntax: `/pm`, `/edifice` |

Skills are always namespaced by their **plugin** (`pm:pm`, `gtm:crm`, `edifice:edifice`) — typing
`/pm` raw looks for a **command**, not a skill. Each plugin's `commands/` files register the bare
slash commands.
The command file must be self-contained — the skill body is NOT pre-loaded when a command fires.

See `docs/skills-mcp-guide.md` for the full reference (MCP detection, cross-platform).

---

### Source of truth — obsidian-crm scripts

`plugins/edifice/scripts/obsidian/` **is the single source of truth** for vault I/O scripts. Do not sync from `MyClaudeSkills/obsidian-crm` or any other location at runtime — the bundle is self-contained for Cowork ephemeral sandboxes.

> It followed `edifice` in the #66 split because it lived under `plugins/hal/scripts/`, but **no
> skill in this repo references it today** (the only mentions left are its own files and archived
> docs). Where it belongs, and whether it should still ship, is open — do not delete it on that
> basis alone.

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
increments by one PATCH whichever plugin it targets. Current state: `hal` 0.12.0, `edifice` 0.1.0,
`pm` 0.1.0, `gtm` 0.1.0, counter 0.10.16.

Skills (`SKILL.md`) no longer carry a `version:` field — there is no per-skill bump ritual.

**Bump rule per release:**
- Plugin → PATCH+1 once per release; the marketplace plugin entry moves with it (stay identical).
- Marketplace top-level `version` → monotonic PATCH+1 on every release, independent of the plugin version.
- Add a `## [<new-version>]` entry to that plugin's `CHANGELOG.md` — CI fails without it.
- `MINOR` (`0.x.0`) for interface changes (new command, new required field); `PATCH` (`0.0.x`) for bugfixes and internal improvements.

**Example:**

| Release | Plugin | What changed | plugin.json | marketplace entry | marketplace top-level |
|---------|--------|-------------|:-----------:|:-----------------:|:---------------------:|
| current | `edifice` | — | 0.1.0 | 0.1.0 | 0.10.16 |
| next — edifice bugfix | `edifice` | skill logic | **0.1.1** | **0.1.1** | **0.10.17** |
| next — new `/pm` field | `pm` | pm interface | **0.2.0** | **0.2.0** | **0.10.18** |

---

## Release Process (one command)

Releases are intentional and infrequent (~1-2/month), and stay a deliberate human act — CI only
enforces the invariant (`.github/workflows/ci.yml` runs `scripts/check_version_sync.sh` + tests on
every PR/push, so a broken version sync or a missing CHANGELOG entry fails the build).

`scripts/release.sh` performs the whole bump in one validated pass so a missed field can no longer
strand Claude Desktop clients on the old version (the top-level marketplace counter is what surfaces
the "Mettre à jour" button — see §Project Overview). It validates everything **before** writing, then:

1. bumps `plugin.json.version`,
2. bumps the matching marketplace plugin entry (kept identical),
3. bumps the marketplace **top-level** `version` (monotonic PATCH +1),
4. prepends a dated `## [<version>]` CHANGELOG entry,
5. runs `scripts/check_version_sync.sh` and aborts if it fails,
6. commits `chore(<plugin>): release v<version>` — **no push, no merge, no tag**.

```bash
# <plugin> <new-version> "<changelog line>"  (--mcp-version <v> also bumps .mcp.json)
bash scripts/release.sh edifice 0.1.1 "fix edifice crop_region off-by-one"
git push        # the human pushes after reviewing the commit
```

It refuses (exit 1, clear message) on: missing args, unknown plugin, a version not strictly
greater than the current one, a dirty working tree, or a CHANGELOG that already lists the version.
A failed validation writes nothing. `.mcp.json` is left untouched unless `--mcp-version` is passed.

---

## schema-contract.json — Cross-repo sync anchor ★

`plugins/edifice/schema-contract.json` will declare which Supabase tables/columns the plugin
depends on. It is a mirror — the source of truth lives in `edifice/plugins/hal/schema-contract.json`
(the private repo's path, unchanged by the split).

> **Status**: not yet created — planned for a future sprint. Since #66 the natural home is
> `edifice`, the plugin that actually reads mission tables, not `hal`, which only carries the
> connector.

**Rule**: after any plugin sync, verify this file matches the current prod Supabase tables. Any version bump that changes table/column dependencies must update this file too.

---

## Core Principles

- **Fix forward** — no backward compatibility, remove deprecated code immediately
- **KISS / YAGNI** — this repo is a distribution layer, not a development environment
- **Clean comments** — describe functionality, not history

---

## Plugin Skill Constraint — Cowork Ephemeral Sandboxes

Claude Cowork mounts a **fresh ephemeral directory each session** — nothing is pre-installed. Every dependency is downloaded from scratch. A slow cold start breaks the UX.

**Rules (non-negotiable for every plugin skill):**
- No `pip install -r requirements.txt` step — ever
- Use stdlib (`urllib`, `json`, `pathlib`, `re`…) wherever possible — `pull_mission.py` is the reference: migrated off `supabase` SDK → stdlib `urllib` for zero cold-start cost
- When a package is unavoidable: `uv run --with pkg1 --with pkg2 script.py` — keep the list as short as possible
- `uv` is the only allowed package manager at runtime. `pip`, `pipenv`, `poetry` are forbidden in skill scripts
- `requirements.txt` is a human-readable manifest only — never executed at runtime

See `docs/brief.md` → "Plugin skill constraints" for full rationale and decision tree.

---

## Artifact front-ends

Rich (React/Tailwind) artifacts are **developed here**, in `ui/`, and **distributed** as a single
committed HTML file under `plugins/edifice/artifacts/`. This repo is both a build environment and a
distribution channel — the two must not contaminate each other.

- **`ui/` is source, never read at runtime.** It is a pnpm workspace at the repo root (sibling to,
  **not** inside, `plugins/edifice/`), one directory per artifact (`ui/<name>/`), pinned to the same
  toolchain as `edifice/local-workspace`. Its `node_modules/` and `dist/` are gitignored and never
  cloned, so the Node toolchain costs plugin installers nothing.
- **`plugins/edifice/artifacts/<name>.html` is the only artifact-facing output** — a single self-contained
  file (JS/CSS/assets inlined, zero external requests per the artifact CSP), committed, built via
  `pnpm --filter <name> build` from within `ui/`. That command runs `vite build` then
  `ui/scripts/build-artifact.mjs`, which stamps provenance, applies the `ARTIFACT_TARGET` shape
  (`cowork` default / `fragment`), enforces the 16 MiB ceiling, and writes the committed file.
- **`scripts/check_artifact_sync.sh` makes "committed output matches source" a machine-checked
  invariant**, not a discipline: it rebuilds every `ui/<name>/` and fails if the committed HTML drifts
  (ignoring only the non-reproducible build-stamp line). CI runs it **only** when `ui/**` or
  `plugins/edifice/artifacts/**` changed, so Python-only PRs stay fast.
- **A hydrated artifact is never written back into the plugin.** When a future skill (`#50`) reads a
  bundled artifact and injects per-session values, the result goes to a **working directory** — never
  back into `plugins/edifice/artifacts/` or anywhere under the plugin root, which is read-only input.
- This is **dev-time / CI-time tooling only.** It never runs inside a live Cowork/Claude Code session,
  so it does not conflict with the "no `pip install` / `uv` only" runtime-skill-script rule above.

See `docs/artifact-front-ends.md` for how a skill consumes a bundled artifact.

---

## Common Gotchas

- `marketplace.json` **plugin entry** (`plugins[name].version`) must match `plugin.json` version — always in sync (enforced by `scripts/check_version_sync.sh`). The **top-level** `version` is a separate monotonic counter, incremented by one PATCH on every release.
- The four plugins are developed directly in this repo, under `plugins/<name>/`
- `plugins/edifice/scripts/obsidian/` is the source of truth for vault I/O — do not edit scripts elsewhere
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

- Use `/handoff` before ending long sessions
- Use `/commit` with the `Context:` section when AI context files change
- After any plugin sync: verify `marketplace.json` version === `plugin.json` version
