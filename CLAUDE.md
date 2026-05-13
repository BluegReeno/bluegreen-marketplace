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

| Plugin | Source repo | Status |
|--------|------------|--------|
| `edifice-mission-report` | `edifice/plugins/edifice-mission-report/` | v0.3.3 — live |
| `hal-crm` | `hal/plugins/hal-crm/` | placeholder — future sprint |

---

## Repo Structure

```
bluegreen-marketplace/
├── .claude-plugin/
│   └── marketplace.json          # registry entry point (Anthropic schema)
├── plugins/
│   ├── edifice-mission-report/   # mirrored from edifice (manual sync on release)
│   │   ├── .claude-plugin/plugin.json
│   │   ├── skills/edifice/SKILL.md
│   │   ├── *.py                  # pull_mission, render_*, pair scripts
│   │   ├── templates/            # *.docx report templates
│   │   ├── requirements.txt
│   │   ├── schema-contract.json  # cross-repo sync anchor ★
│   │   └── CHANGELOG.md
│   └── hal-crm/
│       └── .gitkeep              # placeholder — future sprint
├── docs/
│   ├── brief.md                  # sprint brief and architectural decisions
│   └── INSTALL.md                # one-liner install instructions
└── README.md                     # public-facing install guide
```

---

## Release Process (manual — no CI)

Releases are intentional and infrequent (~1-2/month). No GitHub Actions by design (see `docs/brief.md` — Out of scope).

```bash
# 1. Copy plugin from edifice
rsync -av --delete \
  ../edifice/plugins/edifice-mission-report/ \
  plugins/edifice-mission-report/

# 2. Bump version in .claude-plugin/marketplace.json
# 3. Append entry to edifice/docs/plugin-release-log.md
# 4. Commit and push
git add -A && git commit -m "chore: sync edifice-mission-report vX.Y.Z"
```

---

## schema-contract.json — Cross-repo sync anchor ★

`plugins/edifice-mission-report/schema-contract.json` declares which Supabase tables/columns this plugin depends on. It is a mirror — the source of truth lives in `edifice/plugins/edifice-mission-report/schema-contract.json`.

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

- `marketplace.json` version must match `plugin.json` version after each sync
- Do not develop plugin code here — development happens in `edifice/` and `hal/`
- `plugins/hal-crm/` is intentionally empty — do not add code until the hal CRM Postgres migration is done

---

## Session Management

- Use `/handoff` before ending long sessions
- Use `/commit` with the `Context:` section when AI context files change
- After any plugin sync: verify `marketplace.json` version === `plugin.json` version
