# STATUS — bluegreen-marketplace

Last updated: 2026-06-17

## Current Focus

**hal v0.7.2 — stable.** Prochaine étape : hal-crm ou nouveau sprint à définir.

## In Progress

- (rien)

## Done (current sprint)

- [x] **docs: refs Claude connector mises à jour** — `connectors-and-skills.md` : anciens liens `support.claude.com` / `code.claude.com` remplacés par `claude.com/docs/connectors/building` + `/authentication` ; skill `mcp-server-dev` Anthropic ajouté en référence — 2026-06-17

- [x] **update_sprint wiring — hal v0.7.2** — `update_sprint` ajouté dans la table de routage NL→MCP ("renomme le sprint", "change le statut du sprint en X"…). Section "Sprint resolution" complétée : params + valeurs de statut valides. `.mcp.json` bumped 0.1.0 → 0.2.1. 3-field version sync : hal 0.7.1 → 0.7.2. — 2026-06-15

- [x] **PR #14 — guide multi-provider connector & skills (`docs/connectors-and-skills.md`)** — Claude / Gemini / OpenAI install guide, matrice provider, gotchas OAuth Gemini Enterprise, §3b Codex ajouté, lien mort corrigé, warnings sécurité — 2026-06-14

- [x] **WP-C — `/hal tasks --tag <value>` + tags dans output (PR #15 · v0.7.1)** — flag `--tag` entre en explicit-query mode, passe `tags=[value]` à `list_tasks` v39, affiche `#tag1 #tag2` sur chaque ligne task/project, vocabulary unifié documenté dans README + `plugins/hal/README.md`. Review : 1 HIGH + 3 MEDIUM + 2 LOW fixés, 0 blocker — 2026-06-14

- [x] **Loop 2 — `/hal tasks` daily-usable v0.7.0** — PR #12 mergée (b83f75c), PR #11 fermée — 2026-06-11
  - Résolution workspace via `whoami` (défaut `blue-green`, plus de config client)
  - `/hal tasks` défaut = **sprint courant** (`list_sprints(status="actuel")`) ; aucun sprint → message explicite + fallback tâches ouvertes (jamais de board vide)
  - Couvre `blue-green` (business) + `renaud` (perso) ; flags `--status` / `--project` / `--all` / `--mine`
  - NL edit `update_task` (attributs) + 3 writers à responsabilité unique (status / sprint / attributs) ; corrige les claims stale "no `list_sprints` / `update_task`"
  - Skill `hal` 0.5.0 → 0.7.0 ; plugin = marketplace = 0.7.0
  - 5/5 critères d'acceptation validés live contre sprints seedés
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
- [x] hal plugin v0.2.0 — PR #10 mergée — 2026-06-05
  - Skill `/hal update` réécrit : Obsidian → Supabase via hal-mcp (zéro script Python)
  - `hal_update.py` supprimé
  - README + CLAUDE.md nettoyés (refs Obsidian supprimées)
- [x] hal plugin v0.4.0 — 2026-06-06
  - Skill `edifice` 0.2.0 → 0.3.0 : commande `/edifice list` (pur MCP, zéro script)
  - Fix plugin.json + marketplace.json : `0.2.0` → `0.4.0` (gap 0.3.0 comblé)
  - CHANGELOG entry `[0.4.0]` prependé
- [x] hal plugin v0.5.0 — 2026-06-08
  - Skill `hal` 0.3.0 → 0.4.0 : commande `/hal list [workspace]` (pur MCP, zéro script)
  - plugin.json + marketplace.json : `0.4.0` → `0.5.0`
  - CHANGELOG entry `[0.5.0]` prependé
- [x] hal plugin v0.6.0 — 2026-06-08
  - `commands/hal.md` + `commands/edifice.md` : `/hal` et `/edifice` comme slash commands directs
  - MCP pre-flight check dans skills hal (0.4.1) + edifice (0.3.1)
  - `docs/skills-mcp-guide.md` : référence skills vs commands, MCP, cross-platform
  - CLAUDE.md mis à jour : structure + note skills vs commands

## Backlog

- [ ] schema-contract.json — cross-repo sync anchor (hal v0.3.0+)
