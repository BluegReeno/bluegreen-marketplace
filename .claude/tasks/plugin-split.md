# Plan d'exécution — refonte de l'agencement des plugins (#66)

> **Document de reprise multi-session.** Rédigé en français comme `STATUS.md` et #66, dont il est
> la déclinaison opérationnelle. Chemins, commandes et identifiants restent tels quels.

**Brief** : [#66](https://github.com/BluegReeno/bluegreen-marketplace/issues/66) — le *pourquoi*
et les décisions actées (D1–D9). Ce document est le *comment*, découpé en sessions courtes.
**Suite tracée** : #65 (verticalisation `pm`), à ne pas exécuter ici.

---

## Comment reprendre ce plan à froid

1. Lire **§ État d'avancement** — la première session non cochée est celle à faire.
2. Lire **§ Invariants** — 6 pièges, chacun coûte une CI rouge ou une régression silencieuse.
3. Exécuter la session : elle est autosuffisante (préconditions → étapes → vérification → sortie).
4. Avant de fermer : cocher, dater, remplir le **§ Journal**, commiter.

**Règle de branche** : tout se fait sur `refactor/plugin-split`, une seule branche pour les
sessions S1→S5. Chaque session finit par un commit ; l'état intermédiaire est incohérent
fonctionnellement mais **toujours valide pour `check_version_sync.sh`** (voir Invariant 6).

**Pousser est sans danger avant la PR.** `ci.yml` ne se déclenche que sur `pull_request` et sur
`push: branches: [main]` — pousser `refactor/plugin-split` ne lance aucune CI. Donc : pousser à
chaque fin de session pour ne rien perdre, et **n'ouvrir la PR qu'en S5**, quand le dépôt
redevient cohérent.

---

## État d'avancement

| # | Session | Contenu | Statut |
|---|---------|---------|--------|
| S0 | Cadrage + révision | #66 ouverte, brief vérifié contre les sources | ✅ 2026-08-02 |
| S1 | **L1 — extraire `edifice`** | la plus lourde : 5 familles de chemins | ✅ 2026-08-02 |
| S2 | **L2 + L3 — `gtm` et `pm`** | déplacements purs, léger | ✅ 2026-08-02 |
| S3 | **L4 + L5 — vider `hal`, ménage** | léger | ✅ 2026-08-02 |
| S4 | **Versions** | 4 × `release.sh`, compteur top-level | ⬜ |
| S5 | **L6 doc + PR #1** | `CLAUDE.md`, README, docs → PR `bluegreen` | ⬜ |
| S6 | **PR #2 — `renaud-marketplace`** | après merge de la PR #1 | ⬜ |
| S7 | **Validation terrain** | 3 profils, `BLUEGREEN_MAP`, `STATUS` ×2 | ⬜ |

S2 et S3 sont courtes — enchaînables dans une même session si le temps le permet.

---

## Décision tranchée — `HAL_PLUGIN_DIR` reste `HAL_PLUGIN_DIR`

**Tranché par Renaud le 2026-08-02 : on garde le nom.** La variable d'environnement du resolver
(`skills/edifice/SKILL.md:24`) porte le nom de l'ancien plugin, mais c'est un échappatoire de dev,
pas une interface publique. La renommer casserait tout shell qui l'a exportée (`.zshrc`, sandbox
Cowork) et ajouterait une rupture gratuite à une refonte qui en a déjà une.

→ **Ne pas toucher la ligne 24.** Y poser un commentaire d'une ligne expliquant pourquoi le nom
survit au découpage, sans quoi la prochaine session la « corrigera ». À rouvrir dans #65 si le
sujet revient.

---

## Invariants — à relire avant chaque session

**1. Ne pas toucher `tests/test_release.py`.** Il mentionne `plugins/hal/` mais construit sa
propre fixture dans un `tmp` — il ne lit jamais l'arborescence réelle. Le « corriger » casserait
un test qui passe.

**2. Deux mentions de `hal` dans `skills/edifice/SKILL.md` qui restent justes.**
La ligne **600** référence `plugins/hal/.mcp.json` — `hal` conserve le connecteur. La ligne **24**
garde la variable `HAL_PLUGIN_DIR` (décision ci-dessus). Un `sed` global casserait les deux.

Conséquence de 1 et 2 : **jamais de `sed` global**. Chaque occurrence se traite à la main.

**3. `build-artifact.mjs` et `check_artifact_sync.sh` se repointent ensemble.** Le script de
build écrit **directement dans le fichier commité** (`check_artifact_sync.sh:34-41` l'explique) ;
le check snapshote l'avant, rebuild, et diffe. Si l'un pointe sur `plugins/hal/artifacts` et
l'autre sur `plugins/edifice/artifacts`, le check ne compare plus rien de significatif. Les deux
lignes changent dans le même commit.

**4. `release.sh` exige un working tree propre et fait `git add -A`.** Commiter tout le contenu
**avant** de lancer la moindre release (d'où S4 séparée de S1–S3).

**5. `release.sh` exige que l'entrée marketplace existe déjà.** Il refuse un plugin absent de
`marketplace.json` (« no matching entry »). D'où le **seed en 0.0.0** décrit ci-dessous.

**6. `check_version_sync.sh` doit rester vert à la fin de chaque session.** Il itère sur
`plugins/*/.claude-plugin/plugin.json` et exige pour chacun : entrée `marketplace.json` présente,
version identique, **et** une entrée `## [<version>]` dans son `CHANGELOG.md`. Donc un plugin
créé sans ces trois choses casse *toutes* les releases suivantes, y compris celles des autres
plugins. **Créer un plugin = créer les trois d'un coup.**

### Le seed 0.0.0 — pourquoi

Chaque plugin neuf est créé en **0.0.0** (plugin.json + `## [0.0.0] — seed` dans son CHANGELOG +
entrée marketplace à 0.0.0), puis promu en 0.1.0 par `release.sh` en S4. Deux bénéfices : le
dépôt reste sync-valide à chaque commit intermédiaire (invariant 6), et c'est `release.sh` qui
pose la version réelle, l'entrée CHANGELOG datée **et** l'incrément du compteur top-level — au
lieu de trois éditions manuelles désynchronisables.

---

## S1 — L1 : extraire `edifice`

**Préconditions** : `main` propre.

```bash
git checkout -b refactor/plugin-split
```

### Étapes

- [x] **1.1 — Déplacer le contenu** (`git mv`, pour conserver l'historique) vers
      `plugins/edifice/` :
      `skills/edifice/`, `commands/edifice.md`, `scripts/` (11 fichiers : `build_context.py`,
      `create_devis_template.py`, `download_photos.py`, `prepare_diagnostic_template.py`,
      `render_cr_visite.py`, `render_devis.py`, `render_diagnostic.py`, `render_report.py`,
      `update_suivi_chantier_branding.py`, `xml_escape.py`, + le dossier `obsidian/`),
      `templates/ic-ingenieurs/`, `artifacts/`, `organizations/ic-ingenieurs/`,
      `requirements.txt`, `tests/README.md`.
      Ne pas déplacer `plugins/hal/__pycache__` (invariant : il part au ménage, S3).
- [x] **1.2 — Seed du plugin** (invariants 5 et 6) : `plugins/edifice/.claude-plugin/plugin.json`
      en `0.0.0`, `plugins/edifice/CHANGELOG.md` avec `## [0.0.0] — seed`, entrée `edifice` dans
      `.claude-plugin/marketplace.json` (`"source": "./plugins/edifice"`, version `0.0.0`).
- [x] **1.3 — Repointer les 5 familles de chemins** :

| # | Fichier | Ligne(s) | Changement |
|---|---------|----------|------------|
| a | `scripts/check_artifact_sync.sh` | 12 | `ARTIFACTS_DIR` → `plugins/edifice/artifacts` |
| a | `scripts/check_artifact_sync.sh` | 3, 29, 56 | messages d'erreur en dur |
| b | `ui/scripts/build-artifact.mjs` | 113 | `outDir` → `plugins/edifice/artifacts` — **et** le commentaire l.12 |
| c | `.github/workflows/ci.yml` | 33 | `pip install -r plugins/edifice/requirements.txt` |
| c | `.github/workflows/ci.yml` | 42 | filtre `plugins/edifice/artifacts/**` |
| d | `skills/edifice/SKILL.md` | 30 | cache marketplace : `/ 'hal'` → `/ 'edifice'` |
| d | `skills/edifice/SKILL.md` | 45, 46, 47 | 3 chemins dev (Mac ×2, Windows) |
| d | `skills/edifice/SKILL.md` | 24 | `HAL_PLUGIN_DIR` — **ne pas toucher**, ajouter le commentaire qui explique pourquoi |
| e | `tests/test_build_context.py` | 15 | → `plugins/edifice/scripts` |
| e | `tests/test_render_diagnostic.py` | 16 | → `plugins/edifice/scripts` |
| e | `tests/test_render_escaping.py` | 16 | → `plugins/edifice/scripts` |
| e | `tests/test_edifice_render_smoke.py` | 24, 25 | → `plugins/edifice/scripts` **et** `plugins/edifice/templates/ic-ingenieurs` |
| e | `tests/test_build_artifact.py` | 23 | → `plugins/edifice/artifacts` |
| e | `tests/test_xml_escape.py` | 9 | → `plugins/edifice/scripts` — **trouvé en S1**, absent du brief |
| f | `.gitignore` | 19 | → `plugins/edifice/organizations/ic-ingenieurs/` — **trouvé en S1** |

> **b et e/`test_build_artifact.py` ont été trouvés après l'ouverture de #66** — ils manquaient au
> brief initial. Voir invariant 3 pour le couplage a ↔ b.
>
> **Ne pas toucher** : `tests/test_release.py` (invariant 1), `SKILL.md:600` (invariant 2).

### Vérification

```bash
python3 -m unittest discover -s tests -v          # doit passer, 0 échec
bash scripts/check_version_sync.sh                # hal 0.11.6 + edifice 0.0.0 en sync
bash scripts/check_artifact_sync.sh               # lent (pnpm install) — au moins une fois ici
git status --short                                # aucun fichier oublié
grep -rn "plugins/hal" tests/ scripts/ ui/ .github/ plugins/edifice/   # ne doit rester que test_release.py et SKILL.md:600
```

**Critère de sortie** : les trois checks verts, le `grep` ne renvoyant que les deux exceptions
connues. Commit : `refactor(edifice): extract edifice into its own plugin`.

---

## S2 — L2 + L3 : créer `gtm` et `pm`

**Préconditions** : S1 terminée et commitée.

### Étapes

- [x] **2.1 — `gtm`** : `git mv` de `skills/crm/`, `skills/linkedin/`, `commands/crm.md`,
      `commands/linkedin.md` vers `plugins/gtm/`. Aucun script, aucun template — vérifié :
      ces skills ne référencent ni `PLUGIN_DIR`, ni `scripts/`, ni `templates/`, ni `.py`.
- [x] **2.2 — Seed `gtm`** en 0.0.0 (les trois fichiers, invariant 6).
- [x] **2.3 — `pm` depuis `hal`** : `git mv` de `skills/pm/` et `commands/pm.md` vers
      `plugins/pm/`.
- [x] **2.4 — `pm` depuis `renaud-marketplace`** : **copier** (`cp`, pas `git mv` — dépôt
      différent, et la suppression côté `renaud` n'a lieu qu'en S6) :
      `plugins/briefing/skills/sprint-planner/`, `plugins/briefing/skills/sprint-review/`,
      `plugins/briefing/commands/sprint-planner.md`, `plugins/briefing/commands/sprint-review.md`.
      **Vérifié** : ces skills n'ont aucun resolver `PLUGIN_DIR` à repointer (contrairement à ce
      qu'annonçait le brief initial) — copie telle quelle.
- [x] **2.5 — Seed `pm`** en 0.0.0.
- [x] **2.6 — Documenter les deux couplages cross-repo** en tête de `plugins/pm/CHANGELOG.md` :
      `sprint-planner` déclare `Skill(jobsearch-vault)` **et**
      `mcp__plugin_jobsearch_gmail-mcp__search_emails`, tous deux portés par `renaud-marketplace`.
      Non résolus ici (D8), tracés dans #65. **Correction S2** : `Skill(jobsearch-vault)` est
      déclaré par `sprint-planner` **et** `sprint-review` — le CHANGELOG le dit ainsi.

### Vérification

```bash
bash scripts/check_version_sync.sh                # hal + edifice + gtm + pm, tous sync
ls plugins/hal/skills/                            # ne doit plus rien contenir
grep -rn "allowed-tools" plugins/pm/skills/*/SKILL.md plugins/gtm/skills/*/SKILL.md
# → le préfixe mcp__plugin_hal_hal-mcp__ doit être INCHANGÉ partout (D1)
```

**Critère de sortie** : check vert, préfixes MCP intacts. Commit :
`refactor(gtm,pm): extract gtm and pm into their own plugins`.

---

## S3 — L4 + L5 : vider `hal`, ménage

**Préconditions** : S2 terminée. `plugins/hal/skills/` et `plugins/hal/commands/` déjà vides.

### Étapes

- [x] **3.1 — Ne laisser dans `plugins/hal/`** que : `.claude-plugin/plugin.json`, `.mcp.json`,
      `README.md`, `CHANGELOG.md`. Supprimer les dossiers vides résiduels.
- [x] **3.2 — Réécrire `plugins/hal/README.md`** : plugin de connexion, socle obligatoire, et
      la liste des trois plugins qui prennent la suite.
- [x] **3.3 — Ménage** : `plugins/hal/templates/blue-green/.gitkeep` (suivi par git, jamais
      référencé hors CHANGELOG), `plugins/hal/__pycache__`, les `.DS_Store`.
- [x] **3.4 — Note de migration** — rédiger le bloc destiné au `CHANGELOG` de `hal` 0.12.0 :
      ce que voient les installés (`/pm`, `/crm`, `/linkedin`, `/edifice` disparaissent) et quoi
      réinstaller. Il sera posé par `release.sh` en S4 via son argument `<changelog line>`, ou
      complété à la main juste après.

### Vérification

```bash
find plugins/hal -type f -not -path "*/.git/*" | sort   # exactement 4 fichiers attendus
bash scripts/check_version_sync.sh
python3 -m unittest discover -s tests -v
```

**Critère de sortie** : `plugins/hal/` réduit à 4 fichiers, checks verts. Commit :
`refactor(hal): reduce hal to the MCP connector`.

---

## S4 — Versions : 4 × `release.sh`

**Préconditions** : S3 commitée, **working tree strictement propre** (invariant 4).

Compteur top-level actuel : **0.10.12** → attendu **0.10.16** après les quatre releases
(chacune l'incrémente d'un PATCH automatiquement).

### Étapes

- [ ] **4.1** `bash scripts/release.sh edifice 0.1.0 "extract edifice from the hal monolith"`
- [ ] **4.2** `bash scripts/release.sh gtm 0.1.0 "extract crm and linkedin from the hal monolith"`
- [ ] **4.3** `bash scripts/release.sh pm 0.1.0 "extract pm, adopt sprint-planner and sprint-review"`
- [ ] **4.4** `bash scripts/release.sh hal 0.12.0 "reduce hal to the MCP connector — breaking"`
- [ ] **4.5** Compléter à la main la note de migration (rédigée en S3.4, ci-dessous) sous l'entrée
      `## [0.12.0]` de `plugins/hal/CHANGELOG.md`, puis commiter séparément.

#### Note de migration `hal` 0.12.0 — à coller telle quelle

`release.sh` écrit la ligne de titre (`## [0.12.0] — <date> — reduce hal to the MCP connector — breaking`).
Coller ce bloc **juste en dessous**, avant l'entrée `## [0.11.6]` :

```markdown
### Breaking

- `hal` no longer ships any skill or command. On update, `/edifice`, `/pm`, `/crm` and
  `/linkedin` disappear from an existing install. The plugin is now the connector alone: it
  carries `.mcp.json` and nothing else.
- Nothing else changed: same `hal-mcp` server and URL, same server-side workspace resolution,
  same tool names. No `allowed-tools` entry anywhere in the portfolio needs rewriting — the
  `mcp__plugin_hal_hal-mcp__` prefix is unchanged.

### Migration

Keep `hal` installed — it is the mandatory base — then install what you actually use:

| Command you were using | Install |
|------------------------|---------|
| `/edifice …`           | `/plugin install edifice@bluegreen-marketplace` |
| `/pm …`                | `/plugin install pm@bluegreen-marketplace` |
| `/crm …`, `/linkedin …`| `/plugin install gtm@bluegreen-marketplace` |

`pm` also brings `/sprint-planner` and `/sprint-review`, adopted from the `briefing` plugin of
`renaud-marketplace`.

IC Ingénieurs Conseils installs `hal` + `edifice` only — the CRM, project-management and
editorial commands are no longer part of the download.
```

> Chaque `release.sh` lance `check_version_sync.sh` **sur tous les plugins** avant de commiter :
> si un seed est incomplet, la première release échoue et rien n'est écrit. C'est le filet.
> Chaque commande produit son propre commit `chore(<plugin>): release v<version>`.

### Vérification

```bash
bash scripts/check_version_sync.sh
python3 -c "import json; d=json.load(open('.claude-plugin/marketplace.json')); \
print(d['version'], {p['name']: p['version'] for p in d['plugins']})"
# attendu : 0.10.16 {'hal': '0.12.0', 'edifice': '0.1.0', 'gtm': '0.1.0', 'pm': '0.1.0'}
```

**Critère de sortie** : les quatre versions et le compteur conformes.

---

## S5 — L6 documentation + ouverture de la PR #1

**Préconditions** : S4 terminée.

### Étapes

- [ ] **5.1 — `CLAUDE.md`, le plus gros morceau** (16 occurrences de `plugins/hal/`) :
      tableau des plugins (l.28), source-of-truth obsidian (l.98 → `plugins/edifice/scripts/obsidian/`),
      section versioning (l.108-124), `schema-contract.json` (l.168-169), section « Artifact
      front-ends » (l.203-221), Common Gotchas (l.232-233). La section « Repo Structure » est à
      réécrire entièrement : quatre plugins, plus un.
- [ ] **5.2 — `README.md`** : section « Available plugins » (aujourd'hui un plugin unique), plus
      les refs `plugins/hal/` l.37 et l.74. Ajouter les **trois chemins d'installation par
      persona** de #66 (IC, Renaud, Cris).
- [ ] **5.3 — `docs/artifact-front-ends.md`** : `plugins/hal/artifacts/` en l.6, l.30, l.34.
- [ ] **5.4 — Ouvrir la PR** vers `main`, corps reprenant : la rupture `hal` 0.12.0, les quatre
      versions, la note de migration IC, et le fait que la PR `renaud-marketplace` suit.

### Vérification

```bash
grep -rn "plugins/hal" --include="*.md" --include="*.sh" --include="*.yml" --include="*.py" . \
  | grep -v node_modules | grep -v CHANGELOG | grep -v "\.claude/"
# ne doivent rester que : tests/test_release.py (fixture) et plugins/edifice/skills/edifice/SKILL.md:600 (.mcp.json)
```

Puis **CI verte sur la PR** — c'est le premier passage réel : version sync, artifact sync
(déclenché par le déplacement de `artifacts/`), et les tests.

**Critère de sortie** : PR ouverte, CI verte. ⚠️ **Ne pas merger sans avoir lu le diff de
`CLAUDE.md`** — c'est le fichier qui pilote toutes les sessions suivantes.

---

## S6 — PR #2 : `renaud-marketplace`

**Préconditions** : **PR #1 mergée.** Avant ce point, `pm` n'existe pas publiquement et retirer
les skills de `briefing` les rendrait indisponibles.

### Étapes

- [ ] **6.1** Supprimer `plugins/briefing/skills/sprint-planner/`, `skills/sprint-review/`,
      `commands/sprint-planner.md`, `commands/sprint-review.md`.
- [ ] **6.2** `briefing` 0.11.0 → **0.12.0** (perdre deux skills est un changement fonctionnel) —
      via le `release.sh` du dépôt s'il en a un, sinon les trois fichiers à la main.
- [ ] **6.3** `python3 scripts/generate_improve_map.py` — la CI rejette une table périmée.
- [ ] **6.4** Vérifier que `morning-briefing` et `mail-triage` ne référencent pas les deux skills
      partis (`grep -rn "sprint-planner\|sprint-review" plugins/`). **Non vérifié à ce jour** —
      si un renvoi existe, le repointer vers `pm@bluegreen-marketplace` ou le retirer.
- [ ] **6.5** PR + CI verte.

---

## S7 — Validation terrain et cartes

- [ ] **7.1 — Purger le cache** : `~/.claude/plugins/cache/bluegreen-marketplace/` contient un
      `hal` vidé après mise à jour. Purger avant tout test.
- [ ] **7.2 — Profil Cris** (`hal` + `pm` seuls) : crée une tâche dans `rosaslaborbe`, et
      **aucune commande Blue Green n'apparaît**. `sprint-planner` doit s'arrêter en fail-closed
      sur `sprints_enabled=false` — comportement voulu, pas une régression (D7).
- [ ] **7.3 — Profil IC** (`hal` + `edifice` seuls) : génère un rapport de mission de bout en
      bout. C'est le test qui exerce le resolver `PLUGIN_DIR` repointé.
- [ ] **7.4 — Profil Renaud** : les 8 plugins, `whoami` répond depuis un skill de chaque nouveau
      plugin.
- [ ] **7.5 — `BLUEGREEN_MAP.md`** : 8 plugins, versions réelles, table des skills, section
      « hal + edifice ». Commité et poussé depuis `archon-workflows` (le fichier est un symlink).
- [ ] **7.6 — `.claude/STATUS.md` des deux dépôts**, et clôture de #66.

---

## Journal

> Une ligne par session : ce qui a été fait, ce qui a surpris, où ça s'est arrêté.

- **2026-08-02 — S0.** Cadrage (#66) puis révision du brief contre les sources : 5 corrections,
  dont les tests de `tests/` non repointés (CI rouge garantie) et `CLAUDE.md` absent de L6.
  `skill-improve` écarté — il réintroduirait le champ `version:` supprimé des `SKILL.md`.
  `edifice-front_2.html` supprimé. Deux chemins de plus trouvés en rédigeant ce plan :
  `ui/scripts/build-artifact.mjs:113` et `tests/test_build_artifact.py:23`.
- **2026-08-02 — décision.** `HAL_PLUGIN_DIR` gardé tel quel (Renaud). Le nom survit au découpage :
  échappatoire de dev, pas une interface publique. S1 n'a plus de préalable.
- **2026-08-02 — S1.** `edifice` extrait, seed 0.0.0, 5 familles repointées. Trois surprises,
  toutes bénignes : `tests/test_xml_escape.py:9` pointait aussi sur `plugins/hal/scripts` (6ᵉ test,
  absent du brief) ; `organizations/ic-ingenieurs/` est **gitignoré** (`.gitignore:19`) donc
  `git mv` a refusé — déplacé au `mv` puis ligne d'ignore repointée, une famille (f) de plus ;
  `check_artifact_sync.sh` réécrit le build-stamp des deux artefacts en passant, rétabli depuis
  l'index pour garder le diff propre. Les trois checks verts (75 tests, version-sync sur `hal`
  0.11.6 + `edifice` 0.0.0, artifact-sync sur les deux artefacts), grep résiduel limité aux deux
  exceptions attendues. `HAL_PLUGIN_DIR` conservé avec le commentaire qui explique pourquoi.
- **2026-08-02 — S2.** `gtm` (crm + linkedin) et `pm` (pm + sprint-planner + sprint-review) créés,
  seeds 0.0.0. Sans surprise : les deux vérifications annoncées par le plan se confirment — aucun
  des six skills ne référence de script, de template ou de `PLUGIN_DIR`, et le préfixe
  `mcp__plugin_hal_hal-mcp__` est intact. Une seule nuance : `Skill(jobsearch-vault)` est déclaré
  par les **deux** skills sprint, pas seulement `sprint-planner` (le brief ne citait que
  `sprint-planner`) ; le second couplage, `mcp__plugin_jobsearch_gmail-mcp__search_emails`, reste
  propre à `sprint-planner`. Les deux copies depuis `renaud-marketplace` sont faites telles quelles
  (suppression côté `renaud` en S6). Checks verts : version-sync sur les 4 plugins, 75 tests OK.
  `plugins/hal/skills/` et `plugins/hal/commands/` sont vides — leur suppression est S3.1.
- **2026-08-02 — S3.** `hal` réduit à ses 4 fichiers (`plugin.json`, `.mcp.json`, `README.md`,
  `CHANGELOG.md`) : `.gitkeep` supprimé au `git rm` — qui a emporté les dossiers vides au passage —
  puis `skills/` et `commands/` retirés du disque. Aucun `__pycache__` sous `hal` (il avait suivi
  `edifice` en S1, supprimé là-bas avec les trois `.DS_Store`, tous gitignorés). README réécrit :
  socle connecteur, table des trois plugins qui prennent la suite, chemins d'installation, encart
  « Upgrading from 0.11.x ». Deux ajouts hors liste, tous deux devenus faux avec le découpage :
  le bloc « Versioning convention » du CHANGELOG de `hal` décrivait un versionnage par skill
  (`version:` n'existe plus) et était en français dans un doc anglais — réécrit et aligné sur les
  trois autres plugins ; la `description` de `hal` (« second brain and mission workflow ») remplacée
  par celle du connecteur, dans `plugin.json` **et** dans l'entrée marketplace, les deux devant
  rester identiques. Note de migration 0.12.0 rédigée et posée dans ce document sous S4.5, prête à
  coller. Checks verts : 4 fichiers, version-sync sur les 4 plugins, 75 tests OK.

---

## Completion

- **Started**: 2026-08-02
- **Completed**: —
- **PR bluegreen**: —
- **PR renaud**: —
