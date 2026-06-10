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
version: 0.5.0
allowed-tools: "Bash(uv *) Bash(python3 *) Bash(python *) Bash(git *) Bash(mkdir *) Bash(cat *) Read Write Edit Glob"
---

# HAL — BlueGreen CRM updates via hal-mcp (Claude Code)

This skill routes natural-language CRM updates to the `hal-mcp` MCP connector
(Supabase backend). Zero scripts, zero Bash — pure NL → MCP tool mapping.

**Scope**: BlueGreen CRM and any other workspace served by `hal-mcp` (projects,
companies, contacts, interactions, tasks, sprints). Job Search lives in the
Obsidian vault and is handled by `obsidian-crm` — never write the vault from
this skill. Edifice has its own skill — do not touch.

---

## Workspace resolution (applies to every /hal command)

Every CRM tool call MUST pass a `workspace_slug`. Resolve it in this order:

1. **Explicit arg** (`/hal tasks ic`, `/hal list blue-green`) → use that slug
   directly. Shorthand: `ic` → `ic-ingenieurs-conseils`.
2. **No arg** → read the `HAL_DEFAULT_WORKSPACE` env var:

   ```bash
   python3 -c "import os; print(os.environ.get('HAL_DEFAULT_WORKSPACE', '') or 'UNSET')"
   ```

   - Output is a non-empty slug → use it as `workspace_slug`.
   - Output is `UNSET` → respond and stop:

     > ❌ Workspace par défaut non configuré.
     > Ajoute `export HAL_DEFAULT_WORKSPACE=<ton-slug>` dans ton `~/.zshrc`.
     > Sur Claude Desktop : redémarre l'app après modification. Sur Cowork : ajoute la var dans ton `.env`.
     > Relance la commande après.

`/hal devis` is the only exception — it accepts `--workspace SLUG` with its own
defaults (see that section).

---

## Pre-flight : vérifier hal-mcp

Avant toute opération MCP, vérifier que le connecteur est actif :

1. Appeler `list_stages` avec `workspace_slug: "blue-green"`
   *(hardcodé intentionnellement — sonde de connectivité uniquement, doit toujours résoudre vers un slug valide connu)*
2. **Succès** → continuer normalement
3. **Échec** (outil indisponible / connexion refusée / timeout) :

> ❌ **hal-mcp non connecté.**
> Reconnexion : **Claude Desktop → Paramètres → Connexions → hal-mcp → Activer**
> ⚠️ Ne pas lancer de commandes terminal — interface graphique uniquement.
> Relancer la commande après reconnexion.

`/hal devis` ne nécessite pas MCP — ignorer ce check pour cette commande.

---

## /hal list `[workspace]`

Show the CRM pipeline as a text kanban — projects grouped by stage.
Default workspace: resolved from `HAL_DEFAULT_WORKSPACE` env var (see
"Workspace resolution" at top of this skill).

### Steps

**1. Resolve workspace** — use the standard workspace resolution pattern.

**2. Call MCP `list_projects`**

Call with:
- `workspace_slug` (resolved above)
- No `stage` filter — retrieve the full pipeline
- Optional: if the user passed `stage=<value>` or `kind=<value>`, add them as
  the corresponding filter parameters

To know valid stages for a workspace call `list_stages` first if unsure.

**3. Group and display**

Group results by `stage`. Determine ordering:
- **Active stages** = stages where at least one project has `closed_at` null
- **Terminal stages** = stages where all projects have `closed_at` non-null
- Show active stages first (in pipeline order from the data), terminal stages last
- Within each stage, keep the server order (`created_at DESC`)

Display format:

```
### prospect (2)
- DEV-168 · VESTA SA · 12 000 € · Laval (53)
- — · Martin SARL · — · —

### devis_a_rediger (1)
- DEV-045 · IC Ingénieurs Conseils · 8 500 € · Paris (75)

### devis_envoye (3)
- DEV-121 · Valorem · 45 000 € · Bordeaux (33)
- DEV-099 · EDF · — · —
- DEV-088 · Greenta · 3 200 € · Lyon (69)

### ✓ solde (5)
- DEV-055 · Lacourt · 18 000 € — soldé 2026-05-12
```

Line format per project:
`{project_ref or "—"} · {company.name or "—"} · {amount_ht formatted or "—"} · {location or "—"}`

- Format `amount_ht`: space-separated thousands + ` €` (e.g. `12 000 €`). Show `—` if null.
- For terminal stages: append `— soldé {closed_at[:10]}` or `— perdu {closed_at[:10]}`
  when `closed_at` is present.
- Stage header prefix: `✓ ` for terminal stages.
- Never display the `description` field — too verbose for a kanban overview.

**4. Handle edge cases**

- No projects in workspace → `Aucun projet dans le workspace <slug>.`
- Stage is empty → skip that stage in the output (don't show empty sections)
- `description` field received → ignore it entirely
- `kind` filter passed → show only that kind; add `(kind: <value>)` after the workspace name in the header
- `stage` filter passed → show only that stage; useful for "show me all prospects"
- Unknown workspace slug → surface the `list_projects` error verbatim

---

## /hal tasks `[workspace]` `[--mine]` `[--project <ref>]` `[--status <status>]`

Show tasks as a text kanban grouped by status.
Default workspace: resolved from `HAL_DEFAULT_WORKSPACE` env var (see
"Workspace resolution" at top of this skill).

### Steps

**1. Resolve workspace** — use the standard workspace resolution pattern.

**2. Resolve filters**

- `--mine` → add `assignee_email: "<user's own email, from conversation context>"`.
  If email is unknown, ask the user rather than guessing.
- `--project <ref>` → call `list_projects` to resolve `project_id` by name/ref,
  then add `project_id` filter to `list_tasks`.
- `--status <value>` → add `status` filter (`todo` | `in_progress` | `done` | `blocked`).
- No filters → retrieve all tasks in the workspace (no filter).

**3. Call MCP `list_tasks`**

Call with `workspace_slug` (+ resolved filters).

**4. Group and display**

Group by `status`. Fixed order: `todo` → `in_progress` → `blocked` → `done`.
`done` is terminal — prefix header with `✓ `.

Display format:

```
### todo (3)
- Relancer Valorem pour signature · renaud · 2026-06-15
- Préparer propale VESTA · — · —
- Appeler Laurent IC · — · —

### in_progress (1)
- ⚡ Rédiger rapport Varenne · — · 2026-06-20 [S]

### blocked (1)
- Accès chantier Aulnay · — · —

### ✓ done (5)
- Migration Supabase · renaud · 2026-06-05
```

Line format per task:
`{⚡ if priority=high }{title} · {assignee short or "—"} · {due_date or "—"} {[S] if sprint_id set}`

- `assignee short`: local part before `@` from `assignee_email` (e.g. `renaud`
  from `renaud@bluegreen.ai`). Show `—` if null.
- `[S]` marker if `sprint_id` is non-null (sprint name unknown without extra call).
- `priority` field: prepend `⚡` if `priority == "high"`. Skip the marker for
  `normal` / null / other values.

**Note on `project_id`**: `list_tasks` returns a raw UUID. Without a `--project`
filter that pre-resolved the ref, show nothing in that column — the assignee
short is shown instead. A future improvement could join on project data — out
of scope for this release.

**5. Edge cases**

- No tasks → `Aucune tâche dans le workspace <slug>.`
- Empty status group → skip that group entirely (don't show empty sections)
- `HAL_DEFAULT_WORKSPACE` not set + no arg → surface setup instructions (see
  "Workspace resolution" at top of skill)
- Unknown workspace slug → surface the `list_tasks` error verbatim

---

## /hal update `<texte libre>`

1. Parse the user's text to detect **intent** (write vs read) and **entity**
   (mission, contact, company, interaction, task, sprint).
2. Resolve referenced entities via the appropriate `list_*` tool, always
   filtering to keep payloads small (see "Entity resolution" below).
3. If the match is ambiguous → list candidates and ask before writing.
4. Call the target MCP tool with the resolved `workspace_slug` (see "Workspace
   resolution" at top of this skill).
5. Output result as `✅ [Entité] → [tool]: [valeur]`.

If the user appends `--dry-run`, print the planned MCP calls (tool name +
arguments) without executing them.

---

## Intent → tool mapping

| User says | MCP tool(s) |
|-----------|-------------|
| "propale envoyée [client]", "stage [client] → X" | `list_projects` (filtered) → fuzzy match → `update_project_stage` |
| "perdu", "refus", "dead", "sans suite" | `update_project_stage` → `perdu` |
| "gagné", "signé", "soldé", "terminé" | `update_project_stage` → `solde` |
| "call avec [contact] : [résumé]", "RDV fait", "mail envoyé" | optional `list_contacts` → `log_interaction` |
| "nouveau client [nom]" | `create_company` |
| "nouveau contact [nom] chez [client]" | `list_companies` → match → `create_contact` |
| "nouvelle mission/propale [nom] pour [client]" | `list_companies` → match → `create_project` |
| "pipeline", "où en est [client]", "deals en cours" | `list_projects` / `list_companies` (read-only) |
| "mes tâches", "todo list", "qu'est-ce que j'ai à faire" | `list_tasks` (workspace default) |
| "ajouter tâche X", "nouvelle tâche Y", "todo : Z", "créer une tâche" | `create_task` |
| "tâche X faite", "X → done", "X terminé", "c'est fait" | `list_tasks` → fuzzy match → `update_task_status` (done) |
| "X → in progress", "je commence X", "en cours : X" | `list_tasks` → fuzzy match → `update_task_status` (in_progress) |
| "X bloqué", "X → blocked" | `list_tasks` → fuzzy match → `update_task_status` (blocked) |
| "X → todo", "remettre X en attente" | `list_tasks` → fuzzy match → `update_task_status` (todo) |
| "nouveau sprint S<N>", "créer sprint" | `create_sprint` |
| "assigne tâche X au sprint Y", "tâche X dans sprint Y" | `list_tasks` → match task → `assign_task_to_sprint` |

---

## Stage mapping (NL → stage value)

| User says | Stage |
|-----------|-------|
| "nouveau prospect", "premier contact" | `prospect` |
| "propale à faire", "devis à envoyer", "il veut un devis" | `devis_a_rediger` |
| "propale envoyée" | `devis_envoye` |
| "gagné", "signé", "soldé", "terminé" | `solde` (terminal) |
| "perdu", "refus", "dead", "sans suite" | `perdu` (terminal) |

`update_project_stage` sets `closed_at` automatically when the target stage is
terminal. Call `list_stages` if unsure of valid values — stages are now
per-kind in `halcrm_workspaces.kind_stages`.

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
- **Always filter `list_projects` by `stage`** when the intent allows. Without
  a filter, the response includes the full `description` markdown for every
  project (~70k chars for 51 projects — too heavy to be useful for matching).

---

## Task resolution (fuzzy match)

Same thresholds as entity resolution (score > 80 / 50–80 / < 50).

- Match on `title`. Call `list_tasks` with **no `status` filter** — "X → done"
  must match tasks that are currently `todo` or `in_progress`.
- Ambiguity: multiple tasks at the same score → list candidates, ask to pick.
- `update_task_status` takes `workspace_slug`, `task_id`, and `status`. Always
  pass `workspace_slug` — resolved from arg or `HAL_DEFAULT_WORKSPACE`.
- **Never auto-create a task from an ambiguous match.** Score < 50 → propose
  creation.
- "c'est fait" / "done" said after completing a described action → propose the
  corresponding task write, do not auto-write.
- **Sprint resolution**: no `list_sprints` MCP tool exists. To filter
  `list_tasks` by `sprint_id` (e.g. "tâches du sprint actuel"), the user must
  provide the sprint UUID. If only a number/name is given and no recent
  `create_sprint` response is in context → ask for the UUID.

---

## `log_interaction` rules

- **Required**: `workspace_slug`, `channel` (`call` / `email` / `meeting`),
  `summary`.
- **Optional**: `contact_id`, `project_id`, `occurred_at` (defaults to now).
- If a contact name is cited → `list_contacts` and try to resolve.
- If contact match is **< 80** → log the interaction anyway, put the cited name
  in `summary`. **Never block a log of interaction.**
- Attach `project_id` whenever the conversation context makes it clear which
  project the interaction refers to.

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

## /hal devis `[--workspace SLUG]`

Generate a DOCX devis (IC Ingénieurs Conseils format) from conversation context.

Default workspace: `ic-ingenieurs-conseils`. Pass `--workspace blue-green` to
generate a Blue Green devis (prefix BG). Other slugs are rejected by the script.

### Steps

1. **Gather context** — collect from the conversation (or ask if missing):
   - `client.name` (required), `client.contact_name`, `client.contact_email`
   - `project.name` — the mission title
   - `scope` — free text: what IC will do, conditions, rythme
   - `workpackages` — list of `{"ref": "WP1", "title": "...", "price": 5000}` entries
   - (Optional) `deliverables` list, `terms.deposit_percent`, `terms.validity_days` (default 30)
   - Do NOT set `reference`, `date`, or `valid_until` — the script fills them automatically.

2. **Find hal repo root**:
   ```bash
   HAL_ROOT=$(git -C "$(pwd)" rev-parse --show-toplevel 2>/dev/null || echo "$HOME/Projects/hal")
   echo "hal root: $HAL_ROOT"
   ```

3. **Write JSON context to a temp file**:
   ```bash
   mkdir -p /tmp/hal_devis
   ```
   Then use the Write tool to create `/tmp/hal_devis/context.json` with the
   `DevisICContext`-shaped JSON. Required top-level keys: `client`, `project`,
   `scope`, `workpackages`, `pricing` (use `{}` for defaults).

4. **Generate DOCX**:
   ```bash
   cd "$HAL_ROOT" && uv run python scripts/generate_devis.py \
       --workspace ic-ingenieurs-conseils \
       --json /tmp/hal_devis/context.json
   ```
   The script prints the absolute DOCX path on success, or an error on stderr.

5. **Report result**:
   Output: `✅ Devis généré : <absolute_path>`.
   Read the first few paragraphs of the DOCX to confirm client name, total TTC.

### Error handling

- Script exits 1 → surface the stderr output verbatim to the user. Fix the JSON.
- Missing `workspaces/<slug>/documents/` → the script creates it automatically.
- Unknown workspace slug → `ValueError` from the script; valid slugs: `ic-ingenieurs-conseils`, `blue-green`.
- `uv` not found → run `cd "$HAL_ROOT" && python3 scripts/generate_devis.py --workspace ... --json ...` instead.

---

## Out of scope (do not handle here)

- **Job Search** — handled by `obsidian-crm`. `/hal` never writes the vault.
- **Edifice missions** — handled by the `edifice` skill via dedicated tools
  (`read_edifice_mission`, `get_mission_with_assets`, `push_mission_context`).
- **Task field updates** — only `status` can be updated via
  `update_task_status`. Title, due_date, assignee, description, priority
  cannot be edited after creation (server limitation — no `update_task` tool).
- **Sprint listing** — no `list_sprints` MCP tool. Sprint UUIDs must be
  provided by the user or resolved from a previous `create_sprint` response.
- **`project_id` join** — `list_tasks` returns a raw `project_id` UUID, not
  the project ref. A separate `list_projects` call resolves it — done
  automatically when `--project <ref>` filter is used, otherwise the column
  is omitted.
- **Field updates outside `stage` (projects) and `status` (tasks)** —
  companies / contacts / mission fields cannot be edited (server limitation).
  Mention it when relevant; do not attempt a workaround.
