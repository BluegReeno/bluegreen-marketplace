# HAL CRM — Plugin Specification

**Plugin ID:** `hal-crm`
**Marketplace:** `BluegReeno/bluegreen-marketplace`
**Author:** Renaud Laborbe — renaud@bluegreen.ai
**Status:** Spec v1.1 — to be implemented

---

## Problem Statement

Claude Cowork starts each session with no memory. The Obsidian vault is the only persistent source of truth. But one failure mode degrades data quality repeatedly:

**In-session drift** — information given conversationally ("Thales: no contact, applied via platform") is never written to the vault. The next morning briefing surfaces it again as a stale action item, wastes time, and erodes trust in the system.

**Root cause:** there is no frictionless way to turn a conversational update into a vault write mid-session.

**HAL solves this** with a single explicit skill — `hal-update` — that translates natural language into vault writes instantly.

### What was considered and dropped

**`hal-close` (session close ritual) — dropped from v0.1.**
In practice, sessions end abruptly — Renaud closes the laptop, he doesn't type `/close`. A closing ritual that depends on explicit user action will never run. The morning briefing already reads the daily log and vault as its opening act, creating natural continuity. `hal-update` called throughout the day is sufficient. A `/close` command may be revisited as an optional convenience in v0.2, not as core flow.

---

## Architecture — How hal-crm fits in the stack

```
┌─────────────────────────────────────────────────┐
│         morning-briefing  (anthropic-skills)     │  ← presentation layer
│         Reads vault + calendars, proposes plan   │
└─────────────────────┬───────────────────────────┘
                      │ reads
┌─────────────────────▼───────────────────────────┐
│              hal-crm  (bluegreen-marketplace)    │  ← intent layer
│         /update: NL → vault writes               │
└─────────────────────┬───────────────────────────┘
                      │ calls scripts
┌─────────────────────▼───────────────────────────┐
│           obsidian-crm  (anthropic-skills)       │  ← data layer
│    read_note / search_vault / update_frontmatter │
└─────────────────────┬───────────────────────────┘
                      │ reads/writes
┌─────────────────────▼───────────────────────────┐
│         Obsidian vault  (filesystem)             │  ← single source of truth
│    SynologyDrive-MyAssistant/SecondLife-vault/   │
└─────────────────────────────────────────────────┘
```

**hal-crm does NOT reimplement the data layer.** It locates the `obsidian-crm` scripts at runtime and calls them. No script duplication.

---

## Script Resolution — Finding obsidian-crm at Runtime

`obsidian-crm` scripts live in the `anthropic-skills` plugin cache. hal-crm resolves their path dynamically using the same pattern as `edifice-mission-report`'s `PLUGIN_DIR` resolution:

```python
def resolve_obsidian_crm_scripts() -> Path:
    """
    Resolution order:
    1. Env var OBSIDIAN_CRM_SCRIPTS (explicit override)
    2. Cowork sandbox: /sessions/*/mnt/.claude/skills/obsidian-crm/scripts/
    3. Claude Code cache: ~/.claude/plugins/cache/*/obsidian-crm/*/scripts/
    4. Raise RuntimeError with clear message if not found
    """
```

---

## Vault Context

```
SynologyDrive-MyAssistant/SecondLife-vault/SecondLife/   ← OBSIDIAN_VAULT_PATH
├── CRM-JobSearch/
│   ├── Opportunites/       type: opportunite-js
│   ├── Entreprises/        type: entreprise-js
│   ├── Contacts/           type: contact-js
│   └── Entretiens/         type: entretien
├── CRM-BlueGreen/
│   ├── Opportunites/       type: opportunite-bg
│   ├── Entreprises/        type: entreprise-bg
│   ├── Contacts/           type: contact-bg
│   └── Interactions/       type: interaction-bg
├── Taches/                 type: tache
├── Projets/                type: projet
└── Sprints/                type: sprint
```

**Env var:** `OBSIDIAN_VAULT_PATH` — always set before running any script.
Cowork path pattern: `/sessions/*/mnt/SynologyDrive-MyAssistant/SecondLife-vault/SecondLife`

**obsidian-crm scripts interface** (called by hal-crm, not bundled):
- `search_vault.py <query>` → fuzzy text search
- `search_vault.py --dql '<DQL>'` → Dataview query
- `read_note.py <path>` → JSON with frontmatter + content
- `update_frontmatter.py <path> <field> <value>` → update single field
- `create_note.py <path> <content>` → create new note

---

## Skill — `hal-update`

### Triggers

User says anything like:
- `/update Thales — pas de contact, candidature plateforme, supprimer date de relance`
- `/update ILLUIN — RDV RH Sara Azhari le 2 juin 13h30`
- `/update MuseIA — mail de confirmation envoyé, c'est elle qui démo`
- `note que` / `mets à jour` / `marque comme fait` / `relance le` / `RDV prévu`
- Any explicit vault write instruction mid-conversation

Also trigger **automatically** when the user says "done", "fait", "c'est bon", "next" after completing a task — identify what was completed and propose the corresponding vault write.

### Behavior

```
1. PARSE   — extract entities, intents, and values from free-text input
2. RESOLVE — find matching vault note(s) via obsidian-crm search_vault.py
3. PLAN    — build list of VaultWrite operations
4. CONFIRM — show planned writes (unless input is unambiguous and single-write)
5. WRITE   — call update_frontmatter.py for each operation
6. REPORT  — one line per change: "✅ [Note name] → [field]: [new value]"
```

### Entity Resolution

- Fuzzy match on note title (`difflib` stdlib or `rapidfuzz` via uv)
- If ambiguous → show candidates, ask user to pick
- Folder hint from context: "candidature" / "opportunité" → `CRM-JobSearch`, "client" / "propale" → `CRM-BlueGreen`, "tâche" → `Taches`
- Default: search all folders, rank by relevance

### Field Mapping — Natural Language → Frontmatter

| User says | Field(s) updated |
|-----------|-----------------|
| "pas de contact", "candidature plateforme" | `notes` (append) + `date_relance` (clear) |
| "RDV le [date]", "entretien prévu [date]" | `prochain_rdv` + `statut` → `📞 Entretien prévu` |
| "relance le [date]" | `date_relance` |
| "refus", "dead", "pas retenu" | `statut` → `❌ Refus` |
| "offre reçue" | `statut` → `✅ Offre reçue` |
| "relance à faire", "en attente retour" | `statut` → `🔄 Relance à faire` |
| "terminé", "fait", "done" (task) | `etat` → `Terminé` |
| "en cours" (task) | `etat` → `En cours` |
| "note: [text]" | `notes` (overwrite) |
| "ajouter note: [text]" | `notes` (append + timestamp) |
| "supprimer date relance" | `date_relance` → clear |

### Exact Vocabulary (write these strings verbatim)

**JS opportunity `statut`:**
```
📝 À postuler | ✉️ Candidature envoyée | 📞 Entretien prévu |
🔄 Relance à faire | ❌ Refus | ✅ Offre reçue | ⏸️ En pause
```

**Task `etat`:**
```
Pas commencée | En cours | Terminé | Archivé
```

### SKILL.md frontmatter

```yaml
---
name: hal-update
description: >
  Update the Obsidian SecondLife vault from a natural-language instruction.
  Use when the user says /update, "note that", "mets à jour", "marque comme fait",
  "relance le", "RDV prévu", "pas de contact", or any explicit vault write instruction.
  Also trigger automatically when user says "done", "fait", "c'est bon", "next"
  after completing a task — propose the corresponding vault write.
version: 0.1.0
allowed-tools: "Bash(uv *) Bash(python3 *) Bash(find *) Bash(ls *) Read Write"
---
```

---

## Plugin Structure

```
plugins/hal-crm/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── hal-update/
│       └── SKILL.md
├── scripts/
│   └── hal_update.py          # NL parser + write orchestrator (calls obsidian-crm)
├── requirements.txt           # human-readable manifest only, never executed at runtime
├── README.md
└── CHANGELOG.md
```

---

## `hal_update.py` — Core Logic Spec

```python
# Entry point: called by the skill with the raw user text
# Dependencies: obsidian-crm scripts (resolved at runtime, not bundled)

class VaultWrite:
    note_path: str       # relative path in vault (e.g. "CRM-JobSearch/Opportunites/Thales.md")
    field: str           # frontmatter key
    value: str | None    # new value — None means clear the field
    mode: str            # "set" | "append" | "clear"

def resolve_scripts_path() -> Path:
    """Locate obsidian-crm scripts. See Script Resolution section above."""

def resolve_vault_path() -> Path:
    """OBSIDIAN_VAULT_PATH env var → Cowork glob → error."""

def parse_updates(text: str) -> list[VaultWrite]:
    """
    Extract from free text:
    - Entity names (opportunity, task, company names)
    - Intent verbs (update, clear, mark done, set date, add note...)
    - Values (dates in various formats, status strings, free text)
    Return list of VaultWrite candidates.
    """

def resolve_note(entity: str, scripts: Path, vault: Path, folder_hint: str = None) -> str | list[str]:
    """
    Call search_vault.py with entity name.
    Return single path if unambiguous, list of candidates if multiple matches.
    Rank by folder relevance when folder_hint is provided.
    """

def execute_writes(writes: list[VaultWrite], scripts: Path) -> list[str]:
    """
    Call update_frontmatter.py for each VaultWrite.
    Return confirmation lines.
    """

def main(user_text: str, force: bool = False) -> None:
    """
    Full pipeline: parse → resolve → (confirm if not force) → write → report.
    """
```

---

## Technical Constraints

Non-negotiable (from marketplace `CLAUDE.md`):

- **No `pip install`** at runtime — ever
- **`uv run --with <pkg>`** is the only allowed runtime package manager
- **stdlib first** — `pathlib`, `json`, `re`, `datetime`, `difflib` cover most needs
- `rapidfuzz` via `uv run --with rapidfuzz` if stdlib fuzzy matching is insufficient
- Scripts resolve `OBSIDIAN_VAULT_PATH` via env var, then error clearly if missing
- `requirements.txt` is human-readable only — never executed

---

## Out of Scope (v0.1)

- `hal-close` — dropped (see Problem Statement). Revisit in v0.2 as optional convenience.
- `hal-query` (NL vault search) — deferred to v0.2
- Automatic hook-based writes (no user action required) — deferred
- Migration to Postgres — tracked separately in hal repo
- Multi-user support

---

## Open Questions for Claude Code

1. **Fuzzy matching** — `difflib.SequenceMatcher` (stdlib, zero deps) vs `rapidfuzz` (uv, much better quality). Recommend `rapidfuzz` via `uv run --with rapidfuzz` — the cold start cost is negligible for a single package.

2. **Confirm step** — Default: always show planned writes and ask confirmation before executing. Skip confirmation only when `--force` flag is passed (intended for scripted use by morning-briefing reconciliation). This protects against misresolution on ambiguous entity names.

3. **Multi-write detection** — When user says "Thales — pas de contact" and there are two Thales notes, after confirming the first, proactively ask: "Apply same update to `Thales — Program Manager IT`?" instead of making the user run `/update` twice.

4. **Append vs overwrite for `notes`** — "note: [text]" overwrites, "ajouter note: [text]" appends with ISO timestamp prefix. Make this explicit in the SKILL.md so Claude applies it consistently.

---

## Example Interactions

**Single unambiguous write:**
```
User: /update MuseIA — mail confirmé, c'est Cécile qui fait la démo, prep 30 min

HAL: ✅ MuseIA — Prep + RDV présentiel 29-05-2026
       etat        : Pas commencée → En cours
       notes       : "Mail confirmation envoyé. C'est Cécile qui démo. Prep = 30 min."
```

**Ambiguous entity → confirm + propagate:**
```
User: /update Thales — pas de contact, candidature plateforme, supprimer date relance

HAL: Found 2 notes:
  1. Thales — Chef de Projet R&D.md
  2. Thales — Program Manager IT.md
  Apply to both? (yes / 1 / 2)

User: yes

HAL: ✅ Thales — Chef de Projet R&D      → notes updated, date_relance cleared
     ✅ Thales — Program Manager IT       → notes updated, date_relance cleared
```

**Mid-conversation "done" trigger:**
```
[Renaud has just sent a follow-up email to BPI]

User: c'est envoyé

HAL: BPI — on marque la tâche comme terminée ?
  ✏️ BPI — Envoyer dossier solde 9K€ → etat: Terminé
  Confirm? (yes/no)
```
