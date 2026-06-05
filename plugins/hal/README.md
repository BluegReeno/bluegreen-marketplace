# HAL — Claude Plugin

HAL is the second brain and mission workflow for BlueGreen and IC Ingénieurs Conseils.
It ships two skills inside a single plugin:

| Skill | Command | Purpose |
|-------|---------|---------|
| `edifice` | `/edifice pull`, `/edifice improve`, `/edifice report`, `/edifice push` | Pull a building inspection mission from Supabase and render the DOCX report. |
| `hal` | `/hal update` | Update BG-CRM in Supabase (missions, contacts, interactions) from a natural-language instruction via **hal-mcp**. |

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

### 3. Enable auto-update (recommended)

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

Claude resolves the target entity via `list_missions` / `list_contacts` / `list_companies` (fuzzy
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
