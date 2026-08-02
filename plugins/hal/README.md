# HAL — the BlueGreen connector plugin

`hal` carries **one thing**: the `hal-mcp` connector that every other BlueGreen plugin calls.
It ships no skill and no command of its own — it is the mandatory base you install first.

Since **0.12.0** the skills that used to live here have moved into three installable plugins.
Install `hal` plus whichever of them matches your work:

| Plugin | Commands | For whom |
|--------|----------|----------|
| `edifice` | `/edifice list \| pull \| improve \| report \| push` | IC Ingénieurs Conseils — building inspection missions |
| `pm` | `/pm`, `/sprint-planner`, `/sprint-review` | anyone running projects, tasks and sprints |
| `gtm` | `/crm`, `/linkedin` | Blue Green go-to-market — commercial pipeline and editorial content |

Each of them requires `hal`: without it, the `hal-mcp` tools they call are not registered.

## Install

```
/plugin marketplace add BluegReeno/bluegreen-marketplace
/plugin install hal@bluegreen-marketplace
```

Then add the plugin(s) you need:

```
/plugin install edifice@bluegreen-marketplace     # IC Ingénieurs
/plugin install pm@bluegreen-marketplace          # projects and sprints
/plugin install gtm@bluegreen-marketplace         # crm + linkedin
```

### Upgrading from 0.11.x

Updating `hal` to 0.12.0 removes `/edifice`, `/pm`, `/crm` and `/linkedin` from it. They come
back as soon as you install the corresponding plugin above — nothing else changes: same MCP
server, same workspace resolution, same tool names.

### Enable auto-update (recommended)

`/plugin` → Marketplaces tab → select `bluegreen-marketplace` → enable auto-update.

## Workspace access (no client-side config)

HAL resolves your default workspace server-side from your Supabase membership — zero environment
variables, zero shell config.

Ask your BlueGreen administrator to:

1. Add your email to the workspace(s) you should access (`workspace_members` table).
2. If you belong to several workspaces, flag your default one (`is_default = true`).

Once you are a member, every command resolves to your default workspace automatically (via the
`whoami` MCP tool). Commands that accept a workspace argument let you override it per call.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| A command is not found | Check the plugin that owns it is installed (`/plugin`) |
| Tools are refused or missing | Check `hal-mcp` is connected — `/plugin` → Connectors tab |
| "no workspace for this user" | Your email is not in `workspace_members` — ask your administrator |
| Update not offered | Enable auto-update, or re-add the marketplace to refresh its manifest |
