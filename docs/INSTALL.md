# Install BlueGreen Marketplace

## One-time setup

In Claude Code or Cowork:

```
/plugin marketplace add BluegReeno/bluegreen-marketplace
```

## Install a plugin

```
/plugin install hal@bluegreen-marketplace
```

## Enable auto-updates

`/plugin` → Marketplaces tab → `bluegreen-marketplace` → enable auto-update.

## Available plugins

| Plugin | Skills | Description |
|--------|--------|-------------|
| `hal` | `/edifice`, `/hal list`, `/hal tasks`, `/hal update`, `/hal devis` | Edifice building inspection reports + BlueGreen CRM (Supabase) queries, writes, and devis generation via **hal-mcp** |
| `hal-crm` *(placeholder — superseded by `/hal`)* | — | Reserved namespace; CRM features now ship inside `hal` (`/hal list`, `/hal tasks`, `/hal update`). |
