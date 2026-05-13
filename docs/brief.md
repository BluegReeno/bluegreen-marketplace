# bluegreen-marketplace — Foundation brief

> **Status**: ready to implement
> **Effort**: ~3-4h
> **Repos touched**: `bluegreen-marketplace` (primary), `edifice` (CI + schema-contract + release log rule)
> **Depends on**: Phase 1 MCP (edifice-mission-report v0.3.3 deployed) ✅

---

## Context

BlueGreen has two private repos (`edifice`, `hal`) where plugin code is developed. Clients install plugins via Claude Code's marketplace system (`/plugin marketplace add <repo>`). Until now the `edifice` repo held the plugin **and** the marketplace registry — a problem because `edifice` is private and contains internal configs.

This sprint creates `BluegReeno/bluegreen-marketplace` as the **public distribution layer** for all BlueGreen Claude Code plugins. It decouples plugin distribution from plugin development and puts in place a release workflow so the marketplace stays in sync with the private repos automatically.

### Plugin roadmap (what will live here)

| Plugin | Source repo | Status |
|---|---|---|
| `edifice-mission-report` | `edifice/plugins/edifice-mission-report/` | **v0.3.3 — migrate now** |
| `hal-crm` | `hal/plugins/hal-crm/` (to be created) | placeholder — future sprint |

---

## Architecture

```
edifice (private)           tag plugin/edifice-v*
                           ──────────────────────►  bluegreen-marketplace (public)
hal (private)              tag plugin/hal-crm-v*         ↑
                           ──────────────────────►  installed by clients via:
                                                    /plugin marketplace add BluegReeno/bluegreen-marketplace
```

### Marketplace repo layout

```
bluegreen-marketplace/
├── .claude-plugin/
│   └── marketplace.json              ← registry entry point (Anthropic schema)
│
├── plugins/
│   ├── edifice-mission-report/       ← mirrored from edifice (auto-sync via CI)
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json           (name, version, description, author)
│   │   ├── skills/
│   │   │   └── edifice/
│   │   │       └── SKILL.md          (frontmatter: name, version, allowed-tools)
│   │   ├── scripts/                  (pull_mission.py, render_*.py, pair.py, etc.)
│   │   ├── templates/                (*.docx report templates)
│   │   ├── requirements.txt
│   │   ├── CHANGELOG.md              ← user-facing, semver
│   │   └── schema-contract.json      ← cross-repo sync anchor ★
│   │
│   └── hal-crm/                      ← placeholder only in this sprint
│       └── .gitkeep
│
├── docs/
│   ├── brief.md                      ← this file
│   └── INSTALL.md                    ← one-liner install instructions
│
├── README.md                         ← public-facing (user install guide)
├── CLAUDE.md                         ← dev rules for this repo
└── .github/
    └── workflows/
        └── sync-edifice-plugin.yml   ← CI: tag in edifice → sync here
```

### In `edifice` repo — additions

```
edifice/
├── .github/
│   └── workflows/
│       └── release-plugin.yml        ← tag trigger → rsync → marketplace push
├── docs/
│   └── plugin-release-log.md         ← append-only release log
└── plugins/
    └── edifice-mission-report/
        └── schema-contract.json      ← added this sprint ★
```

---

## Plugin skill constraints — Cowork ephemeral sandboxes ★

**Context**: Claude Cowork mounts a fresh ephemeral directory for every session. Nothing is pre-installed. Every Python dependency declared in a skill is downloaded from scratch at session start. A slow cold start (>15–20 s) breaks the UX.

### Rule: zero mandatory pre-install step

Skills must **never** require the user to run `pip install -r requirements.txt` or any equivalent before using a command. Each script invocation must be self-sufficient.

### Decision tree for script dependencies

| Situation | Pattern | Example |
|-----------|---------|---------|
| Pure stdlib (json, pathlib, urllib, re…) | `python3 script.py` | `pull_mission.py`, `push_mission.py`, `pair.py` |
| 1–2 small packages, unavoidable | `uv run --with pkg1 --with pkg2 script.py` | `render_report.py` (`python-docx`, `Pillow`) |
| Heavy SDK (supabase, langchain…) | **Refactor to stdlib first** — if impossible, `uv run --with` | `pull_mission.py` was migrated from `supabase` SDK → stdlib `urllib` |

### Established precedent: `/edifice pull`

`pull_mission.py` was explicitly refactored to **remove the `supabase` SDK dependency** entirely. It now uses `urllib` (stdlib) for all Supabase REST calls and token refresh. Result: zero download at session start, instant cold start.

This is the reference implementation. Every new script in every future plugin must start from this constraint:

> **Can this be done with stdlib? If yes, do it. If not, use `uv run --with` with the smallest possible package list.**

### `requirements.txt` — documentation only

`requirements.txt` in the plugin directory is kept as a **dependency manifest for humans**, not for runtime installation. It documents what the plugin depends on in aggregate. It is never executed via `pip install -r`.

### `uv` as the only allowed package manager

`uv` is the only tool plugins may use to pull dependencies at runtime. It is listed as a prerequisite in the marketplace README (`brew install uv`). `pip`, `pipenv`, `poetry` are forbidden in skill scripts.

---

## `schema-contract.json` — the cross-repo sync anchor ★

Lives inside the plugin directory (both in `edifice` and mirrored to `bluegreen-marketplace`).

Declares exactly which Supabase tables/columns and MCP tools this plugin depends on:

```json
{
  "plugin": "edifice-mission-report",
  "plugin_version": "0.3.3",
  "supabase_tables": {
    "edifice_projects":  ["id", "name", "status", "type", "mission_context", "organization_ids", "building_id"],
    "edifice_buildings": ["id", "name", "address", "building_type", "description"],
    "edifice_notes":     ["id", "name", "content", "zone", "localisation", "ie", "created_at", "updated_at"],
    "edifice_photos":    ["id", "filename", "storage_path", "note_id", "created_at"]
  },
  "hal_mcp_tools": [
    { "name": "get_mission_with_assets", "hal_mcp_version": ">=1.0.0" }
  ]
}
```

**Rule added to `edifice/CLAUDE.md`**:
> Any Supabase migration that adds, removes, or renames a column listed in any plugin's `schema-contract.json` **must** update `schema-contract.json` + bump `plugin_version` in the same commit. No migration lands without updating its contract.

---

## CI sync workflow (edifice → marketplace)

### Tag convention (in `edifice` repo)

```bash
git tag plugin/edifice-mission-report/v0.4.0
git push origin plugin/edifice-mission-report/v0.4.0
```

### `edifice/.github/workflows/release-plugin.yml`

```yaml
name: Release plugin to bluegreen-marketplace

on:
  push:
    tags:
      - 'plugin/edifice-mission-report/v*'

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout edifice
        uses: actions/checkout@v4
        with:
          path: edifice

      - name: Checkout bluegreen-marketplace
        uses: actions/checkout@v4
        with:
          repository: BluegReeno/bluegreen-marketplace
          token: ${{ secrets.MARKETPLACE_DEPLOY_TOKEN }}
          path: marketplace

      - name: Extract version from tag
        id: version
        run: echo "VERSION=${GITHUB_REF_NAME#plugin/edifice-mission-report/}" >> $GITHUB_OUTPUT

      - name: Sync plugin files
        run: |
          rsync -av --delete \
            edifice/plugins/edifice-mission-report/ \
            marketplace/plugins/edifice-mission-report/

      - name: Update marketplace.json version
        run: |
          cd marketplace
          python3 -c "
          import json, pathlib
          m = json.loads(pathlib.Path('.claude-plugin/marketplace.json').read_text())
          for p in m['plugins']:
              if p['name'] == 'edifice-mission-report':
                  p['version'] = '${{ steps.version.outputs.VERSION }}'
          pathlib.Path('.claude-plugin/marketplace.json').write_text(json.dumps(m, indent=2) + '\n')
          "

      - name: Commit and push to marketplace
        run: |
          cd marketplace
          git config user.email "ci@bluegreen.ai"
          git config user.name "BlueGreen CI"
          git add -A
          git commit -m "chore: sync edifice-mission-report ${{ steps.version.outputs.VERSION }}" \
            || echo "Nothing to sync"
          git push

      - name: Create GitHub Release in marketplace
        uses: softprops/action-gh-release@v2
        with:
          repository: BluegReeno/bluegreen-marketplace
          token: ${{ secrets.MARKETPLACE_DEPLOY_TOKEN }}
          tag_name: edifice-mission-report-${{ steps.version.outputs.VERSION }}
          name: "edifice-mission-report ${{ steps.version.outputs.VERSION }}"
          body: |
            See [CHANGELOG](https://github.com/BluegReeno/bluegreen-marketplace/blob/main/plugins/edifice-mission-report/CHANGELOG.md) for details.
```

**Setup required once**: create a GitHub PAT (`MARKETPLACE_DEPLOY_TOKEN`) with `repo` scope on `BluegReeno/bluegreen-marketplace` and add it to `edifice` repo secrets.

---

## `edifice/docs/plugin-release-log.md` — release traceability

Append-only. One entry per release. Format:

```markdown
## 2026-05-13 — edifice-mission-report v0.3.3 (initial marketplace publish)
- Initial publication to bluegreen-marketplace
- hal-mcp: get_mission_with_assets deployed on prod (Phase 1 MCP ✅)
- schema-contract.json: matches current prod Supabase tables
- → marketplace commit: (first commit)

## YYYY-MM-DD — edifice-mission-report v0.X.Y
- What changed
- Migrations landed: list SQL files if any
- schema-contract.json: updated / unchanged
- → marketplace commit: <sha>
```

---

## Scope of this sprint

### 1. `bluegreen-marketplace` — bootstrap the repo

- [ ] Replace template `CLAUDE.md` with project-specific rules
- [ ] Replace template `README.md` with public install guide
- [ ] Create `.claude-plugin/marketplace.json` (with edifice-mission-report v0.3.3, hal-crm placeholder)
- [ ] Copy `edifice/plugins/edifice-mission-report/` → `marketplace/plugins/edifice-mission-report/`
- [ ] Create `plugins/edifice-mission-report/schema-contract.json` (current tables as listed above)
- [ ] Create `plugins/edifice-mission-report/CHANGELOG.md` (v0.3.3 entry)
- [ ] Create `plugins/hal-crm/.gitkeep`
- [ ] Create `docs/INSTALL.md`

### 2. `edifice` — release infrastructure

- [ ] Create `plugins/edifice-mission-report/schema-contract.json` (source of truth)
- [ ] Create `docs/plugin-release-log.md` (v0.3.3 entry)
- [ ] Append schema-contract rule to `edifice/CLAUDE.md`
- [ ] Remove `.claude-plugin/marketplace.json` from `edifice` root (replaced by bluegreen-marketplace)

### 3. Smoke test

- [ ] `/plugin marketplace add BluegReeno/bluegreen-marketplace` installs successfully
- [ ] `edifice-mission-report` visible and installable from the marketplace listing

---

## Acceptance criteria

1. From a fresh Claude Code session: `/plugin marketplace add BluegReeno/bluegreen-marketplace` → marketplace registered, plugin `edifice-mission-report` listed.
2. `/plugin install edifice-mission-report@bluegreen-marketplace` → plugin installed, `/edifice pull` triggers correctly.
3. `schema-contract.json` exists in both `edifice/plugins/edifice-mission-report/` and mirrored in marketplace — fields match current prod tables.
4. `edifice/CLAUDE.md` has the schema-contract rule.
5. `edifice/docs/plugin-release-log.md` has the v0.3.3 entry.

---

## Out of scope

- `hal-crm` plugin (separate sprint, after hal CRM Postgres migration is done)
- Auto-update notification system (Claude Code handles this natively)
- Multiple DOCX template versions in marketplace
- Plugin test suite in marketplace (tests stay in `edifice`)
- `edifice/.claude-plugin/marketplace.json` coexistence — remove it, not keep both
- **GitHub Actions CI sync** — deliberate choice: solo dev, low release frequency (~1-2/month). Manual sync (`rsync` + version bump + commit) is sufficient. CI adds infrastructure overhead (PAT tokens, secrets, YAML) with minimal gain. Revisit if release cadence increases significantly.

---

## Files to touch

| File | Repo | Action |
|---|---|---|
| `CLAUDE.md` | bluegreen-marketplace | Replace template with project rules |
| `README.md` | bluegreen-marketplace | Replace with public install guide |
| `.claude-plugin/marketplace.json` | bluegreen-marketplace | Create |
| `plugins/edifice-mission-report/**` | bluegreen-marketplace | Create (copy from edifice) |
| `plugins/edifice-mission-report/schema-contract.json` | bluegreen-marketplace | Create |
| `plugins/edifice-mission-report/CHANGELOG.md` | bluegreen-marketplace | Create |
| `plugins/hal-crm/.gitkeep` | bluegreen-marketplace | Create |
| `docs/INSTALL.md` | bluegreen-marketplace | Create |
| `plugins/edifice-mission-report/schema-contract.json` | edifice | Create (source of truth) |
| `docs/plugin-release-log.md` | edifice | Create |
| `CLAUDE.md` | edifice | Append schema-contract rule |
| `.claude-plugin/marketplace.json` | edifice | Delete (replaced by bluegreen-marketplace) |

---

## New session start

```
/core_piv_loop:prime
# Then: read docs/brief.md → /core_piv_loop:plan-feature
```
