# BlueGreen Marketplace

Public distribution registry for [Blue Green AI](https://bluegreen.ai) Claude Code plugins.

## Install the marketplace

In Claude Code or Cowork (one-time):

```
/plugin marketplace add BluegReeno/bluegreen-marketplace
```

## Available plugins

### `hal` — Second brain and mission workflow

Two skills in one plugin:

- **`/edifice`** — Pull a building inspection mission from Supabase, qualify with AI, generate the DOCX report
- **`/hal list`** — Show the BlueGreen CRM pipeline as a text kanban grouped by stage
- **`/hal tasks`** — Show tasks as a text kanban grouped by status (filters: `--mine`, `--project`, `--status`)
- **`/hal update`** — Update BG-CRM in Supabase (projects, contacts, interactions, tasks, sprints) from a natural-language instruction
- **`/hal devis`** — Generate a DOCX devis (IC Ingénieurs Conseils or Blue Green)

**Install:**
```
/plugin install hal@bluegreen-marketplace
```

**Requires**: [`uv`](https://docs.astral.sh/uv/) (`brew install uv` on Mac) and a paired Edifice account (for `/edifice`). `/hal list`, `/hal tasks`, and `/hal update` require only the **hal-mcp** connector (included in the plugin, authenticated via OAuth); `/hal devis` runs locally with no MCP.

The connector targets **hal-mcp v38** (frozen tool surface) on Supabase `zgkvbjqlvebttbnkklpo`.

See [`plugins/hal/README.md`](plugins/hal/README.md) for full setup instructions.

---

## Connecting from Claude, Gemini, or OpenAI

The `hal-mcp` **connector** (the MCP server) works on all three providers; the `/edifice` and
`/hal` **skills** only run on the agent/CLI surfaces (Claude Code, Gemini CLI, OpenAI Codex).

| Provider | One-line path |
|----------|---------------|
| **Claude Code** (full skills + connector) | `/plugin install hal@bluegreen-marketplace` |
| **Claude Desktop / claude.ai** | Settings → Connectors → Add custom connector → paste the URL (OAuth, automatic) |
| **Gemini Enterprise** | Data stores → Custom MCP Server → paste URL + **manual** OAuth endpoints (see guide) |
| **ChatGPT** | Settings → Apps & Connectors → Developer mode → Add connector → OAuth |

MCP server URL: `https://zgkvbjqlvebttbnkklpo.supabase.co/functions/v1/hal-mcp`

**Full step-by-step for every provider** — including the Gemini OAuth gotchas —
is in [`docs/connectors-and-skills.md`](docs/connectors-and-skills.md).

---

## Enable auto-updates

`/plugin` → Marketplaces tab → `bluegreen-marketplace` → enable auto-update.

---

## For developers

Plugin code lives directly in this repo. Each plugin is self-contained under `plugins/<name>/`.

| Plugin | Skills | Status |
|--------|--------|--------|
| `hal` | `edifice`, `hal` | v0.7.0 — active |

```
plugins/hal/
├── .claude-plugin/plugin.json
├── .mcp.json                    # hal-mcp HTTP server (OAuth)
├── skills/
│   ├── edifice/SKILL.md         # /edifice — building inspection reports
│   └── hal/SKILL.md             # /hal update — Supabase CRM writes via hal-mcp
├── scripts/
│   ├── *.py                     # edifice: build_context, render_*, download_photos
│   └── obsidian/                # bundled obsidian-crm scripts (source of truth)
├── templates/                   # DOCX report templates
└── organizations/               # client config
```

See `docs/brief.md` for the full architecture rationale.
