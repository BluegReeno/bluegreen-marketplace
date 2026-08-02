# STATUS — bluegreen-marketplace

Last updated: 2026-08-02

## Current Focus

**Refonte de l'agencement des plugins — brief complet dans [#66](https://github.com/BluegReeno/bluegreen-marketplace/issues/66), prêt à lancer.**

Le plugin `hal` (0.11.6, seul plugin du dépôt) est un monolithe qui sert trois audiences disjointes. Déclencheur : Cris (The Rosas Laborbe Company, workspace `rosaslaborbe`) a besoin de `/pm` et de rien d'autre — aujourd'hui elle devrait installer aussi `/crm`, `/linkedin`, `/edifice` et leurs 10 scripts Python. Même problème pour IC Ingénieurs Conseils, qui prend le monolithe pour `/edifice`.

Cible : `hal` 0.12.0 réduit au connecteur `.mcp.json`, plus `pm` / `gtm` / `edifice` en 0.1.0. Le découpage suit l'**audience installable**, pas le thème.

**Exécution — révisée le 2026-08-02, ne pas lancer archon.** `skill-improve` est écarté après lecture du YAML : son node `implement` bump le frontmatter `version:` de chaque `SKILL.md` et `verify-all-versions` le réapplique — or ce champ a été supprimé de la convention, le workflow le réintroduirait. Il lit aussi `plugins/<plugin>/skills/` pour des plugins qui n'existent pas encore, ne sait pas créer un plugin (ni `plugin.json` neuf, ni `CHANGELOG.md`, ni entrée marketplace), ignore `release.sh`, et est mono-dépôt par construction. Le chantier est du `git mv` + repointage + `release.sh` ×4 : **session directe**.

Trois étapes, ordre imposé : (1) PR sur `bluegreen-marketplace` — L1→L6, en **copiant** `sprint-planner`/`sprint-review` depuis `renaud` ; (2) après merge, PR sur `renaud-marketplace` — retrait des deux skills de `briefing`, bump 0.12.0, `generate_improve_map.py` ; (3) purge du cache `~/.claude/plugins/cache/`, test des trois profils, `BLUEGREEN_MAP.md` + les deux `STATUS.md`. La duplication temporaire est sûre ; supprimer avant que `pm` existe ne l'est pas.

**Plan d'exécution découpé en 7 sessions : [`.claude/tasks/plugin-split.md`](tasks/plugin-split.md)** — préconditions, étapes, commandes de vérification et critère de sortie par session, plus 6 invariants et un journal de reprise. **S1 à S4 faites le 2026-08-02** ; prochaine session : **S5 (documentation du dépôt puis ouverture de la PR #1)** — `CLAUDE.md` (16 occurrences de `plugins/hal/`, la section « Repo Structure » à réécrire entièrement), `README.md` (section « Available plugins » + les trois chemins d'installation par persona), `docs/artifact-front-ends.md` (3 occurrences), puis la PR vers `main` sur la branche `refactor/plugin-split`. **C'est le premier passage réel de la CI** — version sync, artifact sync (déclenché par le déplacement d'`artifacts/`) et les tests. ⚠️ Ne pas merger sans avoir lu le diff de `CLAUDE.md` : c'est lui qui pilote les sessions suivantes. Aucune CI ne tourne dessus — `ci.yml` ne se déclenche que sur `pull_request` et sur `push` vers `main` — et **la PR ne s'ouvre qu'en S5**, quand le dépôt redevient cohérent : l'état intermédiaire est fonctionnellement cassé, mais toujours valide pour `check_version_sync.sh`.

Les quatre plugins sont en place et versionnés : `hal` **0.12.0** réduit à ses quatre fichiers (`plugin.json`, `.mcp.json`, `README.md`, `CHANGELOG.md`), `edifice` / `gtm` / `pm` en **0.1.0**, compteur marketplace à **0.10.16**. Le découpage est terminé, code et versions ; ne reste que la documentation du dépôt, puis la PR (S5).

Deux faits qui allègent le chantier, vérifiés au cadrage : `hal` gardant son nom et restant porteur unique du connecteur, le préfixe `mcp__plugin_hal_hal-mcp__` ne bouge pas — **aucun `allowed-tools` à réécrire dans les 16 skills du portfolio** ; et `pm`, `crm`, `linkedin` ne référencent aucun script ni template, leur extraction est un déplacement pur. Seul `edifice` porte du lourd.

**`/edifice front` (#60) reste ouvert et non résolu**, en pause derrière la refonte. Attention : l'exploration `ui/edifice-front/` non aboutie (415 insertions sur `cowork-mcp.ts`, `mcp-data-adapter.ts`, `ErrorBanner`, `MissionDetail`) a été déplacée telle quelle sur la branche **`wip/edifice-front-mcp`** pour rendre `main` propre — elle n'est pas perdue, elle n'est plus dans le working tree.

### Détail #60 — `/edifice front` (en pause, non résolu)

La route est publiée depuis v0.11.0 et n'a jamais chargé une seule mission. Quatre correctifs livrés le 2026-07-28 (v0.11.2 → v0.11.4), chacun réel, aucun suffisant : l'artefact charge, résout ses ids, émet l'appel — et Cowork le refuse (`Tool "mcp__…__list_edifice_missions" is not in this artifact's mcp_tools allowlist`).

**Cause trouvée en fin de journée** (via une session Cowork interrogée sur le « Command Center », seul artefact connecté qui fonctionne) : l'allowlist `mcp_tools` est déclarée **à la création de l'artefact**, comme paramètre de l'outil de publication. Ni le bloc `cowork-artifact-meta` du HTML, ni les littéraux du bundle ne l'alimentent. Notre skill écrit un fichier HTML et demande à l'utilisateur de l'ouvrir : personne ne déclare jamais l'allowlist. Il manque aussi l'appel hal préalable dans la session, qui approuve le connecteur pour l'artefact.

Recette complète, état d'avancement et inconnue restante (signature de l'outil de publication) : **#60**. Ne pas rouvrir la piste « bloc meta dans le préambule » — PR #59 fermée sans merge, hypothèse fausse.

Le reste du chantier #50 est acquis : socle `ui/` (#51/PR #52), artefact lecture seule (#50/PR #53), toolchain et CI en place. Phase 2 (écriture — `push_mission_context` depuis l'artefact, #49) reste bloquée derrière #60.

En arrière-plan : triage — `update_interaction` (#27 dual-PR hal+skill), smoke test de rendu (#44), Gemini Enterprise (#13 manuel), projet↔opportunité (#21 migration).

## Done (2026-08-02)

- [x] **S4 — les quatre versions posées (#66)** — 2026-08-02
  - `release.sh` passé quatre fois dans l'ordre du plan : `edifice`, `gtm`, `pm` en **0.1.0**, `hal` en **0.12.0**. Compteur marketplace 0.10.12 → **0.10.16**, exactement l'attendu (chaque release l'incrémente d'un PATCH). Un commit `chore(<plugin>): release v<version>` par release.
  - **Note de migration 0.12.0 collée** sous l'entrée écrite par `release.sh` et commitée à part : rupture (les quatre commandes disparaissent d'un install existant, le reste — serveur, résolution de workspace, noms d'outils — est inchangé) et table « commande → plugin à installer ».
  - **Aucun refus, aucune surprise** : le seed 0.0.0 a joué son rôle exactement comme prévu, et `check_version_sync.sh` — que chaque release relance sur **tous** les plugins avant d'écrire quoi que ce soit — est resté vert du premier au dernier appel.
- [x] **S3 — `hal` réduit au connecteur (#66)** — 2026-08-02
  - `plugins/hal/` ne contient plus que ses quatre fichiers : `plugin.json`, `.mcp.json`, `README.md`, `CHANGELOG.md`. `templates/blue-green/.gitkeep` supprimé (seule référence : une ligne de CHANGELOG de 2026-05), `skills/` et `commands/` retirés du disque, résidus `__pycache__` et `.DS_Store` nettoyés — tous gitignorés, aucun n'était suivi.
  - **README réécrit** : `hal` n'est plus décrit comme un cerveau second mais comme le socle connecteur, avec la table des trois plugins qui prennent la suite, les commandes d'installation par plugin et un encart « Upgrading from 0.11.x ».
  - **Deux corrections hors liste, l'une et l'autre devenues fausses avec le découpage** : le bloc « Versioning convention » du CHANGELOG de `hal` décrivait un versionnage par skill (le champ `version:` n'existe plus dans les `SKILL.md`) et était rédigé en français dans un document anglais — réécrit sur le modèle des trois autres plugins ; la `description` de `hal` (« second brain and mission workflow ») remplacée par celle du connecteur **dans `plugin.json` et dans l'entrée marketplace**, les deux devant rester identiques.
  - **Note de migration 0.12.0 rédigée** et posée dans le plan sous S4.5 (rupture, table « commande → plugin à installer », mention IC), prête à coller sous l'entrée que `release.sh` écrira.
  - **Vérifié** : les 4 fichiers attendus, `check_version_sync.sh` vert sur les quatre plugins, 75 tests OK.
- [x] **S2 — `gtm` et `pm` créés (#66)** — 2026-08-02 — commit `afb2058`
  - `git mv` de `crm` + `linkedin` (skills + commandes) vers `plugins/gtm/`, de `pm` vers `plugins/pm/`, les deux seedés en **0.0.0** (plugin.json + `## [0.0.0]` + entrée marketplace). `plugins/pm/` adopte en plus `sprint-planner` et `sprint-review`, **copiés** depuis `briefing` (`renaud-marketplace`) — la suppression côté `renaud` n'a lieu qu'en S6, après merge de la PR #1 : retirer avant que `pm` existe publiquement les rendrait indisponibles.
  - **Les deux vérifications annoncées par le brief se confirment** : aucun des six skills ne référence de script, de template ni de `PLUGIN_DIR` — extraction = déplacement pur — et le préfixe `mcp__plugin_hal_hal-mcp__` est intact partout (D1).
  - **Une nuance au brief** : `Skill(jobsearch-vault)` est déclaré par les **deux** skills sprint, pas seulement `sprint-planner` ; le second couplage, `mcp__plugin_jobsearch_gmail-mcp__search_emails`, lui, reste propre à `sprint-planner`. Les deux sont documentés en tête de `plugins/pm/CHANGELOG.md`, non résolus (D8), tracés dans #65.
  - **Vérifié** : `check_version_sync.sh` vert sur les quatre plugins, 75 tests OK, `plugins/hal/skills/` et `plugins/hal/commands/` vides — leur suppression est S3.1.
- [x] **S1 — `edifice` extrait dans son propre plugin (#66)** — 2026-08-02
  - `git mv` du skill, de la commande, des 11 scripts (dont `obsidian/`), templates `ic-ingenieurs`, `artifacts/` et `tests/README.md` vers `plugins/edifice/`, seedé en **0.0.0** (plugin.json + `## [0.0.0]` + entrée marketplace) — `release.sh` le promeut en 0.1.0 en S4. Commit `refactor(edifice): extract edifice into its own plugin`.
  - **Trois écarts au plan, tous consignés au journal du plan.** `tests/test_xml_escape.py:9` pointait aussi sur `plugins/hal/scripts` — 6ᵉ fichier de tests, absent de la table du brief. `organizations/ic-ingenieurs/` est **gitignoré** (config client hors dépôt public) : `git mv` refuse un répertoire source vide au sens de git — déplacé au `mv`, `.gitignore:19` repointé, c'est une famille de chemins (f) que le plan ne prévoyait pas. `check_artifact_sync.sh` réécrit le build-stamp des deux artefacts en passant (par conception : le build écrit dans le fichier que le check diffe) — rétabli depuis l'index.
  - **Vérifié** : 75 tests OK, `check_version_sync.sh` vert sur `hal` 0.11.6 + `edifice` 0.0.0, `check_artifact_sync.sh` vert sur les deux artefacts. Le grep résiduel de `plugins/hal` ne renvoie que les deux exceptions attendues — `tests/test_release.py` (fixture tmp) et `SKILL.md:601` (`.mcp.json`, `hal` garde le connecteur).
  - `HAL_PLUGIN_DIR` conservé, avec le commentaire en place qui explique pourquoi — sans quoi la prochaine session le « corrige ».
- [x] **Relecture du brief #66 contre les sources avant lancement — 5 corrections** — 2026-08-02
  - **L1, le trou qui aurait coûté une CI rouge** : quatre fichiers de `tests/` pointent en dur sur `plugins/hal/scripts` (`test_build_context.py:15`, `test_render_diagnostic.py:16`, `test_render_escaping.py:16`) et sur `plugins/hal/templates/ic-ingenieurs` (`test_edifice_render_smoke.py:24-25`). Le brief disait « les tests restent à la racine » sans dire qu'il fallait les repointer. `test_release.py` mentionne aussi `plugins/hal/` mais sur une fixture tmp qu'il crée lui-même — à ne pas toucher. Le resolver `PLUGIN_DIR` d'`edifice` a **4** points à corriger (env `HAL_PLUGIN_DIR`, cache marketplace, 3 chemins dev), pas 1 ; et `SKILL.md:600` référence `plugins/hal/.mcp.json` — occurrence qui **reste juste**, `hal` garde le connecteur.
  - **L6** : `CLAUDE.md` décrit `plugins/hal/` en 16 endroits et `docs/artifact-front-ends.md` en 3 — aucun des deux n'était listé. Laisser `CLAUDE.md` périmé invalide la session suivante.
  - **L3 — une affirmation du brief était fausse** : `sprint-planner` / `sprint-review` n'ont **aucun** resolver `PLUGIN_DIR` (zéro occurrence de `PLUGIN_DIR`, `cache`, `briefing` dans leurs `SKILL.md`). Rien à repointer, migration = déplacement pur. En revanche leurs deux fichiers de commande manquaient, et `sprint-planner` a **deux** dépendances cross-repo : `Skill(jobsearch-vault)` **et** `mcp__plugin_jobsearch_gmail-mcp__search_emails`.
  - **`skill-improve` écarté** (détail en Current Focus) et **D9 corrigée** : deux dépôts ⇒ deux PR.
  - **Confirmé au passage** : `briefing` n'a aucun `.mcp.json` — le modèle « un porteur, N consommateurs » est bien en prod ; `release.sh` et `check_version_sync.sh` itèrent sur `plugins/*/`.
- [x] **Cadrage de la refonte de l'agencement des plugins — #66 ouverte, prête à exécuter** — 2026-08-02
  - **Principe retenu** : découper par **audience installable**, pas par thème. Le découpage actuel suivait l'historique des dépôts. Cible — `hal` 0.12.0 (connecteur `.mcp.json` seul), `pm` 0.1.0 (`pm` + `sprint-planner` + `sprint-review`), `gtm` 0.1.0 (`crm` + `linkedin`), `edifice` 0.1.0 (skill + scripts + templates + artifacts + organizations).
  - **Le dépôt n'est pas un mécanisme de sécurité ici** : les deux marketplaces doivent rester publics (Claude Desktop les lit sans authentification), et le cloisonnement est déjà assuré par la RLS hal (`workspace_members`). Le grain de découpage est donc le **plugin**, pas le dépôt — on reste à deux dépôts.
  - **Un seul porteur du connecteur MCP** (décision Renaud) : le plugin `hal`, sans déduplication. Comme il garde son nom, le préfixe `mcp__plugin_hal_hal-mcp__` est inchangé et **aucun `allowed-tools` n'est à réécrire**. Modèle déjà en production : `briefing` (renaud-marketplace) consomme ce connecteur sans porter de `.mcp.json`.
  - **Rupture nette assumée** : `hal` 0.12.0 fait disparaître `/edifice`, `/pm`, `/crm`, `/linkedin` chez les installés (Renaud, IC). Deux installations concernées, note de migration à écrire.
  - **Relevé au cadrage** : `pm`, `crm` et `linkedin` ne référencent aucun script, template ou artifact — extraction = déplacement pur. Seul `edifice` porte du lourd, avec trois chemins codés en dur à repointer (`check_artifact_sync.sh`, `ci.yml` ×2, resolver `PLUGIN_DIR`). `release.sh` et `check_version_sync.sh` itèrent sur `plugins/*/` — génériques, rien à changer, mais chaque nouveau plugin a besoin de son `CHANGELOG.md` dès sa création sinon `release.sh` refuse de tourner.
  - **Direction actée, hors périmètre** : `jobsearch` est une **verticale métier** au même titre qu'`edifice` est la verticale BET terrain — la différence est qu'`edifice` est isolée alors que `jobsearch` fuit dans des skills génériques. Cible à terme : un `pm` générique que des verticales étendent. Tracé dans **#65**, bloqué par #66.
  - **`sprints_enabled=false` sur `rosaslaborbe` est correct et conservé** — le sprint est une notion professionnelle. `sprint-planner`/`sprint-review` s'y arrêtent en fail-closed, c'est le comportement voulu.
- [x] **Dépôt assaini avant lancement** — 2026-08-02
  - `a0bcc54` — `docs/PROTOCOLE-TESTS-ARTEFACTS-COWORK.md` et `docs/artefact-mcp-etat-des-lieux.md` commitées.
  - Branche `wip/edifice-front-mcp` — exploration `ui/edifice-front/` non aboutie, déplacée sans modification. **Pourquoi ce n'était pas cosmétique** : `check_artifact_sync.sh` reconstruit `ui/<name>/` et compare à l'artifact commité ; avec `ui/` modifié **et** `artifacts/` déplacé dans le même mouvement, la CI serait partie rouge sans cause attribuable.
  - `plugins/edifice-mission-report/` supprimé — vérifié avant : ne contenait que des `.DS_Store` et `__pycache__`, non suivi par git depuis le renommage en `hal` (415ad26).
  - `edifice-front_2.html` (racine, non suivi) — **supprimé le 2026-08-02.** Son en-tête le donne comme un build `edifice-front` du 28/07 08:46Z au commit `eff71c1` (#52), présent dans l'historique : reproductible depuis `ui/edifice-front`, rien d'irremplaçable. L'artifact commité porte `2a50396` / 28/07 13:04Z.

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

- [ ] **#66 — éclatement du plugin `hal` en `hal`/`pm`/`gtm`/`edifice`** — **en cours, branche `refactor/plugin-split`. S1 et S2 faites, reprendre en S3.** Ne pas lancer archon (`skill-improve` réintroduirait le champ `version:` des `SKILL.md` — détail en Current Focus) : le chantier se conduit en session directe, session par session, en suivant [`.claude/tasks/plugin-split.md`](tasks/plugin-split.md) — c'est lui qui porte les préconditions, les invariants et le journal de reprise.
  L'ordre des lots est contraint (L1 `edifice` → L2 `gtm` → L3 `pm` → L4 vider `hal` → L5 ménage → L6 doc) : vider `hal` avant d'avoir extrait ses skills les perdrait. La PR ne s'ouvre qu'en S5.
  Suites à ne pas oublier hors de ce dépôt : `python3 scripts/generate_improve_map.py` dans `renaud-marketplace` (la CI y rejette une table périmée), `briefing` 0.12.0 (il perd `sprint-planner` et `sprint-review`), et `BLUEGREEN_MAP.md`.

- [ ] **D1 — #27 `update_interaction`** — deux PRs séquentielles :
  1. **hal repo d'abord** : ajouter tool MCP `update_interaction(interaction_id, ...champs partiels)` dans `hal-mcp/index.ts`, sur le modèle de `update_task`/`update_sprint`. Deploy Edge Function après merge.
  2. **Ce repo ensuite** : documenter dans `plugins/gtm/skills/crm/SKILL.md` (déplacé depuis `plugins/hal/` en S2 de #66) le chemin lookup-par-contact+date → `update_interaction`. Lancer via Archon après deploy hal :
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
