# STATUS — bluegreen-marketplace

Last updated: 2026-07-28

## Current Focus

Chantier **Edifice front as an artifact** (#50) livré en v1 : socle `ui/` (#51/PR #52), artefact lecture seule (#50/PR #53), puis correction de l'hydratation du connecteur trouvée au premier test réel en Cowork (#54/PR #55). La route `/edifice front` est désormais fonctionnelle end-to-end.

Prochaine étape sur ce chantier : phase 2 (écriture — `push_mission_context` depuis l'artefact, #49), pas encore lancée.

En arrière-plan : triage — `update_interaction` (#27 dual-PR hal+skill), smoke test de rendu (#44), Gemini Enterprise (#13 manuel), projet↔opportunité (#21 migration).

## Done (2026-07-28)

- [x] **#54 — `/edifice front` : UUID connecteur lu via `ListConnectors`** — PR #55 mergée — hal v0.11.2 — 2026-07-28
  - L'étape 2 du skill dérivait l'UUID des noms d'outils MCP de la session, en supposant la convention `mcp__<uuid>__<tool>`. **Cowork expose hal-mcp sous son nom court** (`mcp__hal-mcp__list_edifice_missions`) : le meta block était hydraté avec `hal-mcp` et l'artefact refusait de charger.
  - Fix : `ListConnectors(keywords: ["hal"])` → `installedServerId`, le seul id que `window.cowork.callMcpTool` sait résoudre. `ToolSearch` + `ListConnectors` ajoutés à `allowed-tools` — sans eux l'étape corrigée reste bloquée par le frontmatter.
  - Aucun changement côté `ui/` : le bundle résolvait déjà correctement par suffixe depuis le meta block, seule la valeur injectée était fausse.
  - Les deux TODO « verify in Cowork » retirés — route exécutée end-to-end en session réelle, hand-off fichier → live artifact confirmé.
- [x] **#47 — Échappement XML dans les 3 renderers docx** — PR #48 mergée — hal v0.11.1 — 2026-07-28
- [x] **#50 — Artefact Cowork lecture seule pour les missions** — PR #53 mergée — hal v0.11.0 — 2026-07-28
- [x] **#51 — Socle de build Node pour les fronts artefact** (`ui/`, build single-file, `check_artifact_sync.sh` en CI) — PR #52 mergée — 2026-07-28

## Done (2026-07-27)

- [x] **Décisions d'architecture artefact** — #50 mise à jour, 3 issues créées — 2026-07-27
  - **(b)** la source du front vit ici (`ui/edifice-front/`, hors `plugins/hal/`). Un toolchain Node ne coûte rien à l'utilisateur : le clone ne tire que ce qui est commité, `node_modules/` est gitignoré.
  - **`@bluegreeno/annotation-core`** — tranche framework-agnostic d'`annotation-kit`, buildée et publiée sur GitHub Packages depuis le monorepo edifice. Le scope doit matcher l'org GitHub, d'où `@bluegreeno` et non `@edifice`.
  - **Build commité + `check_artifact_sync.sh` en CI** — l'invariant source↔output est vérifié par la machine, pas par la discipline.
  - **Cible v1 : Cowork uniquement.** Le runtime claude.ai est un runtime *différent* (API `window.claude.mcp` vs `window.cowork.callMcpTool`, fragment vs document complet) et exigerait de réenregistrer hal-mcp comme connecteur claude.ai — ce que #39 a supprimé. Non réouvert sans décision explicite.
  - Recherche complète (deux runtimes, mécanisme de packaging, bugs amont [#57398](https://github.com/anthropics/claude-code/issues/57398) / [#55788](https://github.com/anthropics/claude-code/issues/55788), plafond 16 MiB) : premier commentaire de #50.

## Done (2026-07-23)

- [x] **Pre-flight recovery corrigé** — hal v0.10.2 — 2026-07-23
  - Les 4 skills (`crm`, `pm`, `edifice`, `linkedin`) renvoyaient vers « Claude Desktop → Paramètres → Connexions → hal-mcp → Activer » sur échec du `whoami`. Ce chemin n'existe plus : le connecteur claude.ai et le serveur user manuel ont été supprimés au profit du `.mcp.json` du plugin.
  - Remplacé par `/mcp` → `plugin:hal:hal-mcp` → `authenticate`. La ligne « interface graphique uniquement, pas de commandes terminal » (spécifique à Claude Desktop, fausse dans Claude Code) est retirée.
  - **Issue #39 ouverte** : aucune des 4 skills ne déclare d'outil MCP dans son `allowed-tools`, donc aucun appel n'est pré-approuvé → une demande de permission par appel.

## In Progress

- [ ] **D1 — #27 `update_interaction`** — deux PRs séquentielles :
  1. **hal repo d'abord** : ajouter tool MCP `update_interaction(interaction_id, ...champs partiels)` dans `hal-mcp/index.ts`, sur le modèle de `update_task`/`update_sprint`. Deploy Edge Function après merge.
  2. **Ce repo ensuite** : documenter dans `plugins/hal/skills/crm/SKILL.md` le chemin lookup-par-contact+date → `update_interaction`. Lancer via Archon après deploy hal :
     ```bash
     archon workflow run skill-improve "27"
     ```

## Done (current sprint)

- [x] **#28 — Créer skill `/linkedin`** — PR #29 mergée — 2026-06-25
  - Skill `/linkedin` créé (`plugins/hal/skills/linkedin/SKILL.md`) + `commands/linkedin.md`
  - Commandes : `idea`, `backlog`, `trend` (Bright Data), `draft`, `log`
  - Zéro backend nouveau — backlog = tasks taguées `linkedin`, drafts = `save_document`
  - `project_id` vérifié nullable dans `halcrm_interactions` — aucun risque
  - README + CLAUDE.md mis à jour (dette docs PR #19/#25 soldée)
  - Version bumpée 0.9.0 → **0.10.0** (plugin.json + marketplace.json)

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

- [ ] **#13 — Gemini Enterprise** — étapes console manuelles (desktop requis). Checklist complète dans l'issue #13. Ref projet Supabase : `zgkvbjqlvebttbnkklpo`.
- [ ] **#21 — projets ↔ opportunités** — décision Option A/B/C non prise. **Recommandation : Option A** (FK `parent_project_id` nullable dans `halcrm_projects`). Nécessite migration Supabase + expose dans hal-mcp + update skills `/crm` et `/pm`. Planifier en session dédiée.
- [ ] schema-contract.json — cross-repo sync anchor (hal v0.3.0+)
