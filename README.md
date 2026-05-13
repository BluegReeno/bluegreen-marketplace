# BlueGreen Marketplace

Public distribution registry for [Blue Green AI](https://bluegreen.ai) Claude Code plugins.

## Install the marketplace

In Claude Code or Cowork (one-time):

```
/plugin marketplace add BluegReeno/bluegreen-marketplace
```

## Available plugins

### `edifice-mission-report` — Building inspection reports

Pull an Edifice mission from Supabase, qualify observations with AI, and generate the DOCX diagnostic report — directly from Claude Cowork or Claude Code.

**Install:**
```
/plugin install edifice-mission-report@bluegreen-marketplace
```

**Requires**: [`uv`](https://docs.astral.sh/uv/) (`brew install uv` on Mac) and a paired Edifice account.

See [`plugins/edifice-mission-report/README.md`](plugins/edifice-mission-report/README.md) for full setup instructions.

---

### `hal-crm` *(coming soon)*

Interact with client projects, quotes, and tasks via natural language.

---

## Enable auto-updates

`/plugin` → Marketplaces tab → `bluegreen-marketplace` → enable auto-update.

---

## For developers

Plugin code lives directly in this repo. Each plugin is self-contained under `plugins/<name>/`.

| Plugin | Status |
|--------|--------|
| `edifice-mission-report` | Active |
| `hal-crm` | Coming soon |

See `docs/brief.md` for the full architecture rationale.
