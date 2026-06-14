# HAL — Claude Plugin

HAL is the second brain and mission workflow for BlueGreen and IC Ingénieurs Conseils.
It ships two skills inside a single plugin:

| Skill | Command | Purpose |
|-------|---------|---------|
| `edifice` | `/edifice pull`, `/edifice improve`, `/edifice report`, `/edifice push` | Pull a building inspection mission from Supabase and render the DOCX report. |
| `hal` | `/hal list`, `/hal tasks`, `/hal update`, `/hal devis` | Query and update the BlueGreen CRM (Supabase) from natural language via **hal-mcp**, plus DOCX devis generation. |

## Prerequisites

### 1. Install `uv` (one-time)

The plugin uses [`uv`](https://docs.astral.sh/uv/) to manage Python dependencies automatically — no venv, no pip.

**Mac:**

```bash
brew install uv
```

**Windows:**

```powershell
winget install astral-sh.uv
```

### 2. Install the plugin (one-time)

In Claude Cowork:

```
/plugin marketplace add BluegReeno/bluegreen-marketplace
/plugin install hal@bluegreen-marketplace
```

### 3. Workspace access (no client-side config)

HAL resolves your default workspace server-side from your Supabase membership — zero environment variables, zero shell config.

Ask your BlueGreen administrator to:

1. Add your email to the workspace(s) you should access (`workspace_members` table).
2. If you belong to several workspaces, flag your default one (`is_default = true`).

Once you're a member, all `/hal list`, `/hal tasks`, and `/hal update` commands resolve to your default workspace automatically (via the `whoami` MCP tool). You can always override it per command: `/hal tasks ic` or `/hal list blue-green`.

### 4. Enable auto-update (recommended)

In Cowork: `/plugin` → Marketplaces tab → select `bluegreen-marketplace` → enable auto-update.

## /edifice

### First time: pair your laptop

1. In Claude Cowork, type `/edifice pair`.
2. The skill calls the Edifice gateway and displays a code (e.g. `ABCD-EFGH`).
3. On your phone, open the Edifice PWA → tap ⚙️ (Settings) → "Connecter un laptop" → enter the code.
4. The laptop is now paired. Credentials are stored in `~/.hal/config.json`.

### Every mission

1. On the phone (Edifice PWA), open a mission and tap **"Exporter pour Cowork"**.
2. Share the generated `.edifice.md` file to your laptop (AirDrop, email, Drive, etc.).
3. Open Claude Cowork in the folder containing the `.edifice.md` file.
4. Ask: *"Pull this mission and generate the report."*

The skill activates automatically when it detects a `*.edifice.md` file. It authenticates using
the stored refresh token, downloads mission data + photos via the **hal-mcp** server, and renders
the DOCX report. The generated report appears in `mission/rapport.docx` next to the briefing file.

## /hal list

Show the CRM pipeline as a text kanban — projects grouped by stage. Active stages come first;
terminal stages (`solde`, `perdu`) are listed last with `✓` and the closing date.

Workspace defaults to your `whoami.default_workspace_slug` (set server-side); pass a slug
explicitly to override.

Examples:

```
/hal list
/hal list ic
/hal list blue-green stage=propale
```

## /hal tasks

Show tasks as a text kanban grouped by status (`todo → in_progress → blocked → ✓ done`). High-priority
tasks are prefixed with `⚡`; tasks attached to a sprint are tagged `[S]`.

Filters: `--mine` (uses `whoami.user_email` — never asks), `--project <ref>`, `--status <s>`,
`--tag <value>`. Tags use the unified vocabulary: `commercial`, `client`, `marketing`, `product`,
`operations`, `hr`, `finance`, `legal`, `other`.

Examples:

```
/hal tasks
/hal tasks --mine
/hal tasks ic --status in_progress
/hal tasks --project BG-2025-12
/hal tasks --tag commercial
/hal tasks --tag commercial --mine
```

## /hal update

Update BG-CRM in Supabase from a natural-language instruction. The skill activates on explicit
triggers (`/hal update`, "mets à jour", "propale envoyée", "perdu", "call avec", "nouveau client"…)
and calls the **hal-mcp** tools directly — no script, no vault write.

Examples:

```
/hal update propale envoyée IC Ingénieurs
/hal update call avec Laurent : a validé le devis
/hal update Valorem — perdu, sans suite
/hal update nouveau client Natural Power
```

Claude resolves the target entity via `list_projects` / `list_contacts` / `list_companies` (fuzzy
match on names, threshold 80/50), confirms if ambiguous, then writes to Supabase.

Dry-run mode: ask "what would `/hal update …` do?" — Claude prints the planned MCP calls without
executing them.

## Manual usage (without Claude)

The hal-mcp pull/push tools are only reachable through Claude Code. The standalone scripts kept
here are:

- `scripts/download_photos.py <context.json> <output_dir>` — download photos from signed URLs
  already present in `context.json`
- `scripts/render_report.py mission/context.json --photos-dir mission/photos --output mission/rapport.docx`
  — generate the DOCX from `context.json`

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `uv: command not found` | Install uv (see Prerequisites above) |
| "This laptop is not paired" | Run `/edifice pair` in Claude Cowork |
| Auth token refresh fails | Delete `~/.hal/config.json` and re-pair |
| Template not found | Check `project_type` in `context.json` matches a `.docx` file in `templates/ic-ingenieurs/` |
| `/hal update` can't find a mission | Check that hal-mcp is connected — `/plugin` → Connectors tab |
