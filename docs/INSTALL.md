# Install BlueGreen Marketplace

## One-time setup

In Claude Code or Cowork:

```
/plugin marketplace add BluegReeno/bluegreen-marketplace
```

## Install the connector — required by all the others

```
/plugin install hal@bluegreen-marketplace
```

## Then install what you use

```
/plugin install edifice@bluegreen-marketplace     # building inspections
/plugin install pm@bluegreen-marketplace          # projects and sprints
/plugin install gtm@bluegreen-marketplace         # crm + linkedin
```

## Enable auto-updates

`/plugin` → Marketplaces tab → `bluegreen-marketplace` → enable auto-update.

## Available plugins

| Plugin | Skills | Description |
|--------|--------|-------------|
| `hal` | — | The `hal-mcp` connector every other plugin calls. No command of its own; install it first |
| `edifice` | `/edifice` | Edifice building-inspection missions and DOCX reports |
| `pm` | `/pm`, `/sprint-planner`, `/sprint-review` | Project management — tasks, sprints, projects, docs — via **hal-mcp** |
| `gtm` | `/crm`, `/linkedin` | Commercial pipeline and LinkedIn editorial workflow via **hal-mcp** |
