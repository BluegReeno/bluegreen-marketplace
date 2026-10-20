# Changelog — gtm

All notable changes to this plugin are documented here.

## Versioning convention

`0.MINOR.PATCH` (pre-1.0):
- **PATCH** (`0.x.Y+1`) — bugfix, optional field, internal improvement with no interface impact
- **MINOR** (`0.X+1.0`) — interface change: new required field, renamed command, observable behaviour change

Requires the `hal` plugin, which carries the `hal-mcp` connector this plugin's skills call.

---

## [0.3.0] — 2026-10-16 — rewritten once against the target contract (hal audit q17, q25, q49; roadmap step 3)

MINOR — the commands changed. The version is bumped once on `next` (hal
`migration-closing-plan.md` § 5); the heading takes its date the day `next` is fast-forwarded into
`main`.

- **`call` added**, ported by hand from PR #101 (`feat/hal-192-gtm-call`): resolve the project, fetch
  the Granola or pasted transcript, correct it, extract signals, write the interaction and the
  `call_analysis` document (`knowledge=true`, hal#235), index. Rewritten for the four project kinds
  (an ongoing mission is a `client` project, no BANT), archived workspaces (refused by name) and
  `renaud-newjob` (the `jobsearch`-type workspace) for interviews. `/crm log` is retired for it.
- **`crm` cut to four gestes** — `new` (duplicate check, vocabulary, BANT draft), `qualify` (BANT
  merge), `stage` (reason before a loss, `client` project created on a win), `review` (pipeline,
  dormant first). `update`, `contact`, `doc`, `list`, `log` and `log update` are gone: single tool
  calls, named in the sentence. Stages are read from `kind_stages.opportunity`; an opportunity needs
  a counterpart (company or contact).
- **`linkedin` repaired** — `idea`, `draft`, `log`. `draft` reads `marketing/tone_of_voice`
  (`list_documents` then `get_document`) and stops when it is missing; posts are short (800
  characters), one per week, oriented toward the job search, saved with the right `save_document`
  arguments (`content_md`, `slug`, `domain`, `kind`). `backlog` and `trend` removed; `stats` is not
  built (bgm#35).
- **`call` indexes where hal-mcp is** — the ingest step takes its environment file from `HAL_ENV_FILE` (default the checkout's `.env`, which may still aim at the frozen cloud) and shows the host, never a key, in the plan.
- **`call` takes what PR #109 had** (hal q56: `next` won, #109 closed): § 3a lists the Granola
  calls with no CR, found by the `[granola:<8>]` mark the interaction `summary` now carries; § 11
  prepares the next meeting from hal rows only (`kb_search`, `list_tasks`, `list_documents`,
  `get_document_link`); « Acceptance — S01 » maps each step of the story to the tool calls, split
  between `jobsearch:log-cr` (vault, until cutover — hal q54) and this skill (hal).
- **`call` states the `heure` contract** — `HH:MM–HH:MM`, `HH:MM` alone when the end is unknown, or `null`; hal's `call_analysis.py render` now refuses anything else (hal S01: « 10:00–<à compléter> » reached the indexed document).
- **`commands/` removed**: `crm.md` and `linkedin.md` were 322 lines that drifted from the skills.
- **`crm review` reads a company workspace only** (step 0): never the candidatures of a `jobsearch`
  workspace nor a `personal` one. No slug and no company default → the one live company workspace
  with `opportunity`, or ask among several — never fold them (hal S02 `sc3`, three runs out of three:
  « Quel est mon pipeline ? » answered with the job-search funnel, the pme pursuit never in it).
- **`crm review` reads the open tasks of a dormant pursuit before proposing a relance** (step 4):
  an existing relance is named with its due date, never proposed again (hal S02 `sc3`, run
  `20261014-105458`: the overdue « Relancer Hélène Mercier sur le devis » unseen, two relances
  proposed, one a duplicate).
- **`crm new` proposes before it creates** — step 2 shows the company, the contact and the
  opportunity it would create, with the `ecosystem`, `activity_type`, `stage`, `tags`, `amount_ht`
  (an amount said without HT/TTC is shown as « HT, supposé », corrected in the yes) and the BANT draft, then stops on « Je crée ? »; the three
  `create_*` run only after the yes, company → contact → project (hal S02 `sc1-intro`, eval case
  `s02-sc1-intro`, two `opus` runs out of two: the three rows created in the first turn, no question).

- **`call`: one rule for a summary-only source** (§ 3). A Granola AI summary, notes or a CR is
  never a transcript: never a signal, a quote nor an interaction's `transcript`, and no
  `call_analysis` is written without a transcript. Granola without one → `granola:SANS TRANSCRIPT`
  and one question: (a) paste the transcript, (b) the interaction alone, no analysis, no ingestion,
  (c) nothing on the hal side yet. A re-run on the same source does the same — never an analysis
  added « to complete » the first pass. The refusal was the rule the skill already implied (§ 5:
  quotes copied word for word, anchored by `render` in the transcript; « rien que le transcript
  n'énonce pas »). hal S01 on the real rows (migration block 4, 2026-10-15): `l1-log` refused,
  `l2-relance` wrote and indexed a 17-signal analysis quoted from the summary.
- **`call`: a non-answer is asked again** — a question with options waits for an option named;
  « continue tel que tu l'as proposé » picks none (same run: option (b) taken on it, « la seule
  possible »).
- **`call` indexes only what the call produced** (§ 9): one `ingest.py --pending --only <uri>` per
  source — the interaction when it carries a transcript, the analysis `D` (`document.id` of
  `save_document`) — each expected to show `rows seen 1`; nothing produced, no ingestion. `--pending`
  alone swept the workspace's queue (same run: `retex-monday-2026-10` indexed by a call log).
- **`call` § 12 — retrouver un passage**: « retrouve le passage de l'entretien … » goes through
  `kb_search(kind=["call","call_analysis"])` before any answer, quotes what it returns with its date,
  and says an absence only of what it read (« hal n'a pas ce passage »), never of a vault CR it did
  not open (same run, `s8-passage`: no hal call, and « il n'y a pas de compte-rendu » while the CR
  was there). `knowledge:ingest` points the question here.

## [0.2.6] — 2026-10-07 — crm and linkedin lose their /edifice routing line — the edifice plugin is archived (hal audit q20)

## [0.2.5] — 2026-09-25 — crm resolves companies and contacts with list_*(search=…) — since hal#171 the lists return a 100-row page, not every row

## [0.2.4] — 2026-08-29 — Le pointeur remplace la doctrine `tags`, `hal://vocabulary` ne verra jamais le jour

`hal#135` (scope D) a tranché que le carrier de la doctrine `tags` est hal-mcp lui-même — le
paragraphe de 523 caractères dupliqué dans `commands/crm.md`, `commands/linkedin.md`,
`skills/crm/SKILL.md` et `skills/linkedin/SKILL.md` promettait une resource MCP
`hal://vocabulary` que `#135` a définitivement écartée : les round-trips coûteraient
`resources/list` + `resources/read`, alors que `whoami` — déjà appelé par chaque skill qui
écrit dans hal — renvoie `allowed_tags` depuis hal-mcp v70. Le paragraphe est réduit à un
pointeur d'une ligne vers les `instructions` du serveur MCP, seule source de la doctrine
complète désormais — `instructions` reste ignoré par claude.ai/Cowork et tronqué à 2 Ko par
Claude Code, donc le pointeur porte lui-même le minimum exigible (workspace, `allowed_tags`,
`other`, colonnes déjà porteuses).

`skills/crm/SKILL.md` l.37-38 : la description de `kind_stages` en cache (pre-flight)
n'énumère plus `{active, terminal}` — `hal#137` ajoute `won` à ce même tableau, une
énumération figée ici serait devenue fausse le jour où ce champ shippe. Le check de stage
cible (l.282-283) reste inchangé : il valide déjà contre l'union `active` + `terminal` sans
nommer les clés, donc il reste exact que `won` en fasse partie ou non.

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
