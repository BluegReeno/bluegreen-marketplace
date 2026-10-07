> **bluegreen-marketplace** is the Claude Code plugin distribution layer for [hal](https://github.com/BluegReeno/hal) — the AI foundation a small firm runs on: its pipeline, its work, its memory, its documents. Install a plugin to wire that foundation into your Claude client.

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
| **`pm`** | `/pm`, `/sprint-planner` | Project management: tasks, sprints, projects, docs (`list`, `tasks`, `new`, `task`, `log`, `doc`, `sprint`, `update`), plus the weekly ritual that closes the sprint and plans the next |
| **`gtm`** | `/crm`, `/linkedin` | Commercial pipeline — opportunities, contacts, BANT qualification, interaction log — and the LinkedIn editorial pipeline (idea, backlog, trend, draft, publish log) |

### Pick your install

| You are | Install | Why |
|---------|---------|-----|
| Running projects and sprints | `hal` + `pm` | Tasks and sprints only — none of the Blue Green commercial surface |
| Blue Green, end to end | `hal` + `pm` + `gtm` | Everything |

```
/plugin install pm@bluegreen-marketplace
/plugin install gtm@bluegreen-marketplace
```

**Requires**: nothing beyond the **hal-mcp** connector that `hal` brings (authenticated via OAuth); `/linkedin trend` also uses the Bright Data connector.

The connector targets **hal-mcp 0.3.0** on Supabase `zgkvbjqlvebttbnkklpo` (the version in
`plugins/hal/.mcp.json`). Powered by [hal](https://github.com/BluegReeno/hal).

**Task and project tags come from the workspace, not from this page.** Each workspace declares
its own `allowed_tags`, and `whoami` is the only carrier — a value legal in one workspace is
rejected in the next, and the list changes without a deploy. For `blue-green` it is currently
`commercial`, `client`, `marketing`, `product`, `operations`, `hr`, `finance`, `legal`, `memory`,
`other`; do not hardcode that anywhere, call `whoami`.

See [`plugins/hal/README.md`](plugins/hal/README.md) for full setup instructions.

> **Coming from `hal` 0.11.x?** That version bundled all four skill families. Updating to 0.12.0
> removes `/edifice`, `/pm`, `/crm` and `/linkedin` from it — install the plugin that owns the
> command you need and it comes straight back. Nothing else changed: same server, same tools.
> `/edifice` is the exception since 2026-10-07: that plugin is archived (git tag
> `archive/edifice-plugin`) — hal-mcp no longer serves its tools.

---

## Connecting from Claude, Gemini, or OpenAI

The `hal-mcp` **connector** (the MCP server) works on all three providers; the `/pm`, `/crm`, and `/linkedin` **skills** only run on the agent/CLI surfaces (Claude Code, Gemini CLI, OpenAI Codex).

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

**Versions are deliberately absent from this table.** They go stale the day a plugin is released,
and this one was wrong on two of four until 2026-09-08. `.claude-plugin/marketplace.json` is the
only version table; read it there.

| Plugin | Skills | Serves |
|--------|--------|--------|
| `hal` | — (connector only) | the foundation — every other plugin calls through it |
| `pm` | `pm`, `sprint-planner` | tasks, sprints, projects, documents |
| `gtm` | `crm`, `linkedin` | pipeline, contacts, logged exchanges |

```
plugins/
├── hal/                         # the connector — no skill, no command
│   ├── .claude-plugin/plugin.json
│   └── .mcp.json                # hal-mcp HTTP server (OAuth) — the only one in the repo
├── pm/
│   └── skills/                  # pm, sprint-planner
└── gtm/
    └── skills/                  # crm, linkedin
```

The two skill plugins declare no `.mcp.json` — they call `hal-mcp` through `hal`, which is why
it is a required install for all of them.

See `docs/brief.md` for the full architecture rationale.
