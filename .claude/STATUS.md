# STATUS — bluegreen-marketplace

Last updated: 2026-06-17

## Current Focus

**Refonte skill architecture** — `/hal` → `/pm` ✅ + nouveau skill `/crm` en cours (Archon #20 lancé).

## In Progress

- [ ] **#20 — Créer skill `/crm`** — Archon `skill-improve "20"` re-lancé (~16h00).
  Log : `tail -f /tmp/archon-20b.log`
  Après completion : vérifier la PR créée, vérifier déclencheurs BANT + format CR, merger.

## Done (current sprint)

- [x] **#19 — Rename `/hal` → `/pm`** — PR #24 mergée — 2026-06-17
  - Skill `/pm` créé (`plugins/hal/skills/pm/SKILL.md`), `/hal` supprimé
  - `commands/pm.md` remplace `commands/hal.md`
  - Version bumpée 0.7.2 → **0.8.0** (plugin.json + marketplace.json + SKILL.md)
  - CHANGELOG 0.8.0 entry ajoutée

- [x] **#22 — `update_contact`** — PR #23 fermée (scope mismatch) — 2026-06-17
  - Contacts sont désormais hors scope `/pm` (→ `/crm`)
  - `update_contact` sera intégré dans le skill `/crm` (issue #20)
  - hal-mcp server-side implem est prête, sera câblée dans /crm

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

## À faire après Archon #20

1. **Merger PR /crm** (skill /crm) — vérifier déclencheurs BANT + format CR + update_contact intégré
2. **Bumper CHANGELOG.md** pour la release 0.9.0 qui regroupe /crm + update_contact
3. **Issue #21** — lier projets internes ↔ opportunités — nécessite migration Supabase (`parent_project_id` FK) + discussion Option A/B/C

## Backlog

- [ ] **#21** — lien projets internes ↔ opportunités (migration Supabase Option A recommandée)
- [ ] **#13** — Connexion Gemini Enterprise (console steps manuels — voir issue)
- [ ] schema-contract.json — cross-repo sync anchor (hal v0.3.0+)
