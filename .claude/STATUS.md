# STATUS — bluegreen-marketplace

Last updated: 2026-06-24

## Current Focus

**GitHub portfolio cleanup** — ✅ terminée. Vieux plans supprimés, README mis à jour, `.gitignore` renforcé.

## In Progress

_(rien — sprint terminé)_

## Done (current sprint)

- [x] **GitHub portfolio cleanup** — PR #26 mergée — 2026-06-24
  - 10 vieux fichiers de plans supprimés (`.agents/plans/`, `.claude/plans/`) — 4100 lignes
  - `.gitignore` renforcé (patterns plans + artifacts)
  - `README.md` mis à jour : version v0.9.0, skills `pm` + `crm` + `edifice`

- [x] **#20 — Créer skill `/crm`** — PR #25 mergée — 2026-06-17
  - Skill `/crm` créé (`plugins/hal/skills/crm/SKILL.md`) + `commands/crm.md`
  - Commandes : `list`, `new`, `qualify` (BANT), `log` (CR), `update`, `contact new/update`, `doc`
  - BANT stocké dans `description` jusqu'à colonne Supabase dédiée
  - `contact update` câblé sur `update_contact` MCP (graceful degradation si outil absent)
  - Version bumpée 0.8.0 → **0.9.0** (plugin.json + marketplace.json)
  - Issue #20 close automatiquement, issue #22 fermée manuellement

- [x] **#22 — `update_contact`** — Issue fermée — 2026-06-17
  - Intégré dans `/crm contact update` (PR #25)
  - PR #23 (scope /pm) fermée sans merge — contacts hors scope /pm

- [x] **#19 — Rename `/hal` → `/pm`** — PR #24 mergée — 2026-06-17
  - Skill `/pm` créé (`plugins/hal/skills/pm/SKILL.md`), `/hal` supprimé
  - `commands/pm.md` remplace `commands/hal.md`
  - Version bumpée 0.7.2 → **0.8.0** (plugin.json + marketplace.json + SKILL.md)

- [x] **Issues #8, #5, #9 — fix + tests edifice** — commit `0b24009` — 2026-06-17
  - #8 : warning print pour disorder photo failures (render_diagnostic.py:110)
  - #5 : suite pytest `tests/test_build_context.py` (8 tests, build_building_context + _download_building_2d_map)
  - #9 : suite pytest `tests/test_render_diagnostic.py` (11 tests, _render_methodo_item + tag filtering + _building_block)
  - 19/19 tests passent

- [x] **#16 — Label `ai-improvable` créé** — issue fermée — 2026-06-17
- [x] **Fix workflow Archon `skill-improve`** — commit `522c4d1` — 2026-06-17
- [x] **docs(claude): règles Archon correctes** — commit `bf404fb` — 2026-06-17
- [x] **docs: refs Claude connector mises à jour** — 2026-06-17
- [x] **update_sprint wiring — hal v0.7.2** — 2026-06-15
- [x] **PR #14 — guide multi-provider connector & skills** — 2026-06-14
- [x] **WP-C — `/hal tasks --tag` (PR #15 · v0.7.1)** — 2026-06-14
- [x] **Loop 2 — `/hal tasks` daily-usable v0.7.0** — PR #12 mergée — 2026-06-11

## Backlog

- [ ] **#21** — lien projets internes ↔ opportunités (migration Supabase Option A recommandée)
- [ ] **#13** — Connexion Gemini Enterprise (console steps manuels — voir issue)
- [ ] schema-contract.json — cross-repo sync anchor (hal v0.3.0+)
