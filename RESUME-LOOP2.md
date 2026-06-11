# RESUME — Loop 2 (`/hal tasks`, default = current sprint) — start here

> Written 2026-06-11 from the hal session that **froze the backend** (Loop 1 / PR #42).
> Loop 2 is **skills only**, in **this repo** (`bluegreen-marketplace`). hal-mcp is frozen at
> **v38, 26 tools** — you only *consume* its tools, you never add or change one.

## What this loop is

Bring `/hal tasks` to daily-usable: merge the pending whoami-based PR, then make the **default
invocation show the current sprint's kanban** for both `blue-green` (business) and `renaud` (perso).

- **Master plan**: `../hal/docs/lastdev-plan.md` (the 4 loops, freeze line).
- **Brief**: relocated here → [`docs/loop-2-hal-tasks-skill.md`](docs/loop-2-hal-tasks-skill.md)
  (Archon runs from this repo, so the brief must live here).

## Pre-flight (do first, in order)

1. **Connectivity** — you connect to hal-mcp over **OAuth** (the plugin `.mcp.json` is `type:http`,
   URL only, no auth header). Call `whoami` → expect `renaud@bluegreen.ai` + workspaces
   `blue-green` (default), `ic-ingenieurs-conseils`, `renaud`. 200 = MCP reachable + provisioned.
   *(API-key auth exists in the code but is dormant/broken — do not use it. See
   `../hal/docs/operations.md`.)*
2. **Confirm the frozen tool surface — DO NOT ASSUME** (the brief warns about this and it bit us):
   - `update_task` = partial attributes only: `title, description, due_date, project_id,
     assignee_email, priority, external_ref`. **NOT `status`, NOT `sprint`.**
   - status → `update_task_status` (todo/in_progress/done/blocked).
   - sprint → `assign_task_to_sprint` (or `sprint_id` inline on `create_task`).
   - current sprint → `list_sprints(workspace_slug, status="actuel")`.
   > ⚠️ The brief's "Deliverables" line still says `update_task` handles *sprint* — that is **stale**.
   > M1 (Loop 1 freeze decision) removed both `status` and `sprint` from `update_task`:
   > three single-responsibility writers. Honor the deployed surface, not the old brief text.

## Step 0 — seed a realistic sprint (run these MCP calls; you're OAuth-connected)

So the kanban isn't empty when you test. **No workspace currently has any sprint** (the Loop 1
validation sprint was cleaned up). Plausible tasks are drawn from the real Blue Green pipeline in
the Obsidian vault; `external_ref` points back to the opportunity note (the loose-coupling design).

`priority` uses `high`/`medium`/`low` (the value validated in Loop 1).

**A. blue-green — current sprint + 7 tasks**

1. `create_sprint(workspace_slug="blue-green", name="Sprint 24 — semaine 11-15 juin", sprint_number=24, status="actuel")` → keep `sprint_id`.
2. `create_task` ×7 with that `sprint_id` (then bump status on the non-todo ones via `update_task_status`):

   | title | priority | external_ref | due_date | final status |
   |---|---|---|---|---|
   | Relancer Greenta — propale Audit IA + déploiement | high | `CRM-BlueGreen/Opportunites/Greenta — Audit IA + Déploiement` | 2026-06-12 | in_progress |
   | Envoyer le devis IC — DIAG La Poste Longjumeau | high | `CRM-BlueGreen/Opportunites/IC Ingénieurs Conseils-DIAG La Poste Longjumeau` | 2026-06-12 | in_progress |
   | Finaliser la propale Eneor — Accompagnement IA BET | high | `CRM-BlueGreen/Opportunites/Eneor — Accompagnement IA BET` | 2026-06-13 | todo |
   | Préparer l'atelier IA — Pierre Lacourt × Cyril Laborbe | medium | `CRM-BlueGreen/Opportunites/Atelier IA — Pierre Lacourt × Cyril Laborbe` | 2026-06-13 | todo |
   | Suivre BlueWind Companion — EDF Power Solutions | medium | `CRM-BlueGreen/Opportunites/EDF Power Solutions — BlueWind Companion` | 2026-06-15 | todo |
   | Relancer D-ICE Engineering — positionnement stratégie | low | `CRM-BlueGreen/Opportunites/D-ICE Engineering-Strategy Positionnement` | — | todo |
   | Débrief Boreales energy — levier sur offre existante | medium | `CRM-BlueGreen/Opportunites/Boreales energy- Levier sur offre existante` | 2026-06-11 | done |

   → kanban spread: **2 in_progress / 4 todo / 1 done**.

**B. renaud — current sprint + 4 perso tasks** (for `/hal tasks renaud`, criterion 2)

1. `create_sprint(workspace_slug="renaud", name="Perso — semaine 11-15 juin", sprint_number=1, status="actuel")`.
2. `create_task` ×4 with that `sprint_id`:

   | title | priority | due_date | final status |
   |---|---|---|---|
   | Boucler le dossier prêt d'honneur AFACE | high | 2026-06-13 | in_progress |
   | Déclarer les charges URSSAF Q2 | high | 2026-06-15 | todo |
   | Relancer 2 candidatures jobsearch | medium | 2026-06-12 | todo |
   | Réserver les vacances d'été (famille) | low | — | todo |

> Cleanup later if needed: no `delete_*` tool exists — delete rows directly with the service key
> (`DELETE FROM halcrm_tasks/halcrm_sprints WHERE workspace_slug=... AND ...`), as in the Loop 1 session.

## Loop 2 work (the actual deliverable)

1. **Merge PR #12** (`archon/task-feat-hal-whoami-v07` — whoami workspace resolution + `/hal tasks`
   skeleton). **Close PR #11** (`archon/task-feat-hal-lot2-tasks-sprints` — superseded env-var approach).
2. **Default = current sprint**: `/hal tasks` (no `--status`/`--sprint`) → resolve current sprint via
   `list_sprints(status="actuel")`, list its tasks as a **kanban by status**. **No current sprint →
   explicit message + fallback to open tasks** (never a silent empty board).
3. **Workspace**: default `whoami.default_workspace_slug` (`blue-green`); `/hal tasks renaud` → perso.
   One workspace per call (no cross-workspace aggregation — that's Loop 3 morning-briefing).
4. **NL task intents** in the skill: create (`create_task` w/ `priority`+`external_ref`), edit
   (`update_task` — attributes only), status (`update_task_status`), sprint (`assign_task_to_sprint`).
5. **Version bump** `0.6.0 → 0.7.0` — keep `plugin.json === marketplace.json`, bump skill `hal`.

## Acceptance criteria (from the brief)

1. `/hal tasks` → current-sprint kanban in `blue-green` (Step 0-A makes this non-empty).
2. `/hal tasks renaud` → current-sprint kanban for perso (Step 0-B).
3. `/hal tasks --status blocked` → only blocked tasks.
4. NL edit ("repousse la relance Greenta à lundi") → `update_task` with new `due_date`.
5. No current sprint → explicit message + fallback, never silent empty.

## Guardrails

- **hal-mcp is frozen** — if you feel you need a new tool/param, you're doing Loop 2 wrong. Re-read.
- Run Loop 2 via the **`archon` skill** (`archon-idea-to-pr`) from *this* repo, or hand-build — but
  do not raw-`archon workflow run` from Bash.
- After merge, update this repo's `.claude/STATUS.md` (Loop 2 done) and delete this file.

## After Loop 2 — the loop chain LEAVES this repo

**Loop 2 is the last loop in `bluegreen-marketplace`.** Once `/hal tasks` is merged (v0.7.0):

- **Loop 3 → repo `renaud-marketplace`** (the `morning-briefing` / gmail-mcp / jobsearch plugin).
  New architecture for the daily view: hal tasks (both `blue-green` + `renaud` current sprints) +
  Obsidian jobsearch + the 3 Google Calendars, in **one** pro+perso dashboard. This is where the
  two workspaces finally get aggregated (the cross-workspace view that `/hal tasks` deliberately
  does *not* do).
- **Loop 4 → `renaud-marketplace` + Obsidian** — systematize jobsearch (`log-application` +
  `interview-prep` skills). Deadline **Sun 2026-06-14 → STOP**.

So: when Loop 2 merges, **`cd ../renaud-marketplace`** and start a fresh session there from the
Loop 3 brief (`../hal/docs/features/loop-3-morning-briefing.md` — relocate it into
`renaud-marketplace`, same as this one). Master plan: `../hal/docs/lastdev-plan.md`.
