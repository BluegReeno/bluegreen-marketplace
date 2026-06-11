# Loop 2 — `/hal tasks` finalized (default = current sprint)

> **Repo**: `bluegreen-marketplace` · **Target**: `plugins/hal/` (skill `hal`, `commands/hal.md`)
> **Depends on**: Loop 1 (`list_sprints`, `update_task`, `external_ref`). **Confirm the exact
> tool names/params from the merged Loop 1 PR before launching — do not assume.**
> Relocated from `hal/docs/features/loop-2-hal-tasks-skill.md` (Archon runs from this repo).

> 🛠️ **CORRECTION (post-Loop-1 freeze)** — the "Deliverables" bullet below mentions `update_task`
> editing *sprint*. **That is stale.** Loop 1 decision **M1** removed both **`status`** and
> **`sprint`** from `update_task` (three single-responsibility writers):
> - `update_task` → attributes only (`title, description, due_date, project_id, assignee_email,
>   priority, external_ref`).
> - `update_task_status` → status (todo/in_progress/done/blocked).
> - `assign_task_to_sprint` (or `sprint_id` inline on `create_task`) → sprint.
> hal-mcp is **frozen at v38** — honor the deployed surface.

## Objective

Bring `/hal tasks` to a daily-usable state. Merge the pending **PR #12** (whoami-based workspace
resolution + the first `/hal tasks` kanban), then make the **default invocation show the current
sprint's tasks**, working for both the `blue-green` (business) and `renaud` (perso) workspaces.

## Deliverables

- **Merge PR #12** (whoami resolution + `/hal tasks` skeleton). Close the superseded PR #11.
- **Default = current sprint**: `/hal tasks` with no `--status`/`--sprint` resolves the current
  sprint via `list_sprints(status: "actuel")` and lists its tasks (all statuses, kanban by status).
  If no current sprint exists, fall back to all open tasks **and say so explicitly** (no silent empty).
- **Workspace**: defaults to `whoami.default_workspace_slug` (`blue-green`); `/hal tasks renaud`
  targets perso. One workspace per call.
- **NL task intents** in the skill: create (`create_task`, now with `priority`/`external_ref`),
  edit (`update_task` — attributes only, see correction banner), status change
  (`update_task_status`), sprint assign (`assign_task_to_sprint`).
- Version bump: plugin `0.6.0 → 0.7.0`, skill `hal` accordingly, `plugin.json === marketplace.json`.

## Non-goals

- No cross-workspace aggregation in `/hal tasks` (perso + business in one view is the **Loop 3
  morning-briefing** job, not this command).
- No NL trigger phrases in the SKILL frontmatter (backlog).
- No `domain` concept.
- No sprint create/close UX beyond the existing `create_sprint` / `assign_task_to_sprint` intents.

## Acceptance criteria

1. `/hal tasks` (no args) → kanban of the **current sprint** in `blue-green`.
2. `/hal tasks renaud` → current-sprint kanban for the perso workspace.
3. `/hal tasks --status blocked` → only blocked tasks.
4. An NL edit ("repousse la relance Greenta à lundi") → calls `update_task` with the new `due_date`.
5. No current sprint → explicit message + fallback to open tasks, never a silent empty board.
