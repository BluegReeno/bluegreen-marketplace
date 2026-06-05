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
- **`/hal update`** — Update BG-CRM in Supabase (missions, contacts, interactions) from a natural-language instruction

**Install:**
```
/plugin install hal@bluegreen-marketplace
```

**Requires**: [`uv`](https://docs.astral.sh/uv/) (`brew install uv` on Mac) and a paired Edifice account (for `/edifice`). `/hal update` requires only the **hal-mcp** connector (included in the plugin).

See [`plugins/hal/README.md`](plugins/hal/README.md) for full setup instructions.

---

### `hal-crm` *(coming soon)*

Interact with client projects, quotes, and tasks via natural language — backed by Supabase CRM.

---

## Enable auto-updates

`/plugin` → Marketplaces tab → `bluegreen-marketplace` → enable auto-update.

---

## For developers

Plugin code lives directly in this repo. Each plugin is self-contained under `plugins/<name>/`.

| Plugin | Skills | Status |
|--------|--------|--------|
| `hal` | `edifice`, `hal` | v0.2.0 — active |
| `hal-crm` | — | Coming soon |

```
plugins/hal/
├── .claude-plugin/plugin.json
├── .mcp.json                    # hal-mcp SSE server
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
