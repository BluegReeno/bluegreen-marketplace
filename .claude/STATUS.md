# STATUS — bluegreen-marketplace

Last updated: 2026-06-17

## Current Focus

**Refonte skill architecture** — `/hal` → `/pm` + nouveau skill `/crm`. Issues #19/#20/#22 traitées via Archon. PRs à merger puis push.

## In Progress

- [ ] **#19 — Rename `/hal` → `/pm`** — Archon `skill-improve "19"` en cours (lancé ~14h30).
  Monitorer : `archon workflow status` + `tail -f /tmp/archon-19b.log`
  Après completion : vérifier la PR créée, merger, puis lancer #20.

- [ ] **#20 — Créer skill `/crm`** — auto-lancé par le script monitor dès que #19 termine.
  Log : `/tmp/archon-20b.log`

## Done (current sprint)

- [x] **Issues #8, #5, #9 — fix + tests edifice** — commit `0b24009` — 2026-06-17
  - #8 : warning print pour disorder photo failures (render_diagnostic.py:110)
  - #5 : suite pytest `tests/test_build_context.py` (8 tests, build_building_context + _download_building_2d_map)
  - #9 : suite pytest `tests/test_render_diagnostic.py` (11 tests, _render_methodo_item + tag filtering + _building_block)
  - 19/19 tests passent

- [x] **#16 — Label `ai-improvable` créé** — issue fermée — 2026-06-17

- [x] **#22 — `update_contact` dans skill hal** — PR #23 ouverte — 2026-06-17
  - Archon `skill-improve "22"` a tourné et ouvert PR #23 `feat(skill:hal): add update_contact`
  - Version bumpée 0.7.2 → **0.8.0** (plugin.json + marketplace.json)
  - ⚠️ PR #23 modifie `plugins/hal/skills/hal/SKILL.md` — merger APRÈS #19 pour éviter conflit

- [x] **Fix workflow Archon `skill-improve`** — commit `522c4d1` — 2026-06-17
  - `command: archon-fix-github-issue-experimental` → `.md` introuvable (c'est un YAML workflow)
  - Remplacé par `prompt:` inline avec les étapes complètes fetch/implement/PR
  - Deux bugs documentés dans CLAUDE.md : pipe SIGPIPE + SQLite lock concurrent

- [x] **docs(claude): règles Archon correctes** — commit `bf404fb` — 2026-06-17
  - Ne jamais piper `archon workflow run` (SIGPIPE tue le process)
  - Lancer séquentiellement (SQLite single-writer)

- [x] **docs: refs Claude connector mises à jour** — 2026-06-17
- [x] **update_sprint wiring — hal v0.7.2** — 2026-06-15
- [x] **PR #14 — guide multi-provider connector & skills** — 2026-06-14
- [x] **WP-C — `/hal tasks --tag` (PR #15 · v0.7.1)** — 2026-06-14
- [x] **Loop 2 — `/hal tasks` daily-usable v0.7.0** — PR #12 mergée — 2026-06-11

## À faire après que les Archon terminent

1. **Merger PR #19** (rename /hal → /pm) — vérifier que le skill s'appelle bien `/pm`
2. **Merger PR #20** (skill /crm) — vérifier les déclencheurs BANT + format CR
3. **Merger PR #23** (update_contact) — après #19 pour éviter conflit SKILL.md
4. **Bumper CHANGELOG.md** pour la release qui regroupe #19 + #20 + #22 (MINOR — nouvelle interface)
5. **Issue #21** — lier projets internes ↔ opportunités — nécessite migration Supabase (`parent_project_id` FK dans `projects`) + discussion choix Option A/B/C

## Backlog

- [ ] **#21** — lien projets internes ↔ opportunités (migration Supabase Option A recommandée)
- [ ] **#13** — Connexion Gemini Enterprise (console steps manuels — voir issue)
- [ ] schema-contract.json — cross-repo sync anchor (hal v0.3.0+)
