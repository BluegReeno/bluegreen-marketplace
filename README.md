> **bluegreen-marketplace** is the Claude Code plugin distribution layer for [hal](https://github.com/BluegReeno/hal) — the AI-native company layer for field-work SMEs. Install a plugin to wire CRM, project management, and building-inspection workflows directly into your Claude client.

# BlueGreen Marketplace

Public distribution registry for [Blue Green AI](https://bluegreen.ai) Claude Code plugins.

## Install the marketplace

In Claude Code or Cowork (one-time):

```
/plugin marketplace add BluegReeno/bluegreen-marketplace
```

## Available plugins

### `hal` — Second brain and mission workflow

Four skills in one plugin:

- **`/edifice`** — Pull a building inspection mission from Supabase, qualify with AI, generate the DOCX report
- **`/pm`** — Project management: tasks, sprints, projects via hal-mcp (`list`, `tasks`, `new`, `task`, `log`, `doc`, `sprint`, `update`)
- **`/crm`** — Commercial pipeline: opportunities, contacts, BANT qualification, interaction log (`list`, `new`, `qualify`, `log`, `update`, `contact`, `doc`)
- **`/linkedin`** — LinkedIn editorial pipeline: idea capture, backlog, trend research, draft, publish log (`idea`, `backlog`, `trend`, `draft`, `log`)

**Install:**
```
/plugin install hal@bluegreen-marketplace
```

**Requires**: [`uv`](https://docs.astral.sh/uv/) (`brew install uv` on Mac) and a paired Edifice account (for `/edifice`). `/pm`, `/crm`, and `/linkedin` require only the **hal-mcp** connector (included in the plugin, authenticated via OAuth); `/linkedin trend` also uses the Bright Data connector.

The connector targets **hal-mcp v39** on Supabase `zgkvbjqlvebttbnkklpo`. Powered by [hal](https://github.com/BluegReeno/hal).

**Task and project tags** use a unified vocabulary: `commercial`, `client`, `marketing`, `product`, `operations`, `hr`, `finance`, `legal`, `other`.

See [`plugins/hal/README.md`](plugins/hal/README.md) for full setup instructions.

---

## Connecting from Claude, Gemini, or OpenAI

The `hal-mcp` **connector** (the MCP server) works on all three providers; the `/edifice`, `/pm`, `/crm`, and `/linkedin` **skills** only run on the agent/CLI surfaces (Claude Code, Gemini CLI, OpenAI Codex).

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
| `hal` | `edifice`, `pm`, `crm`, `linkedin` | v0.10.0 — active |

```
plugins/hal/
├── .claude-plugin/plugin.json
├── .mcp.json                    # hal-mcp HTTP server (OAuth)
├── skills/
│   ├── edifice/SKILL.md         # /edifice — building inspection reports
│   ├── pm/SKILL.md              # /pm — project management via hal-mcp
│   ├── crm/SKILL.md             # /crm — commercial pipeline via hal-mcp
│   └── linkedin/SKILL.md        # /linkedin — editorial content pipeline
├── scripts/
│   ├── *.py                     # edifice: build_context, render_*, download_photos
│   └── obsidian/                # bundled obsidian-crm scripts (source of truth)
├── templates/                   # DOCX report templates
└── organizations/               # client config
```

See `docs/brief.md` for the full architecture rationale.
