# CLAUDE.md — bluegreen-marketplace

## Language Policy

- **Conversations**: French OK
- **Code, filenames, commits**: English only
- **Documentation** (`docs/*.md`, `README.md`, `CHANGELOG.md`): English

---

## Project Overview

**bluegreen-marketplace** is the public distribution layer for all BlueGreen Claude Code plugins. It decouples plugin distribution (public) from plugin development (private repos `edifice` and `hal`).

Clients install plugins via:
```
/plugin marketplace add BluegReeno/bluegreen-marketplace
```

**Distribution channel**: Renaud uses **Claude Desktop** (Customize → Plugins personnels → Hal).
Updates appear as a "Mettre à jour" button when the remote version > installed version.
Claude Desktop reads versions from `marketplace.json` → `plugins[0].version` and compares
with the cached installed version. **This is why version bumps in every release are mandatory** —
without a version bump, Claude Desktop won't surface the update and clients stay on the old code.

| Plugin | Status | Skills |
|--------|--------|--------|
| `hal` | `plugins/hal/` — developed here | `edifice` + `pm` |
| `hal-crm` | placeholder — future sprint | — |

---

## Repo Structure

```
bluegreen-marketplace/
├── .claude-plugin/
│   └── marketplace.json          # registry entry point (Anthropic schema)
├── plugins/
│   ├── hal/
│   │   ├── .claude-plugin/plugin.json
│   │   ├── .mcp.json             # hal-mcp SSE server + version
│   │   ├── skills/
│   │   │   ├── edifice/SKILL.md  # /edifice — building inspection reports
│   │   │   └── pm/SKILL.md       # /pm list | tasks | new | task | log | doc | sprint | update — project management via hal-mcp
│   │   ├── scripts/
│   │   │   ├── *.py              # edifice: build_context, render_*, download_photos
│   │   │   └── obsidian/         # bundled obsidian-crm scripts ← source of truth ★
│   │   │       ├── obsidian_api.py
│   │   │       ├── note_schemas.py
│   │   │       ├── search_vault.py
│   │   │       ├── read_note.py
│   │   │       ├── list_notes.py
│   │   │       ├── create_note.py
│   │   │       ├── update_frontmatter.py
│   │   │       ├── sprint_transition.py
│   │   │       └── references/schemas.md
│   │   ├── commands/
│   │   │   ├── pm.md             # /pm slash command (routes to pm skill)
│   │   │   └── edifice.md        # /edifice slash command (routes to edifice skill)
│   │   ├── templates/            # *.docx report templates
│   │   ├── organizations/        # client config
│   │   ├── requirements.txt
│   │   └── CHANGELOG.md
│   └── hal-crm/
│       └── .gitkeep              # placeholder — future sprint
├── docs/
│   ├── brief.md                  # sprint brief and architectural decisions
│   ├── INSTALL.md                # one-liner install instructions
│   └── skills-mcp-guide.md       # skill vs command architecture, MCP check, cross-platform
└── README.md                     # public-facing install guide
```

### Skills vs Commands — why both exist

Claude Code has two separate invocation systems:

| System | Directory | Invocation |
|--------|----------|-----------|
| **Skill** | `skills/<name>/SKILL.md` | Semantic trigger OR `plugin:skill` menu (e.g., `hal:pm`) |
| **Command** | `commands/<name>.md` | Direct slash syntax: `/pm`, `/edifice` |

Skills are always namespaced (`hal:pm`) — typing `/pm` raw looks for a **command**, not a skill.
`commands/pm.md` and `commands/edifice.md` register the bare slash commands.
The command file must be self-contained — the skill body is NOT pre-loaded when a command fires.

See `docs/skills-mcp-guide.md` for the full reference (MCP detection, cross-platform).

---

### Source of truth — obsidian-crm scripts

`plugins/hal/scripts/obsidian/` **is the single source of truth** for vault I/O scripts. Do not sync from `MyClaudeSkills/obsidian-crm` or any other location at runtime — the bundle is self-contained for Cowork ephemeral sandboxes.

---

## Versioning Policy

Each component tracks its own version independently.

| Component | Version field | File |
|-----------|--------------|------|
| Plugin `hal` | `"version"` | `plugins/hal/.claude-plugin/plugin.json` |
| Skill `edifice` | `version:` frontmatter | `plugins/hal/skills/edifice/SKILL.md` |
| Skill `pm` | `version:` frontmatter | `plugins/hal/skills/pm/SKILL.md` |
| MCP `hal-mcp` | `"version"` | `plugins/hal/.mcp.json` |
| Marketplace plugin entry | `plugins[name].version` | `.claude-plugin/marketplace.json` |
| Marketplace top-level | `version` | `.claude-plugin/marketplace.json` |

**Bump rule per release:**
- Each modified component → PATCH+1 on that component
- Plugin → always PATCH+1 once per release (regardless of how many components changed)
- Marketplace plugin entry (`plugins[name].version`) = plugin version (always in sync)
- Marketplace top-level `version` → monotonic PATCH+1 on every release, independent of plugin version numbers
- `MINOR` (`0.x.0`) for interface changes (new command, new required field)
- `PATCH` (`0.0.x`) for bugfix and internal improvements

**Example:**

| Release | What changed | `edifice` | `pm` skill | `hal-mcp` | plugin |
|---------|-------------|:---------:|:-----------:|:---------:|:------:|
| v0.1.0 (initial) | — | 0.1.0 | 0.1.0 | 0.1.0 | **0.1.0** |
| next — edifice only | edifice bugfix | **0.1.1** | 0.1.0 | 0.1.0 | **0.1.1** |
| next — pm skill | new vault field | 0.1.1 | **0.1.1** | 0.1.0 | **0.1.2** |
| next — Supabase migration | pm skill interface | 0.1.1 | **0.2.0** | **0.2.0** | **0.2.0** |

---

## Release Process (manual — no CI)

Releases are intentional and infrequent (~1-2/month). No GitHub Actions by design (see `docs/brief.md` — Out of scope).

```bash
# 1. Bump version in each modified component (see Versioning Policy above)
# 2. Bump plugin version in plugin.json and marketplace.json (must stay identical)
# 3. Add a CHANGELOG.md entry for the new version (required — no push without it)
# 4. Commit and push
git add -A && git commit -m "chore(hal): release vX.Y.Z"
```

---

## schema-contract.json — Cross-repo sync anchor ★

`plugins/hal/schema-contract.json` will declare which Supabase tables/columns this plugin
depends on. It is a mirror — the source of truth lives in `edifice/plugins/hal/schema-contract.json`.

> **Status**: not yet created — planned for a future sprint (hal v0.3.0+).

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

## Common Gotchas

- `marketplace.json` **plugin entry** (`plugins[name].version`) must match `plugin.json` version — always in sync. The **top-level** `version` is a separate monotonic counter, incremented by one PATCH on every release.
- Component skill versions (SKILL.md) are independent — they only bump when that skill changes
- `hal` plugin is developed directly in this repo (`plugins/hal/`)
- `plugins/hal/scripts/obsidian/` is the source of truth for vault I/O — do not edit scripts elsewhere
- `plugins/hal-crm/` is intentionally empty — do not add code until the hal CRM Postgres migration is done

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
