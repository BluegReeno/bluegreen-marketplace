> **bluegreen-marketplace** is the Claude Code plugin distribution layer for [hal](https://github.com/BluegReeno/hal) — the AI-native company layer for field-work SMEs. Install a plugin to wire CRM, project management, and building-inspection workflows directly into your Claude client.

# BlueGreen Marketplace

Public distribution registry for [Blue Green AI](https://bluegreen.ai) Claude Code plugins.

## Install the marketplace

In Claude Code or Cowork (one-time):

```
/plugin marketplace add BluegReeno/bluegreen-marketplace
```

## Available plugins

**`hal` first, always** — it carries the `hal-mcp` connector every other plugin calls, and ships
no command of its own. Then add what you actually use.

```
/plugin install hal@bluegreen-marketplace
```

| Plugin | Commands | What it does |
|--------|----------|--------------|
| **`edifice`** | `/edifice` | Pull a building inspection mission from Supabase, qualify with AI, generate the DOCX report (`list`, `pull`, `improve`, `report`, `push`) |
| **`pm`** | `/pm`, `/sprint-planner`, `/sprint-review` | Project management: tasks, sprints, projects, docs (`list`, `tasks`, `new`, `task`, `log`, `doc`, `sprint`, `update`), plus weekly planning and review |
| **`gtm`** | `/crm`, `/linkedin` | Commercial pipeline — opportunities, contacts, BANT qualification, interaction log — and the LinkedIn editorial pipeline (idea, backlog, trend, draft, publish log) |

### Pick your install

| You are | Install | Why |
|---------|---------|-----|
| A building inspector (IC Ingénieurs Conseils) | `hal` + `edifice` | Missions and reports only — no CRM, no sprints |
| Running projects and sprints | `hal` + `pm` | Tasks and sprints only — none of the Blue Green commercial surface |
| Blue Green, end to end | `hal` + `edifice` + `pm` + `gtm` | Everything |

```
/plugin install edifice@bluegreen-marketplace
/plugin install pm@bluegreen-marketplace
/plugin install gtm@bluegreen-marketplace
```

**Requires**: [`uv`](https://docs.astral.sh/uv/) (`brew install uv` on Mac) and a paired Edifice account — both for `edifice` only. `pm` and `gtm` need nothing beyond the **hal-mcp** connector that `hal` brings (authenticated via OAuth); `/linkedin trend` also uses the Bright Data connector.

The connector targets **hal-mcp v39** on Supabase `zgkvbjqlvebttbnkklpo`. Powered by [hal](https://github.com/BluegReeno/hal).

**Task and project tags** use a unified vocabulary: `commercial`, `client`, `marketing`, `product`, `operations`, `hr`, `finance`, `legal`, `other`.

See [`plugins/hal/README.md`](plugins/hal/README.md) for full setup instructions.

> **Coming from `hal` 0.11.x?** That version bundled all four skill families. Updating to 0.12.0
> removes `/edifice`, `/pm`, `/crm` and `/linkedin` from it — install the plugin that owns the
> command you need and it comes straight back. Nothing else changed: same server, same tools.

---

## Connecting from Claude, Gemini, or OpenAI

The `hal-mcp` **connector** (the MCP server) works on all three providers; the `/edifice`, `/pm`, `/crm`, and `/linkedin` **skills** only run on the agent/CLI surfaces (Claude Code, Gemini CLI, OpenAI Codex).

| Provider | One-line path |
|----------|---------------|
| **Claude Code** (connector + the skills you install) | `/plugin install hal@bluegreen-marketplace` |
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
| `hal` | — (connector only) | v0.12.0 — active |
| `edifice` | `edifice` | v0.1.0 — active |
| `pm` | `pm`, `sprint-planner`, `sprint-review` | v0.1.0 — active |
| `gtm` | `crm`, `linkedin` | v0.1.0 — active |

```
plugins/
├── hal/                         # the connector — no skill, no command
│   ├── .claude-plugin/plugin.json
│   └── .mcp.json                # hal-mcp HTTP server (OAuth) — the only one in the repo
├── edifice/
│   ├── skills/edifice/SKILL.md  # /edifice — building inspection reports
│   ├── scripts/                 # build_context, render_*, download_photos + obsidian/ bundle
│   ├── templates/               # DOCX report templates
│   ├── organizations/           # client config
│   └── artifacts/               # committed artifact front-ends (built from ui/)
├── pm/
│   └── skills/                  # pm, sprint-planner, sprint-review
└── gtm/
    └── skills/                  # crm, linkedin
```

The three skill plugins declare no `.mcp.json` — they call `hal-mcp` through `hal`, which is why
it is a required install for all of them.

See `docs/brief.md` for the full architecture rationale.
