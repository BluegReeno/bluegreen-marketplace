# Skills & MCP — Best Practices

Reference guide for maintaining and extending the plugins of this repo. Covers the
skill vs command architecture, MCP detection, and cross-platform compatibility.

---

## 1. `/skill-name` vs `plugin:skill` — why `/hal` failed

Claude Code has two separate invocation systems:

| System | Location | Invocation |
|--------|----------|-----------|
| **Skills** | `skills/<name>/SKILL.md` | Semantic trigger (description match) OR `plugin:skill` menu |
| **Commands** | `commands/<name>.md` | Explicit `/command-name` slash syntax |

Skills are always namespaced by their plugin: the skill `pm` in plugin `pm` → `pm:pm` in the menu.
Typing `/pm` raw looks for a **command** named `pm`, not a skill. Without `commands/pm.md`,
Claude Code returns "compétence inconnue".

**Fix**: each plugin ships a `commands/<name>.md` per skill (auto-discovered from the `commands/`
directory, no manifest entry needed) — that is what registers `/pm`, `/edifice`, `/crm`, `/linkedin`,
`/sprint-planner` and `/sprint-review` as first-class slash commands.

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
1. Call whoami (pm / crm skills — no args) or list_edifice_missions (edifice skill) with workspace_slug: "blue-green"
2. Success → proceed normally. For the pm / crm skills, cache the whoami payload
   (default_workspace_slug, workspaces, user_email) for the current command.
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
| `/pm …` | ✅ | `whoami` |
| `/crm …` | ✅ | `whoami` |
| `/linkedin …` | ✅ | `whoami` |
| `/sprint-planner`, `/sprint-review` | ✅ | `whoami` |
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
| `name` | required — matches directory name | ✅ `edifice` / `pm` / `crm` … |
| `description` | required | ✅ present |
| `allowed-tools` | optional, experimental | ✅ used |
| `version` | not in spec (use `metadata.version`) | **not used** — skills carry no version, see §4 |

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
ln -sf "$(pwd)/plugins/edifice/skills/edifice" .agents/skills/edifice
ln -sf "$(pwd)/plugins/pm/skills/pm" .agents/skills/pm
```

The SKILL.md frontmatter requires no changes — it already complies with the spec.

---

## 4. Versioning — skills vs commands

Commands (`commands/*.md`) are NOT versioned separately. They are part of the plugin
and their changes are covered by the plugin version bump.

Skills (`skills/*/SKILL.md`) are **not** versioned either — the `version:` frontmatter field was
dropped from the convention. The plugin version is the only one that moves.

| What changed | Bump |
|-------------|------|
| New command file added | Plugin MINOR |
| Command body updated | Plugin PATCH |
| Skill new command/subcommand | Plugin MINOR |
| Skill MCP check / guardrail added | Plugin PATCH |

See `CLAUDE.md` → Versioning Policy for the full bump table.

---

## 5. Validation

```bash
# Frontmatter compliance (agentskills.io)
npx skills-ref validate ./plugins/edifice/skills/edifice
npx skills-ref validate ./plugins/pm/skills/pm

# Version sync — every plugin at once, same check CI runs
bash scripts/check_version_sync.sh
```

`skills-ref` CLI: `npm install -g skills-ref`
Source: https://github.com/agentskills/agentskills/tree/main/skills-ref
