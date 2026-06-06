# STATUS — bluegreen-marketplace

Last updated: 2026-06-05

## Current Focus

hal v0.2.0 mergé — Lot 2 (tâches/sprints) en attente des tools hal-mcp (`create_task`, `list_tasks`, `update_task`)

## In Progress

_(rien)_

## Done (current sprint)

- [x] Embed hal-mcp in plugin via `.mcp.json` — removes custom connector friction at onboarding — 2026-05-27 ✅ tested & validated (Steeve onboarding)
- [x] Bump plugin to v0.6.3 (plugin.json + SKILL.md + marketplace.json) — 2026-05-27
- [x] Fix CLAUDE.md — source repo updated, release process corrected — 2026-05-27
- [x] Architecture hal plugin : décisions prises + 2 plans rédigés — 2026-05-28
  - Un plugin `hal`, deux skills (`/edifice` + `/hal`), un MCP `hal-mcp`
  - Versioning par composant (3 chiffres, PATCH par release, MINOR pour interface)
  - `plugins/hal/scripts/obsidian/` = source de vérité unique pour scripts vault I/O
  - `/hal` v0.1.0 → Obsidian ; v0.2.0 → Supabase (après migration)
- [x] hal plugin v0.1.0 — PR #3 mergée — 2026-05-28
  - `plugins/edifice-mission-report/` → `plugins/hal/`
  - Skill `/hal update` v0.1.0 (Obsidian vault) + `hal_update.py`
  - 8 scripts obsidian-crm bundlés dans `scripts/obsidian/`
  - README, CLAUDE.md, marketplace.json, versioning policy mis à jour
- [x] hal plugin v0.1.1 — PR #4 mergée — 2026-05-28
  - Carte IGN 2D dans les rapports diagnostic (Plan C plugin natif)
  - Fix orientation photos portrait + nettoyage adresses BAN
- [x] hal plugin v0.1.2 — PR #7 mergée — 2026-06-01
  - Notes taguées `methodo:visite_terrain` / `methodo:moyens` dans section Méthodologie du rapport diagnostic
  - Issues #8 et #9 créées (warning photos désordres, unit tests)
- [x] Suppression `hal/agents/skills/hal-crm/` — scripts migrés vers `bluegreen-marketplace/plugins/hal/scripts/obsidian/` — hal PR #13 mergée 2026-05-29

## Done (current sprint)

- [x] hal plugin v0.2.0 — PR #10 mergée — 2026-06-05
  - Skill `/hal update` réécrit : Obsidian → Supabase via hal-mcp (zéro script Python)
  - `hal_update.py` supprimé
  - README + CLAUDE.md nettoyés (refs Obsidian supprimées)

## Backlog

- [ ] hal Lot 2 — tâches et sprints : prérequis `create_task` / `list_tasks` / `update_task` côté hal-mcp, puis extension du mapping skill
- [ ] schema-contract.json — cross-repo sync anchor (hal v0.3.0+)
