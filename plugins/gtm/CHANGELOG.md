# Changelog — gtm

All notable changes to this plugin are documented here.

## Versioning convention

`0.MINOR.PATCH` (pre-1.0):
- **PATCH** (`0.x.Y+1`) — bugfix, optional field, internal improvement with no interface impact
- **MINOR** (`0.X+1.0`) — interface change: new required field, renamed command, observable behaviour change

Requires the `hal` plugin, which carries the `hal-mcp` connector this plugin's skills call.

---

## [0.2.3] — 2026-08-29 — `list_stages` retiré de hal-mcp, les étapes arrivent par `whoami`

`hal#135` a tranché le porteur de chaque vocabulaire : ce qui **diffère par workspace** voyage
dans `whoami`, qui est déjà appelé en pre-flight par ce skill. `kind_stages` (les étapes du
pipeline par `kind` de projet, `{active, terminal}`) en fait partie, donc l'outil de découverte
`list_stages` a été supprimé du registre hal-mcp (35 → 34 outils). Sans cette migration, le
skill appellerait un outil qui n'existe plus.

Le seul appel de ce skill était de toute façon cassé : `list_stages(workspace_slug)` était
passé **sans `kind`**, et `getKindStages` retombait sur la clé `"default"` qu'aucun workspace
ne déclare → `Unknown project kind: "default". Valid: project, opportunity`, en échec depuis
que `hal#118` a fermé le vocabulaire des `kind`. Le pliage dans `whoami` supprime le mode
d'échec : il n'y a plus d'argument `kind` à se tromper, et tous les `kind` arrivent d'un coup.

- `skills/crm/SKILL.md` : `list_stages` retiré de `allowed-tools` ; le pre-flight met
  `kind_stages` en cache avec le reste de la réponse `whoami` ; la validation de stage de
  `/crm update` lit ce cache ; 2 lignes de routage mises à jour.
- `commands/crm.md` : 2 lignes de routage mises à jour.
- Aucun appel MCP supplémentaire : `kind_stages` voyage sur une réponse déjà payée.

---

## [0.2.2] — 2026-08-28 — every `tags` writer picks from the workspace vocabulary, fix a stale hardcoded tag

`whoami` already returns each workspace's `allowed_tags`, but no skill spelled out the rule for
using it. Measured on prod: 67 tag values outside the workspace vocabulary across 28 rows —
some of it traced back here: `commands/linkedin.md` still hardcoded `tags: ["linkedin"]` on
every `create_task`/`list_tasks` call, even though `skills/linkedin/SKILL.md` was fixed to
`marketing` after the same bug broke `create_task` on `blue-green` (`linkedin` isn't in that
workspace's `allowed_tags` — see `hal` CHANGELOG [0.11.5]). Because `commands/*.md` files are
self-contained (the skill body isn't preloaded when the command fires), the fix never reached
the command file, so `/linkedin idea|backlog|draft|log` kept failing/silently drifting.

- `commands/linkedin.md`: replaced every `tags=["linkedin"]` / `tags: ["linkedin"]` with
  `tags: ["marketing"]` (5 call sites), matching `skills/linkedin/SKILL.md`.
- `crm` (SKILL + `commands/crm.md`), `linkedin` (SKILL + `commands/linkedin.md`): added a
  `## Tags` section — `tags` means functional domain, pick only from the calling workspace's
  `allowed_tags` (via `whoami`), fall back to `other`, never invent a value, and never
  duplicate what `company_id`/`role`/`channel`/`project_id` already carry. The rule does not
  claim `hal://vocabulary` exists — that resource is proposed (`BluegReeno/hal#123`) and
  unimplemented. Byte-identical to `pm`'s and to `renaud-marketplace`'s (`rm#107`), so one
  grep finds every writer across the portfolio.

Closes [#86](https://github.com/BluegReeno/bluegreen-marketplace/issues/86).

## [0.2.1] — 2026-08-27 — /linkedin backlog: handle blocked and cancelled statuses

`list_tasks` returns five statuses since hal#98 (`todo`, `in_progress`, `done`,
`blocked`, `cancelled`), but `/linkedin backlog` only grouped three
(`todo` → `in_progress` → `done`). Tasks in `blocked` or `cancelled` fell between
groups and were silently dropped or misfiled — confirmed in production against
`marketing`-tagged tasks (3 `cancelled` tasks had no bucket).

Grouping order is now `todo` → `in_progress` → `blocked` → `done` → `cancelled`.
`blocked` gets its own section (prefixed `⛔ `) between `in_progress` and `done`.
`cancelled` is terminal like `done` and gets a trailing section (prefixed `✗ `) —
excluded from prior "active work" sections but not dropped from the report, so
the editorial backlog stays traceable.

Updated in both `skills/linkedin/SKILL.md` and `commands/linkedin.md`.

Closes #83.

## [0.2.0] — 2026-08-14 — /crm log update

Add `/crm log update` to correct an already-logged interaction (`summary`, `transcript`,
`channel`, `occurred_at`, `contact_id`, `project_id`, `tags`) via the new `update_interaction`
hal-mcp tool (hal-mcp v60, deployed 2026-08-14). Previously a logged interaction was immutable —
the only "fix" was creating a duplicate via `/crm log`. `interaction_id` has no MCP lookup path
(`list_interactions` does not exist), so `/crm log` now echoes the created `interaction_id` and
`/crm log update` resolves it from conversation context only. No delete path — none is exposed.

Closes #27.

## [0.1.0] — 2026-08-02 — extract crm and linkedin from the hal monolith

## [0.0.0] — seed

Placeholder entry so version-sync stays green while `crm` and `linkedin` are being extracted
from the `hal` monolith (#66). Superseded by `0.1.0`, the first released version.
