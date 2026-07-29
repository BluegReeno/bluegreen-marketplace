# STATUS — bluegreen-marketplace

Last updated: 2026-07-28

## Current Focus

**`/edifice front` ne fonctionne toujours pas — reprise cadrée dans [#60](https://github.com/BluegReeno/bluegreen-marketplace/issues/60).**

La route est publiée depuis v0.11.0 et n'a jamais chargé une seule mission. Quatre correctifs livrés le 2026-07-28 (v0.11.2 → v0.11.4), chacun réel, aucun suffisant : l'artefact charge, résout ses ids, émet l'appel — et Cowork le refuse (`Tool "mcp__…__list_edifice_missions" is not in this artifact's mcp_tools allowlist`).

**Cause trouvée en fin de journée** (via une session Cowork interrogée sur le « Command Center », seul artefact connecté qui fonctionne) : l'allowlist `mcp_tools` est déclarée **à la création de l'artefact**, comme paramètre de l'outil de publication. Ni le bloc `cowork-artifact-meta` du HTML, ni les littéraux du bundle ne l'alimentent. Notre skill écrit un fichier HTML et demande à l'utilisateur de l'ouvrir : personne ne déclare jamais l'allowlist. Il manque aussi l'appel hal préalable dans la session, qui approuve le connecteur pour l'artefact.

Recette complète, état d'avancement et inconnue restante (signature de l'outil de publication) : **#60**. Ne pas rouvrir la piste « bloc meta dans le préambule » — PR #59 fermée sans merge, hypothèse fausse.

Le reste du chantier #50 est acquis : socle `ui/` (#51/PR #52), artefact lecture seule (#50/PR #53), toolchain et CI en place. Phase 2 (écriture — `push_mission_context` depuis l'artefact, #49) reste bloquée derrière #60.

En arrière-plan : triage — `update_interaction` (#27 dual-PR hal+skill), smoke test de rendu (#44), Gemini Enterprise (#13 manuel), projet↔opportunité (#21 migration).

## Done (2026-07-28)

- [x] **Diagnostic `/edifice front` — cause racine identifiée, correctif non livré** — #60 ouverte — 2026-07-28
  - Journée entière de diagnostic, quatre releases, aucune ne débloque. Ce qui a fait avancer : à chaque itération, faire dire à l'erreur ce qu'elle avait *observé* plutôt que ce qu'elle supposait.
  - **Leçon de méthode** : trois hypothèses successives ont été construites sur l'artefact de référence téléchargé (`docs/reference-cowork-artifact-command-center.html`), en le lisant comme un livrable. C'est un **produit de session** — l'essentiel de sa recette (déclaration `mcp_tools` à la publication) n'est pas dans son HTML et ne pouvait pas en être déduit. Interroger la session qui l'a produit a donné en une réponse ce que six heures de lecture du fichier n'avaient pas donné.
  - Erreur d'analyse à ne pas répéter : le fichier téléchargé depuis le bloc « Code · HTML » d'une conversation est la **source** écrite sur disque, pas l'artefact publié. Les differ pour « disculper la plateforme » est un raisonnement invalide.
- [x] **Erreur auto-diagnostiquante de l'artefact** — PR #57 mergée — hal v0.11.3 — 2026-07-28
  - « Outil MCP … absent du bloc meta » ne nommait ni l'artefact en cours d'exécution ni les outils réellement déclarés : un artefact obsolète de la galerie était indiscernable d'un vrai échec d'hydratation. Les distinguer a coûté un téléchargement de l'artefact publié et un diff contre la source.
  - Le message rapporte maintenant le `name` du meta et la liste `mcpTools` lue. Nouveau code `bad_meta` extrait de `no_cowork` — l'artefact *tourne* dans Cowork, l'ancienne bannière désignait la mauvaise cause.
  - **Leçon** : une erreur qui n'expose pas ce qu'elle a observé transforme un diagnostic d'une seconde en enquête. Vaut pour tout front artefact à venir.
- [x] **#54 — `/edifice front` : UUID connecteur lu via `ListConnectors`** — PR #55 mergée — hal v0.11.2 — 2026-07-28
  - L'étape 2 du skill dérivait l'UUID des noms d'outils MCP de la session, en supposant la convention `mcp__<uuid>__<tool>`. **Cowork expose hal-mcp sous son nom court** (`mcp__hal-mcp__list_edifice_missions`) : le meta block était hydraté avec `hal-mcp` et l'artefact refusait de charger.
  - Fix : `ListConnectors(keywords: ["hal"])` → `installedServerId`, le seul id que `window.cowork.callMcpTool` sait résoudre. `ToolSearch` + `ListConnectors` ajoutés à `allowed-tools` — sans eux l'étape corrigée reste bloquée par le frontmatter.
  - Aucun changement côté `ui/` : le bundle résolvait déjà correctement par suffixe depuis le meta block, seule la valeur injectée était fausse.
  - Les deux TODO « verify in Cowork » retirés — route exécutée en session réelle, hand-off fichier → live artifact confirmé (le chargement des missions, lui, reste à valider — voir Current Focus).
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
