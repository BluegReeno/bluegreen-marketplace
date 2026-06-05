---
name: hal
description: >
  Update the BlueGreen CRM (Supabase) from a natural-language instruction
  via the hal-mcp connector. Use when the user says /hal update,
  "propale envoyée", "stage", "perdu", "gagné", "signé", "refus",
  "call avec", "RDV fait", "mail envoyé", "nouveau client",
  "nouveau contact", "nouvelle mission/propale", "pipeline",
  "où en est", "deals en cours", or any explicit CRM write/read
  instruction mid-conversation. Also trigger when the user says
  "done", "fait", "c'est bon", "next" after completing a task —
  propose the corresponding CRM write.
version: 0.2.0
---

# HAL — BlueGreen CRM updates via hal-mcp (Claude Code)

This skill routes natural-language CRM updates to the `hal-mcp` MCP connector
(Supabase backend). Zero scripts, zero Bash — pure NL → MCP tool mapping.

**Workspace**: `blue-green` — hard-coded. Every CRM tool call MUST pass
`workspace_slug: "blue-green"`.

**Scope**: BlueGreen CRM only (missions, companies, contacts, interactions).
Job Search lives in the Obsidian vault and is handled by `obsidian-crm` — never
write the vault from this skill. Edifice has its own skill — do not touch.

---

## /hal update `<texte libre>`

1. Parse the user's text to detect **intent** (write vs read) and **entity**
   (mission, contact, company, interaction).
2. Resolve referenced entities via the appropriate `list_*` tool, always
   filtering to keep payloads small (see "Entity resolution" below).
3. If the match is ambiguous → list candidates and ask before writing.
4. Call the target MCP tool with `workspace_slug: "blue-green"`.
5. Output result as `✅ [Entité] → [tool]: [valeur]`.

If the user appends `--dry-run`, print the planned MCP calls (tool name +
arguments) without executing them.

---

## Intent → tool mapping

| User says | MCP tool(s) |
|-----------|-------------|
| "propale envoyée [client]", "stage [client] → X" | `list_missions` (filtered) → fuzzy match → `update_mission_stage` |
| "perdu", "refus", "dead", "sans suite" | `update_mission_stage` → `perdu` |
| "gagné", "signé", "soldé", "terminé" | `update_mission_stage` → `solde` |
| "call avec [contact] : [résumé]", "RDV fait", "mail envoyé" | optional `list_contacts` → `log_interaction` |
| "nouveau client [nom]" | `create_company` |
| "nouveau contact [nom] chez [client]" | `list_companies` → match → `create_contact` |
| "nouvelle mission/propale [nom] pour [client]" | `list_companies` → match → `create_mission` |
| "pipeline", "où en est [client]", "deals en cours" | `list_missions` / `list_companies` (read-only) |

---

## Stage mapping (NL → stage value)

| User says | Stage |
|-----------|-------|
| "nouveau prospect", "premier contact" | `prospect` |
| "propale à faire", "devis à envoyer", "il veut un devis" | `devis_a_faire` |
| "gagné", "signé", "soldé", "terminé" | `solde` (terminal) |
| "perdu", "refus", "dead", "sans suite" | `perdu` (terminal) |

`update_mission_stage` sets `closed_at` automatically when the target stage is
terminal. If Renaud adds new stages to `halcrm_workspaces.mission_stages`,
update this table.

---

## Entity resolution (client-side fuzzy match)

The server has no search endpoint — resolve by listing and fuzzy-matching on
names.

**Thresholds**:

- score **> 80** → match direct, proceed with the write
- score **50–80** → list the candidates, ask the user to pick (never write)
- score **< 50** → entity not found, propose creation (never auto-create)

**Rules**:

- **Match on mission name, not on company name.** `company_id` can be null
  (EDF, Engie, Buchan, Lacourt), and a single company often has many missions
  (IC: 10, Valorem: 3, Greenta: 2).
- **Ambiguity is the default**: if several active missions share a company
  (e.g. "Valorem perdu"), list all candidates — unless the conversation context
  makes one obviously correct, in which case confirm the pick in the output.
- **Always filter `list_missions` by `stage`** when the intent allows. Without
  a filter, the response includes the full `description` markdown for every
  mission (~70k chars for 51 missions — too heavy to be useful for matching).

---

## `log_interaction` rules

- **Required**: `workspace_slug`, `channel` (`call` / `email` / `meeting`),
  `summary`.
- **Optional**: `contact_id`, `mission_id`, `occurred_at` (defaults to now).
- If a contact name is cited → `list_contacts` and try to resolve.
- If contact match is **< 80** → log the interaction anyway, put the cited name
  in `summary`. **Never block a log of interaction.**
- Attach `mission_id` whenever the conversation context makes it clear which
  mission the interaction refers to.

---

## Guardrails

- **Confirm before any write if ambiguous.** When in doubt, ask.
- **Dry-run mode**: if the user adds `--dry-run`, print the MCP call plan
  (tool name + arguments) without executing.
- **Never auto-create.** Match score < 50 → propose creation, wait for
  confirmation.
- **Output format**: `✅ [Entité] → [tool]: [valeur]` per successful write.
- **On MCP failure**: output `❌ [Entité] → [tool]: [error reason]`. Surface
  the error to the user immediately — do not retry automatically.

---

## Out of scope (do not handle here)

- **Job Search** — handled by `obsidian-crm`. `/hal` never writes the vault.
- **Edifice missions** — handled by the `edifice` skill via dedicated tools
  (`read_edifice_mission`, `get_mission_with_assets`, `push_mission_context`).
- **Tasks and sprints** — server CRUD (`create_task`, `list_tasks`,
  `update_task`) not yet available. Coming in a future sprint (lot 2).
- **Field updates outside `stage`** — companies / contacts / missions cannot
  be edited (server limitation). Mention it when relevant; do not attempt a
  workaround.
