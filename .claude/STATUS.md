# STATUS — bluegreen-marketplace

Last updated: 2026-08-18

## Current Focus

### 2026-08-18 — `pm` 0.1.7 : deux ruptures de contrat suivies le jour même

**`sprint-planner` a suivi le déplacement de `gmail-mcp`** ([#79](https://github.com/BluegReeno/bluegreen-marketplace/issues/79) → PR #80).
`renaud-marketplace#96` a déplacé le connecteur de `jobsearch` vers `briefing`, donc le préfixe
est passé à `mcp__plugin_briefing_gmail-mcp__*`. `sprint-planner` était le **seul appelant hors
de ce dépôt-là** (SKILL.md l.16, 212, 216) : la PR d'en face ne pouvait pas l'atteindre. Fusionné
**avant** elle, pour qu'il n'existe aucune fenêtre où l'étape « alertes LinkedIn » pointe dans le
vide. ⚠️ La CI vérifie que `allowed-tools` est *présent*, jamais que ses noms *résolvent* — un
préfixe mort passe au vert (défaut `rm#88`, 2026-08-09).
**Conséquence à retenir** : `pm` dépend désormais de `briefing` installé, plus de `jobsearch`.

**`list_tasks` ne renvoie plus un tableau** ([#81](https://github.com/BluegReeno/bluegreen-marketplace/issues/81) → PR #82),
mais `{tasks, total, returned, truncated}` (hal#105/#107). Quatre fichiers suivis : `pm`,
`commands/pm.md`, `sprint-planner`, `sprint-review`. Le drapeau est **exploité, pas toléré** :
`sprint-review` affiche `⚠️ Résultat tronqué : <returned>/<total> tâches affichées` au lieu de
publier des chiffres faux — il lisait jusqu'ici 100 lignes sur les 111 du workspace `blue-green`,
les plus anciennes tombant en premier.

⛔ **hal-mcp n'est pas encore déployé** — [hal#108](https://github.com/BluegReeno/hal/issues/108)
tient le verrou tant que l'artefact Command Center n'est pas republié. Ces skills sont prêts pour
le nouveau format, donc ils ne fonctionneront correctement qu'**après** ce déploiement.


**Refonte de l'agencement des plugins — brief complet dans [#66](https://github.com/BluegReeno/bluegreen-marketplace/issues/66), prêt à lancer.**

Le plugin `hal` (0.11.6, seul plugin du dépôt) est un monolithe qui sert trois audiences disjointes. Déclencheur : Cris (The Rosas Laborbe Company, workspace `rosaslaborbe`) a besoin de `/pm` et de rien d'autre — aujourd'hui elle devrait installer aussi `/crm`, `/linkedin`, `/edifice` et leurs 10 scripts Python. Même problème pour IC Ingénieurs Conseils, qui prend le monolithe pour `/edifice`.

Cible : `hal` 0.12.0 réduit au connecteur `.mcp.json`, plus `pm` / `gtm` / `edifice` en 0.1.0. Le découpage suit l'**audience installable**, pas le thème.

**Exécution — révisée le 2026-08-02, ne pas lancer archon.** `skill-improve` est écarté après lecture du YAML : son node `implement` bump le frontmatter `version:` de chaque `SKILL.md` et `verify-all-versions` le réapplique — or ce champ a été supprimé de la convention, le workflow le réintroduirait. Il lit aussi `plugins/<plugin>/skills/` pour des plugins qui n'existent pas encore, ne sait pas créer un plugin (ni `plugin.json` neuf, ni `CHANGELOG.md`, ni entrée marketplace), ignore `release.sh`, et est mono-dépôt par construction. Le chantier est du `git mv` + repointage + `release.sh` ×4 : **session directe**.

Trois étapes, ordre imposé : (1) PR sur `bluegreen-marketplace` — L1→L6, en **copiant** `sprint-planner`/`sprint-review` depuis `renaud` ; (2) après merge, PR sur `renaud-marketplace` — retrait des deux skills de `briefing`, bump 0.12.0, `generate_improve_map.py` ; (3) purge du cache `~/.claude/plugins/cache/`, test des trois profils, `BLUEGREEN_MAP.md` + les deux `STATUS.md`. La duplication temporaire est sûre ; supprimer avant que `pm` existe ne l'est pas.

**Plan d'exécution découpé en 7 sessions : [`.claude/tasks/plugin-split.md`](tasks/plugin-split.md)** — préconditions, étapes, commandes de vérification et critère de sortie par session, plus 6 invariants et un journal de reprise. **S1 à S6 faites le 2026-08-02 — le code est livré et publié des deux côtés.** Les deux PR sont **mergées** (en squash) : [#67](https://github.com/BluegReeno/bluegreen-marketplace/pull/67) ici, [renaud-marketplace#81](https://github.com/BluegReeno/renaud-marketplace/pull/81) là-bas, qui retire `sprint-planner` / `sprint-review` de `briefing` (0.12.0). Les deux branches de travail sont supprimées, les deux `main` propres et alignés sur `origin`. **Rien n'est en attente côté code.**

Il ne reste que **S7 — la validation terrain, à faire à la main par Renaud.** Contexte : il a **purgé ses skills et plugins Cowork le 2026-08-02** pour repartir d'une base propre, et testera dans une nouvelle session sur ce dépôt. Donc une commande absente au test signifie « plugin pas installé », pas nécessairement une régression du découpage.

**Ce qui est publié et installable** (vérifié sur `origin/main`, pas sur un working tree) :

| Plugin | Version | Commandes | Connecteur |
|--------|---------|-----------|------------|
| `hal` | 0.12.0 | aucune | `.mcp.json` — le seul du dépôt |
| `edifice` | 0.1.0 | `/edifice` | — |
| `gtm` | 0.2.0 | `/crm`, `/linkedin` | — |
| `pm` | 0.1.5 | `/pm`, `/sprint-planner`, `/sprint-review` | — |

Compteur marketplace **0.10.21** (relu dans `marketplace.json` après les merges du 2026-08-17 ; `gtm` **0.2.0** via #76, `pm` **0.1.5** via #75 → #77 → #78).

⚠️ **Deux publications tiennent dans un seul incrément, et rien ne l'a signalé.** #75 et #76 partaient toutes deux de 0.10.18 et écrivaient toutes deux 0.10.19 : git a fusionné sans conflit, puisque la modification était *identique*. La convention du dépôt est +1 par publication (0.10.16 → .17 → .18). Le contenu de 0.10.19 est juste — il porte les deux changements — donc rien n'a été rebumpé, mais **deux `skill-improve` en vol simultané produisent cette fusion silencieuse à chaque fois**. `check_version_sync.sh` ne la voit pas : il contrôle les versions de plugin contre leur CHANGELOG, pas le compteur top-level. Côté `renaud-marketplace` : top-level 0.6.16, `briefing` 0.12.0 réduit à `morning-briefing` + `mail-triage`.

**Protocole de test S7** — `hal` s'installe toujours en premier, c'est lui qui enregistre le connecteur que les trois autres appellent :

```
/plugin install hal@bluegreen-marketplace
/plugin install edifice@bluegreen-marketplace
/plugin install pm@bluegreen-marketplace
/plugin install gtm@bluegreen-marketplace
```

1. **Purger `~/.claude/plugins/cache/bluegreen-marketplace/`** avant tout — il peut contenir un `hal` déjà vidé de ses skills, et le test porterait alors sur l'ancien contenu.
2. **Profil Cris** (`hal` + `pm` seuls) : créer une tâche dans `rosaslaborbe`, et vérifier qu'**aucune commande Blue Green n'apparaît**. `sprint-planner` doit s'arrêter en **fail-closed** sur `sprints_enabled=false` — comportement voulu (D7), pas une régression.
3. **Profil IC** (`hal` + `edifice` seuls) : générer un rapport de mission de bout en bout. **C'est le seul test qui exerce le resolver `PLUGIN_DIR` repointé** — le morceau le plus risqué du découpage.
4. **Profil Renaud** : les 8 plugins, `whoami` depuis un skill de chacun des nouveaux plugins.
5. Les skills changent de namespace (`briefing:sprint-planner` → `pm:sprint-planner`) ; les commandes `/sprint-planner` et `/sprint-review`, elles, ne bougent pas.

Puis **`BLUEGREEN_MAP.md`** — 8 plugins, versions réelles, table des skills — commité et poussé **depuis `archon-workflows`** (le fichier est un symlink), et la **clôture de #66**.

Les quatre plugins sont en place et versionnés : `hal` **0.12.0** réduit à ses quatre fichiers (`plugin.json`, `.mcp.json`, `README.md`, `CHANGELOG.md`), `edifice` / `gtm` / `pm` en **0.1.0**, compteur marketplace à **0.10.16**. Le découpage est terminé de bout en bout — fichiers, versions, documentation, et les deux PR mergées.

Deux faits qui allègent le chantier, vérifiés au cadrage : `hal` gardant son nom et restant porteur unique du connecteur, le préfixe `mcp__plugin_hal_hal-mcp__` ne bouge pas — **aucun `allowed-tools` à réécrire dans les 16 skills du portfolio** ; et `pm`, `crm`, `linkedin` ne référencent aucun script ni template, leur extraction est un déplacement pur. Seul `edifice` porte du lourd.

**`/edifice front` (#60) reste ouvert et non résolu**, en pause derrière la refonte. Attention : l'exploration `ui/edifice-front/` non aboutie (415 insertions sur `cowork-mcp.ts`, `mcp-data-adapter.ts`, `ErrorBanner`, `MissionDetail`) a été déplacée telle quelle sur la branche **`wip/edifice-front-mcp`** pour rendre `main` propre — elle n'est pas perdue, elle n'est plus dans le working tree.

### Détail #60 — `/edifice front` (en pause, non résolu)

La route est publiée depuis v0.11.0 et n'a jamais chargé une seule mission. Quatre correctifs livrés le 2026-07-28 (v0.11.2 → v0.11.4), chacun réel, aucun suffisant : l'artefact charge, résout ses ids, émet l'appel — et Cowork le refuse (`Tool "mcp__…__list_edifice_missions" is not in this artifact's mcp_tools allowlist`).

**Cause trouvée en fin de journée** (via une session Cowork interrogée sur le « Command Center », seul artefact connecté qui fonctionne) : l'allowlist `mcp_tools` est déclarée **à la création de l'artefact**, comme paramètre de l'outil de publication. Ni le bloc `cowork-artifact-meta` du HTML, ni les littéraux du bundle ne l'alimentent. Notre skill écrit un fichier HTML et demande à l'utilisateur de l'ouvrir : personne ne déclare jamais l'allowlist. Il manque aussi l'appel hal préalable dans la session, qui approuve le connecteur pour l'artefact.

Recette complète, état d'avancement et inconnue restante (signature de l'outil de publication) : **#60**. Ne pas rouvrir la piste « bloc meta dans le préambule » — PR #59 fermée sans merge, hypothèse fausse.

Le reste du chantier #50 est acquis : socle `ui/` (#51/PR #52), artefact lecture seule (#50/PR #53), toolchain et CI en place. Phase 2 (écriture — `push_mission_context` depuis l'artefact, #49) reste bloquée derrière #60.

En arrière-plan : triage — `update_interaction` (#27 dual-PR hal+skill), smoke test de rendu (#44), Gemini Enterprise (#13 manuel), projet↔opportunité (#21 migration).

## Done (2026-08-17)

- [x] **#68 — unicité du sprint courant, côté skill** — PR [#78](https://github.com/BluegReeno/bluegreen-marketplace/pull/78) mergée — 2026-08-17
  - Moitié skill de [hal#99](https://github.com/BluegReeno/hal/issues/99) (hal-mcp **v61**). `pm` 0.1.4 → **0.1.5**, compteur **0.10.21**.
  - Le rollover passe désormais par `transition_sprint` (une transaction) au lieu de deux `update_sprint` — que la contrainte d'unicité rejetterait maintenant. Au passage, le run a trouvé que l'ancienne boucle démotait le sprint sortant vers **`passes`** au lieu de `dernier` : sémantiquement faux, invisible jusqu'ici.
  - ⚠️ **Le prochain numéro de sprint vient de `MAX(sprint_number) + 1`, jamais du sprint courant + 1.** Le dédoublonnage du 2026-08-14 a renuméroté vers des numéros libres plutôt que resequencé (le numéro figure dans le nom : `BG-31`), donc la suite a un trou : `blue-green` saute de 31 à **33**, `renaud` a 8 et 9 pris.

- [x] **#69 — distinguer une tâche annulée d'une tâche faite** — PR [#77](https://github.com/BluegReeno/bluegreen-marketplace/pull/77) mergée — 2026-08-17
  - Moitié skill de [hal#98](https://github.com/BluegReeno/hal/issues/98). `pm` 0.1.3 → **0.1.4**.
  - **Trois buckets, pas deux** : `cancelled` est exclu du **dénominateur** du taux de complétion dans `sprint-review` *et* `sprint-planner`, affiché sur une ligne à part, et **jamais reporté** au sprint suivant. Mesuré en production : `done` est passé de 158 à 128 une fois les 30 annulations migrées — un cinquième du chiffre annoncé.
  - La convention `❌ ANNULÉ (date, motif) — ` n'est **pas** documentée : elle est explicitement interdite dans le SKILL.md. La migration l'a supprimée des 30 titres ; la redocumenter l'aurait fait renaître en doublon du vrai statut.

- [x] **Les quatre issues du plan d'intégrité sont livrées** — `#70`, `#27`, `#69`, `#68`, chacune après le déploiement de sa moitié backend. Reste le re-run d'`issue-portfolio-plan`.

## Done (2026-08-14)

- [x] **#27 — `/crm log update` : corriger une interaction loguée** — PR [#76](https://github.com/BluegReeno/bluegreen-marketplace/pull/76) mergée — 2026-08-14
  - Moitié skill de [hal#100](https://github.com/BluegReeno/hal/issues/100), déployée le matin même (hal-mcp **v60**, 32ᵉ tool). `gtm` 0.1.0 → **0.2.0**.
  - `allowed-tools` vérifié **contre les 32 `registerTool` du bundle déployé**, pas de mémoire — c'est le piège `rm#88` : la CI contrôle que `allowed-tools` est présent, jamais que ses noms résolvent.
  - ⚠️ **Trou fonctionnel confirmé, non comblé** : il n'existe aucun `list_interactions`. Une interaction n'est donc corrigeable que dans la session qui l'a loguée — or corriger *après coup* est le cas d'usage même de #27. Contournement livré : `/crm log` affiche désormais l'`interaction_id`, et `/crm log update` refuse de deviner un id absent du contexte. Une issue `hal` (`list_interactions`) reste à ouvrir.

- [x] **#70 — `priority` validée contre un vocabulaire fermé** — PR [#75](https://github.com/BluegReeno/bluegreen-marketplace/pull/75) mergée — 2026-08-14
  - Moitié skill de [hal#97](https://github.com/BluegReeno/hal/issues/97), déployée le matin même. `pm` 0.1.2 → **0.1.3**. Le skill normalise le français (« priorité haute » → `high`) **en amont** d'un serveur qui n'accepte que la forme canonique.
  - ⚠️ **Le run a documenté un état du monde périmé de six heures** — « pas de validation serveur », « fix hal-mcp hors scope » — parce qu'il a lu le corps de l'issue, écrit avant le déploiement. Corrigé dans `b538795`. **Leçon : `skill-improve` prend un numéro d'issue, pas un prompt — le corps de l'issue est le seul canal. Le corriger avant de lancer n'est pas optionnel.** `bgm#27`, dont le corps avait été remis à jour d'abord, est sorti juste du premier coup.

- [x] **#73 — les comparaisons de dates de `sprint-planner` / `sprint-review` échouaient en silence** — PR [#74](https://github.com/BluegReeno/bluegreen-marketplace/pull/74) mergée — 2026-08-14
  - `[ "$a" \>= "$b" ]` n'est pas un opérateur : `test` recevait `">="` comme troisième argument et la comparaison ne matchait jamais. 12 occurrences sur 6 lignes, dans les deux skills. Remplacées par la vraie négation `[[ ! "$a" < "$b" ]]`.
  - **Vérifié fonctionnellement, pas seulement relu** : rejoué contre les 102 notes réelles du vault sur la fenêtre 07-27 → 08-02, l'ancienne forme retourne **0** candidature, la nouvelle **7** (OpenAI, Celonis, Arcom, OWKIN, OCDE, Streem, Kpler).
  - `pm` 0.1.1 → **0.1.2**, marketplace top-level 0.10.17 → **0.10.18**, CHANGELOG à jour (three-file sync vérifié).
  - Le champ `version:` dans le frontmatter des `SKILL.md` n'existe plus dans la convention du dépôt — ce n'était pas un oubli du run.

## Done (2026-08-02)

- [x] **S6 — `briefing` 0.12.0 sur `renaud-marketplace`, PR [#81](https://github.com/BluegReeno/renaud-marketplace/pull/81) ouverte (#66)** — 2026-08-02
  - `sprint-planner`, `sprint-review` et leurs deux commandes retirés de `briefing` ; `briefing` 0.11.0 → **0.12.0**, compteur marketplace 0.6.15 → 0.6.16. **Vérifié avant de supprimer** : les quatre fichiers étaient **identiques** aux copies faites en S2 — le dernier commit qui les touchait (`0999867`, 2026-08-01) est antérieur à la copie, donc aucun delta à reporter.
  - **6.4 tranchée** (le plan la disait « non vérifiée ») : ni `morning-briefing` ni `mail-triage` ne référencent les deux skills partis. Rien à repointer.
  - **Une vraie surprise, qui aurait rendu la CI rouge quoi qu'il arrive** : `generate_improve_map.py` énumérait `plugins/<name>/skills` pour **chaque** plugin distant et mourait sur l'échec — or `hal` n'a plus de `skills/`, l'API répond 404. Le job CI lance ce script puis `git diff --exit-code`. Corrigé : un 404 sur ce chemin ne produit plus de lignes (comme le fait déjà le côté local) ; **seul** « HTTP 404 » est traité ainsi — un token invalide ou un dépôt renommé abort toujours — et un 404 sur un fichier requis meurt encore. Deux tests hors-ligne épinglent les deux moitiés. Les 5 jobs de CI passent.
  - **Signalé, non corrigé** (hors périmètre, à trancher) : `scripts/test_release.sh` de `renaud-marketplace` échoue sur son « happy path », **et échouait déjà sur `main`** ; aucun job de CI ne le lance. Cause : `check_version_sync.sh:69` boucle sur `plugins/*/skills/*/SKILL.md` et passe le motif littéral à Python quand le glob ne correspond à rien — la fixture n'a aucun `SKILL.md`. **Même famille de défaut que le bug ci-dessus** : l'outillage suppose qu'un plugin a des skills, ce qui n'est plus vrai depuis que `hal` est un connecteur seul.

- [x] **S5 — documentation repointée, PR [#67](https://github.com/BluegReeno/bluegreen-marketplace/pull/67) ouverte (#66)** — 2026-08-02
  - **`CLAUDE.md`**, le plus gros morceau : table des quatre plugins **par audience installable**, « Repo Structure » réécrite de fond en comble, section versioning passée au per-plugin (le check itère sur `plugins/*/`, un plugin cassé bloque **toutes** les releases), chemins artefacts sur `plugins/edifice/`. Deux règles que le découpage rend critiques y sont désormais écrites noir sur blanc : **créer un plugin = créer ses trois fichiers d'un coup**, et **`hal` est le seul porteur d'un `.mcp.json`** (en ajouter un ailleurs créerait un second préfixe d'outils, que tous les `allowed-tools` contredisent).
  - **`README.md`** et **`docs/INSTALL.md`** : `hal` en socle requis, puis les trois installs, avec la table par persona (IC / projets-sprints / Blue Green complet) et un encart de migration 0.11.x.
  - **Quatre docs vivantes hors périmètre du plan**, trouvées au grep de sortie : `connectors-and-skills.md` (installs + symlinks `.agents/skills/`), `skills-mcp-guide.md`, `cowork-artifact-publishing.md`, `artifact-front-ends.md`. `skills-mcp-guide.md` portait en plus **deux affirmations devenues fausses** — le `version:` par skill (champ supprimé de la convention, exactement ce qui a fait écarter `skill-improve`) et la famille `/hal list|tasks|update` qui n'existe plus. Corrigées.
  - **Laissés tels quels** : `docs/_archive/`, `docs/brief.md`, `docs/features/ops-1-purge-ci.md` — comptes rendus datés, les réécrire falsifierait l'histoire. Le grep de sortie du plan les ignorait, d'où un résidu attendu et non un écart.
  - **Un constat à trancher, pas tranché ici** : le bundle `scripts/obsidian/` a suivi `edifice` parce qu'il vivait sous `plugins/hal/scripts/`, mais **aucun skill du dépôt ne le référence** — les seules mentions restantes sont ses propres fichiers et une archive. Noté dans `CLAUDE.md` avec la consigne de ne pas le supprimer sur cette seule base.
  - **Vérifié avant la PR** : `check_version_sync.sh` vert, `check_artifact_sync.sh` vert sur les deux artefacts (build-stamp rétabli depuis l'index, comme en S1), 75 tests OK.
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
- [ ] **#21 — projets ↔ opportunités** — **décision prise le 2026-07-29 : Option A** (FK `parent_project_id` nullable, self-referencing), actée en commentaire sur [#21](https://github.com/BluegReeno/bluegreen-marketplace/issues/21) lors de la revue du portfolio plan (`archon-workflows#10`), B et C écartées avec leurs raisons. Cette ligne a dit « décision non prise » pendant deux semaines de plus — corrigé le 2026-08-14. La moitié backend est **filée** ([hal#86](https://github.com/BluegReeno/hal/issues/86), scope + acceptance criteria complets), donc la paire n'est plus bloquée : elle attend seulement d'être exécutée, hal d'abord. Restent deux choix internes, tous deux déjà recommandés dans l'issue : `ON DELETE SET NULL` et un seul niveau d'imbrication.
- [ ] schema-contract.json — cross-repo sync anchor (hal v0.3.0+)
