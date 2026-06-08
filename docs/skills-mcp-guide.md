# Skills & MCP — Best Practices

Reference guide for maintaining and extending the `hal` plugin. Covers the
skill vs command architecture, MCP detection, and cross-platform compatibility.

---

## 1. `/skill-name` vs `plugin:skill` — why `/hal` failed

Claude Code has two separate invocation systems:

| System | Location | Invocation |
|--------|----------|-----------|
| **Skills** | `skills/<name>/SKILL.md` | Semantic trigger (description match) OR `plugin:skill` menu |
| **Commands** | `commands/<name>.md` | Explicit `/command-name` slash syntax |

Skills are always namespaced: a skill `hal` in plugin `hal` → `hal:hal` in the menu.
Typing `/hal` raw looks for a **command** named `hal`, not a skill. Without `commands/hal.md`,
Claude Code returns "compétence inconnue".

**Fix**: `commands/hal.md` and `commands/edifice.md` register `/hal` and `/edifice` as
first-class slash commands (auto-discovered from the `commands/` directory, no manifest entry needed).

### Command file format

```markdown
---
description: Short description (shown in /help and autocomplete)
argument-hint: "subcommand [args]"
allowed-tools: "Bash(uv *) Read Write Edit Glob"
---

Body — $ARGUMENTS contains everything typed after /command-name.
```

Field reference:
- `description` — single line, shown in `/help` list
- `argument-hint` — autocomplete hint for the argument field
- `allowed-tools` — pre-approved tools (same syntax as SKILL.md)
- `model` — optional model override (`haiku`, `sonnet`, `opus`)
- `disable-model-invocation` — set `true` to suppress LLM call (for pure Bash commands)

### Design rule: commands must be self-contained

Command files are invoked BEFORE the associated skill body is loaded into context.
Do NOT rely on the skill being pre-loaded. Either:
1. Include the essential routing logic inline (current approach — preferred)
2. Open with `Read skills/<name>/SKILL.md` to load instructions explicitly

---

## 2. MCP connection detection

### Pattern

Add a pre-flight check at the top of every skill section and command body that
requires MCP tools.

```
1. Call list_stages (hal skill) or list_edifice_missions (edifice skill) with workspace_slug: "blue-green"
2. Success → proceed normally
3. Failure (tool not found / connection refused / timeout) → show reconnection message, stop
```

### Reconnection message (exact wording — do not vary)

```
❌ hal-mcp non connecté.
Reconnexion : Claude Desktop → Paramètres → Connexions → hal-mcp → Activer
⚠️ Ne pas lancer de commandes terminal — interface graphique uniquement.
```

**Critical**: the fix is ALWAYS via Claude Desktop GUI. Never suggest `npx`, `node`, or any
terminal command to reconnect. The MCP server is managed by the Claude Desktop application,
not by the user's shell.

### Which commands need the check

| Command | MCP needed | Check tool |
|---------|-----------|-----------|
| `/hal list` | ✅ | `list_stages` |
| `/hal update` | ✅ | `list_stages` |
| `/hal devis` | ❌ (script only) | skip |
| `/edifice list` | ✅ | `list_edifice_missions` |
| `/edifice pull` | ✅ | `list_edifice_missions` |
| `/edifice improve` | ❌ (local files) | skip |
| `/edifice report` | ❌ (local files) | skip |
| `/edifice push` | ✅ | `list_edifice_missions` |

---

## 3. Cross-platform compatibility (agentskills.io)

The [open standard](https://agentskills.io/specification) defines a cross-client format
for skills. Our SKILL.md files already comply:

| Field | Spec | Our SKILL.md |
|-------|------|-------------|
| `name` | required — matches directory name | ✅ `hal` / `edifice` |
| `description` | required | ✅ present |
| `allowed-tools` | optional, experimental | ✅ used |
| `version` | not in spec (use `metadata.version`) | custom — accepted by Claude Code |

### Cross-client discovery paths

| Client | Discovery path |
|--------|---------------|
| Claude Code | `~/.claude/skills/`, plugin `skills/` directories |
| Cross-client (spec) | `.agents/skills/<name>/SKILL.md` in project root |
| VS Code Copilot | `.agents/skills/` |
| OpenAI Codex | `.agents/skills/` |
| Dust, OpenClaw, others | `.agents/skills/` |

### Enabling cross-platform (future sprint)

Create `.agents/skills/` symlinks at the repo root so Codex, Dust, and other
agentskills.io-compatible clients can discover the skills without the Claude Code
plugin system:

```bash
mkdir -p .agents/skills
ln -sf "$(pwd)/plugins/hal/skills/hal" .agents/skills/hal
ln -sf "$(pwd)/plugins/hal/skills/edifice" .agents/skills/edifice
```

The SKILL.md frontmatter requires no changes — it already complies with the spec.

---

## 4. Versioning — skills vs commands

Commands (`commands/*.md`) are NOT versioned separately. They are part of the plugin
and their changes are covered by the plugin version bump.

Skills (`skills/*/SKILL.md`) are versioned independently via `version:` frontmatter.

| What changed | Bump |
|-------------|------|
| New command file added | Plugin MINOR |
| Command body updated | Plugin PATCH |
| Skill new command/subcommand | Skill MINOR |
| Skill MCP check / guardrail added | Skill PATCH |

See `CLAUDE.md` → Versioning Policy for the full bump table.

---

## 5. Validation

```bash
# Frontmatter compliance (agentskills.io)
npx skills-ref validate ./plugins/hal/skills/hal
npx skills-ref validate ./plugins/hal/skills/edifice

# Version sync
python3 -c "
import json, pathlib
p = json.loads(pathlib.Path('plugins/hal/.claude-plugin/plugin.json').read_text())
m = json.loads(pathlib.Path('.claude-plugin/marketplace.json').read_text())
assert p['version'] == m['plugins'][0]['version']
print(f'Sync OK: {p[\"version\"]}')
"
```

`skills-ref` CLI: `npm install -g skills-ref`
Source: https://github.com/agentskills/agentskills/tree/main/skills-ref
