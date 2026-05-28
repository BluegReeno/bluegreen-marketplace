# Plan : Plugin `hal` v0.1.0

**Repo** : `bluegreen-marketplace`
**Branch cible** : `feat/hal-plugin-v0.1`
**PR title** : `feat: rename plugin to hal + add /hal update skill v0.1.0 (Obsidian vault)`
**Séquence** : ce plan en premier → puis `.agents/plans/remove-hal-crm-skill.md` dans le repo `hal`

---

## Contexte & Décisions d'architecture

### Ce qu'on construit

On renomme le plugin `edifice-mission-report` → `hal`.  
On ajoute un second skill `/hal` au plugin existant.  
Le skill `/hal update` v0.1.0 cible le vault Obsidian via les scripts `obsidian-crm` déjà écrits dans `hal/agents/skills/hal-crm/scripts/`.

### Vision long terme

- HAL = plateforme générique pour PMEs (CRM + gestion de projet)
- `edifice` = première verticale (BET, diagnostics bâtiment)
- `/hal update` v0.2.0 (future) → Supabase via `hal-mcp` CRM tools, quand migration Obsidian → Supabase prête

### Pourquoi Obsidian d'abord

Le vault Obsidian est aujourd'hui la source de vérité opérationnelle. Les scripts `obsidian-crm` sont déjà écrits et testés. La migration vers Supabase est planifiée mais pas encore prête. Le skill v0.1.0 résout un besoin immédiat sans attendre.

### hal-crm SQLite

Abandonné. Ne pas porter dans le plugin `hal`.

### Source de vérité pour les scripts vault I/O (obsidian-crm)

`plugins/hal/scripts/obsidian/` dans `bluegreen-marketplace` = **source de vérité unique**.

`hal/agents/skills/hal-crm/` est supprimé du repo hal (Phase 5). Tout passe par Cowork — aucun workflow ne passe par `hal chat` en terminal pour les scripts vault.

---

## Politique de versioning (décision prise)

### Règle

| Composant | Version propre | Fichier |
|-----------|---------------|---------|
| Plugin `hal` | `version` | `plugins/hal/.claude-plugin/plugin.json` |
| Skill `edifice` | `version:` frontmatter | `plugins/hal/skills/edifice/SKILL.md` |
| Skill `hal` | `version:` frontmatter | `plugins/hal/skills/hal/SKILL.md` |
| MCP `hal-mcp` | `"version"` | `plugins/hal/.mcp.json` |

**Par release** : tout composant modifié → ce composant PATCH +1. Plugin PATCH +1 (une seule fois par release, quel que soit le nombre de composants).

**MINOR** (`0.x.0`) pour changement d'interface (nouvelle commande, nouveau champ obligatoire). **PATCH** (`0.0.x`) pour bugfix et améliorations internes.

### Exemple d'évolution dans le temps

| Release | Ce qui change | edifice | hal skill | hal-mcp | **plugin** |
|---------|--------------|---------|-----------|---------|------------|
| v0.1.0 (initial) | — | 0.1.0 | 0.1.0 | 0.1.0 | **0.1.0** |
| R1 — même release | edifice + hal-mcp modifiés ensemble | **0.1.1** | 0.1.0 | **0.1.1** | **0.1.1** |
| R2 — release séparée | edifice seul | **0.1.2** | 0.1.0 | 0.1.1 | **0.1.2** |
| R3 — release séparée | hal skill seul | 0.1.2 | **0.1.1** | 0.1.1 | **0.1.3** |
| R4 — migration Supabase | hal skill (interface change) | 0.1.2 | **0.2.0** | **0.2.0** | **0.2.0** |

R2 et R3 séparées → plugin a pris +2 au total. Chaque +1 déclenche une mise à jour dans Claude Cowork.

---

## Structure cible du plugin

```
plugins/hal/
├── .claude-plugin/
│   └── plugin.json              # name: hal, version: 0.1.0
├── .mcp.json                    # hal-mcp + version: 0.1.0
├── skills/
│   ├── edifice/
│   │   └── SKILL.md             # version: 0.1.0 — /edifice pull improve report push
│   └── hal/
│       └── SKILL.md             # version: 0.1.0 — /hal update
├── scripts/
│   ├── build_context.py         # existant (edifice)
│   ├── download_photos.py       # existant (edifice)
│   ├── render_report.py         # existant (edifice)
│   ├── render_diagnostic.py     # existant (edifice)
│   ├── render_cr_visite.py      # existant (edifice)
│   ├── render_devis.py          # existant (edifice)
│   ├── hal_update.py            # NOUVEAU — NL parser + appels obsidian-crm
│   └── obsidian/                # NOUVEAU — bundle des scripts obsidian-crm (source: hal repo)
│       ├── search_vault.py      #   copie depuis hal/agents/skills/hal-crm/scripts/
│       ├── read_note.py
│       ├── list_notes.py
│       ├── create_note.py
│       ├── update_frontmatter.py
│       ├── sprint_transition.py
│       └── references/
│           └── schemas.md       #   11 types de notes + frontmatter — source de vérité
├── templates/                   # existant (edifice)
├── organizations/               # existant (edifice)
├── requirements.txt             # ajouter rapidfuzz>=3.0 (fuzzy match)
├── README.md                    # mettre à jour
└── CHANGELOG.md                 # entrée v0.1.0
```

---

## Tâches

### Phase 1 — Renommage du plugin

#### 1.1 Renommer le répertoire

```bash
git mv plugins/edifice-mission-report plugins/hal
```

#### 1.2 Mettre à jour `plugins/hal/.claude-plugin/plugin.json`

```json
{
  "name": "hal",
  "version": "0.1.0",
  "description": "HAL — second brain and mission workflow for BlueGreen and IC Ingénieurs Conseils.",
  "author": { "name": "Renaud Laborbe", "email": "renaud@bluegreen.ai" }
}
```

#### 1.3 Mettre à jour `plugins/hal/.mcp.json`

Ajouter le champ `"version": "0.1.0"` à l'entrée `hal-mcp`.

Format cible :
```json
{
  "mcpServers": {
    "hal-mcp": {
      "type": "sse",
      "url": "https://zgkvbjqlvebttbnkklpo.supabase.co/functions/v1/hal-mcp",
      "version": "0.1.0",
      "headers": {
        "Authorization": "Bearer ${SUPABASE_ANON_KEY}"
      }
    }
  }
}
```

#### 1.4 Mettre à jour `plugins/hal/skills/edifice/SKILL.md`

- `version:` frontmatter → `0.1.0`
- Mettre à jour le bloc de résolution `PLUGIN_DIR` : chercher `plugins/hal/` dans les chemins connus (remplacer `edifice-mission-report`)

#### 1.5 Mettre à jour `.claude-plugin/marketplace.json`

```json
{
  "plugins": [
    {
      "name": "hal",
      "version": "0.1.0",
      "description": "HAL — second brain and mission workflow.",
      "skills": [
        { "name": "edifice", "version": "0.1.0" },
        { "name": "hal", "version": "0.1.0" }
      ],
      "mcp": { "name": "hal-mcp", "version": "0.1.0" }
    },
    {
      "name": "hal-crm",
      "placeholder": true
    }
  ]
}
```

---

### Phase 2 — Créer le skill `/hal`

#### 2.1 Créer `plugins/hal/skills/hal/SKILL.md`

Frontmatter :
```yaml
---
name: hal
description: >
  Update the Obsidian SecondLife vault from a natural-language instruction.
  Use when the user says /hal update, "note that", "mets à jour",
  "marque comme fait", "relance le", "RDV prévu", "pas de contact",
  or any explicit vault write instruction mid-conversation.
  Also trigger when user says "done", "fait", "c'est bon", "next"
  after completing a task — propose the corresponding vault write.
version: 0.1.0
allowed-tools: "Bash(uv *) Bash(python3 *) Bash(find *) Bash(ls *) Read Write"
---
```

Contenu du skill :

**Résolution des chemins au démarrage**

```bash
# Résoudre PLUGIN_DIR (même pattern que /edifice)
PLUGIN_DIR=$(python3 - <<'PYEOF'
import json, os, pathlib, sys, glob as _glob

home = pathlib.Path.home()

# 1. env var
env = os.environ.get('HAL_PLUGIN_DIR', '')
if env and pathlib.Path(env, 'scripts', 'hal_update.py').exists():
    print(env); sys.exit(0)

# 2. Claude Code marketplace cache
for _mkt in ['bluegreen-marketplace']:
    cache_root = home / '.claude' / 'plugins' / 'cache' / _mkt / 'hal'
    if cache_root.exists():
        candidates = sorted(cache_root.glob('*/scripts/hal_update.py'), key=lambda p: p.stat().st_mtime, reverse=True)
        if candidates:
            print(str(candidates[0].parent.parent)); sys.exit(0)

# 3. Cowork sandbox
for pat in ['/sessions/*/mnt/.remote-plugins/*/scripts/hal_update.py']:
    matches = sorted(_glob.glob(pat), key=lambda p: os.path.getmtime(p), reverse=True)
    if matches:
        print(os.path.dirname(os.path.dirname(matches[0]))); sys.exit(0)

# 4. Dev paths
for dev_path in [
    home / 'Projects' / 'bluegreen-marketplace' / 'plugins' / 'hal',
]:
    if dev_path.joinpath('scripts', 'hal_update.py').exists():
        print(str(dev_path)); sys.exit(0)

print('PLUGIN_DIR_NOT_FOUND')
PYEOF
)
if [ "$PLUGIN_DIR" = "PLUGIN_DIR_NOT_FOUND" ]; then
  echo "ERROR: HAL plugin dir introuvable. Définis HAL_PLUGIN_DIR=<chemin> dans ton shell."
  exit 1
fi

# Résoudre VAULT_PATH
VAULT_PATH=$(python3 - <<'PYEOF'
import os, pathlib, glob as _glob, sys

# 1. env var
env = os.environ.get('OBSIDIAN_VAULT_PATH', '')
if env and pathlib.Path(env).exists():
    print(env); sys.exit(0)

# 2. Cowork sandbox
for pat in ['/sessions/*/mnt/SynologyDrive-MyAssistant/SecondLife-vault/SecondLife']:
    matches = _glob.glob(pat)
    if matches:
        print(matches[0]); sys.exit(0)

# 3. Dev path
dev = pathlib.Path.home() / 'SynologyDrive-MyAssistant' / 'SecondLife-vault' / 'SecondLife'
if dev.exists():
    print(str(dev)); sys.exit(0)

print('VAULT_NOT_FOUND')
PYEOF
)
if [ "$VAULT_PATH" = "VAULT_NOT_FOUND" ]; then
  echo "ERROR: Vault Obsidian introuvable. Définis OBSIDIAN_VAULT_PATH=<chemin>."
  exit 1
fi
```

**`/hal update <texte libre>`**

1. Parser le texte utilisateur pour extraire entité + intention + valeur
2. Appeler `hal_update.py` avec le texte brut
3. Le script résout les notes, planifie les writes, demande confirmation si ambigu
4. Afficher le résultat : `✅ [Note] → [field]: [valeur]`

```bash
uv run \
  --with "rapidfuzz>=3.0" \
  python3 $PLUGIN_DIR/scripts/hal_update.py \
  --vault "$VAULT_PATH" \
  --text "<texte utilisateur verbatim>"
```

**Tableaux de référence (dans le skill)**

Vault structure :
```
CRM-BlueGreen/Opportunites/    type: opportunite-bg
CRM-BlueGreen/Entreprises/     type: entreprise-bg
CRM-BlueGreen/Contacts/        type: contact-bg
CRM-BlueGreen/Interactions/    type: interaction-bg
CRM-JobSearch/Opportunites/    type: opportunite-js
CRM-JobSearch/Entreprises/     type: entreprise-js
CRM-JobSearch/Contacts/        type: contact-js
CRM-JobSearch/Entretiens/      type: entretien
Taches/                        type: tache
Projets/                       type: projet
```

Field mapping NL → frontmatter (extrait du hal-crm-spec.md) :

| User dit | Champs mis à jour |
|----------|------------------|
| "pas de contact", "candidature plateforme" | `notes` (append) + `date_relance` (clear) |
| "RDV le [date]", "entretien prévu [date]" | `prochain_rdv` + `statut` → `📞 Entretien prévu` |
| "relance le [date]" | `date_relance` |
| "refus", "dead", "pas retenu" | `statut` → `❌ Refus` |
| "offre reçue" | `statut` → `✅ Offre reçue` |
| "terminé", "fait", "done" (tâche) | `etat` → `Terminé` |
| "note: [text]" | `notes` (overwrite) |
| "ajouter note: [text]" | `notes` (append + timestamp ISO) |

---

### Phase 3 — Bundler les scripts `obsidian-crm` dans le plugin

`/hal update` ne réimplémente **pas** le vault I/O. Il appelle les scripts `obsidian-crm` comme sous-processus. Ces scripts sont **bundlés** dans le plugin (pas résolus à runtime depuis le repo hal) pour fonctionner dans Cowork où le repo hal n'est pas monté.

**Source** : `hal/agents/skills/hal-crm/scripts/` + `hal/agents/skills/hal-crm/references/`

**Destination dans le plugin** :
```
plugins/hal/scripts/obsidian/
├── obsidian_api.py          # vault client (filesystem + REST API fallback) — dep de tous les scripts
├── note_schemas.py          # validation schemas Python — dep de tous les scripts
├── search_vault.py          # copie depuis hal/agents/skills/hal-crm/scripts/
├── read_note.py
├── list_notes.py
├── create_note.py
├── update_frontmatter.py
├── sprint_transition.py
└── references/
    └── schemas.md           # source de vérité : 11 types de notes + frontmatter exacts
```

**Source de vérité unique** : `plugins/hal/scripts/obsidian/` EST la source de vérité. Aucune sync à faire — `hal/agents/skills/hal-crm/` est supprimé du repo hal (voir Phase 5). Tout passe par Cowork.

`hal_update.py` résout son chemin obsidian via :
```python
OBSIDIAN_SCRIPTS = Path(__file__).parent / "obsidian"
```
Pas de résolution runtime, pas d'env var nécessaire. Le chemin est relatif au plugin.

---

### Phase 4 — Créer `scripts/hal_update.py`

Script principal appelé par le skill. Dépendance unique : `rapidfuzz` (via `uv run --with`).

**Interface CLI** :
```
hal_update.py --vault <path> --text <user_text> [--force] [--dry-run]
```

**Pipeline** :
```
1. PARSE   — extraire entité + intention + valeur du texte libre
2. RESOLVE — trouver la note via search_vault.py (fuzzy match rapidfuzz)
3. PLAN    — construire liste de VaultWrite (respecter schemas.md pour les champs)
4. CONFIRM — afficher le plan (skip si --force ou écriture non ambiguë)
5. WRITE   — appeler update_frontmatter.py pour chaque write
6. REPORT  — une ligne par changement : ✅ [Note] → [field]: [valeur]
```

**Schemas.md comme source de vérité** :
`hal_update.py` charge `obsidian/references/schemas.md` au démarrage pour connaître :
- Les 11 types de notes et leurs dossiers dans le vault
- Les champs frontmatter valides par type
- Les valeurs enum autorisées (statut, etat, etc.)

Aucun field mapping n'est hardcodé dans `hal_update.py` — tout vient de `schemas.md`.

**Scripts obsidian-crm appelés (bundlés dans `scripts/obsidian/`)** :
- `search_vault.py <query> --vault <path>` → liste de notes candidates
- `read_note.py <note_path> --vault <path>` → JSON frontmatter + contenu
- `update_frontmatter.py <note_path> <field> <value> --vault <path>` → write

**Fuzzy matching** :
- `rapidfuzz.process.extract(entity, note_titles, scorer=fuzz.WRatio, limit=3)`
- Score > 80 : match direct
- Score 50–80 : afficher candidats, demander à l'utilisateur
- Score < 50 : note introuvable, proposer création

**Hint de dossier** :
- "candidature", "poste", "entretien" → `CRM-JobSearch/`
- "client", "propale", "devis", "mission" → `CRM-BlueGreen/`
- "tâche", "faire", "task" → `Taches/`
- Pas de hint → chercher partout, ranked par relevance

---

### Phase 4 — Mise à jour fichiers annexes

#### 4.1 `requirements.txt`

Ajouter `rapidfuzz>=3.0` (runtime via `uv run --with`, listé ici comme manifest).

#### 4.2 `plugins/hal/README.md`

Mettre à jour :
- Nom du plugin : `hal`
- Deux skills : `edifice` + `hal`
- Section `/hal update` avec exemples

#### 4.3 `plugins/hal/CHANGELOG.md`

Ajouter entrée :

```markdown
## [0.1.0] — YYYY-MM-DD — HAL plugin : renommage + skill /hal (Obsidian vault)

### Changed
- Plugin renommé `edifice-mission-report` → `hal`
- Skill `edifice` : version reset à 0.1.0 (nouveau plugin, historique CHANGELOG préservé)

### Added
- Skill `hal` v0.1.0 — `/hal update` : mise à jour du vault Obsidian en langage naturel
- `scripts/hal_update.py` — NL parser + orchestrateur de writes obsidian-crm
- Politique de versioning par composant documentée dans CLAUDE.md

### Architecture
- hal-mcp v0.1.0 — version trackée dans `.mcp.json`
- `/hal` v0.2.0 (future) : migration data layer Obsidian → Supabase via hal-mcp CRM tools
```

#### 4.4 `CLAUDE.md` du repo

Mettre à jour :
- Nouvelle structure `plugins/hal/`
- Politique de versioning (règle + tableau d'exemple)
- Section "Migration path" : `/hal` v0.1.0 Obsidian → v0.2.0 Supabase
- Mention : `plugins/hal/scripts/obsidian/` = source de vérité unique pour les scripts vault I/O

---

> **Étape suivante** (repo `hal`) : merger cette PR, puis lancer
> `hal/.agents/plans/remove-hal-crm-skill.md`

---

## Tests de validation

### Level 1 — Structure et versions cohérentes

```bash
cd /Users/renaud/Projects/bluegreen-marketplace

# Plugin renommé
test -d plugins/hal && echo "hal dir OK" || echo "MISSING"
test ! -d plugins/edifice-mission-report && echo "old dir gone OK" || echo "PROBLEM"

# Versions identiques plugin.json = marketplace.json
python3 -c "
import json
m = json.load(open('.claude-plugin/marketplace.json'))
p = json.load(open('plugins/hal/.claude-plugin/plugin.json'))
plugin = next(x for x in m['plugins'] if x['name']=='hal')
assert plugin['version'] == p['version'], f'MISMATCH: {plugin[\"version\"]} vs {p[\"version\"]}'
print(f'Version parity OK: {p[\"version\"]}')
"

# Version hal-mcp dans .mcp.json
python3 -c "
import json
mcp = json.load(open('plugins/hal/.mcp.json'))
v = mcp['mcpServers']['hal-mcp'].get('version')
assert v, 'hal-mcp version missing'
print(f'hal-mcp version OK: {v}')
"
```

### Level 2 — PLUGIN_DIR resolution (edifice)

```bash
cd /Users/renaud/Projects/bluegreen-marketplace/plugins/hal
python3 -c "
import pathlib
p = pathlib.Path('scripts/hal_update.py')
assert p.exists(), f'hal_update.py missing: {p}'
print('hal_update.py OK')
"
```

### Level 3 — hal_update.py import

```bash
cd /Users/renaud/Projects/bluegreen-marketplace/plugins/hal
python3 -c "
import importlib.util, sys
spec = importlib.util.spec_from_file_location('hal_update', 'scripts/hal_update.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print('hal_update import OK')
"
```

### Level 4 — hal_update dry run

```bash
VAULT="$HOME/SynologyDrive-MyAssistant/SecondLife-vault/SecondLife"
uv run \
  --with "rapidfuzz>=3.0" \
  python3 plugins/hal/scripts/hal_update.py \
  --vault "$VAULT" \
  --text "test — dry run" \
  --dry-run
# Expected : résolution vault OK, 0 writes
```

### Level 5 — Render edifice (non-régression)

```bash
MISSION="$HOME/Library/CloudStorage/GoogleDrive-renaud@bluegreen.ai/Drive partagés/PARTENAIRES/IC Ingénieurs Conseils/Dev-xxx-Diag rue de varenne/mission"
uv run --with "docxtpl>=0.18" --with pillow \
  python3 plugins/hal/render_report.py \
  "$MISSION/context.json" \
  --photos-dir "$MISSION/photos" \
  --output /tmp/test_edifice_nonreg.docx
python3 -c "
import os; s = os.path.getsize('/tmp/test_edifice_nonreg.docx')
assert s > 50000, f'trop petit ({s} bytes)'
print(f'Non-régression edifice OK: {s} bytes')
"
```

---

## Critères d'acceptation

- [ ] `plugins/edifice-mission-report/` n'existe plus
- [ ] `plugins/hal/` existe avec tous les fichiers
- [ ] `plugin.json` : `name: hal`, `version: 0.1.0`
- [ ] `.mcp.json` : champ `version: 0.1.0` sur hal-mcp
- [ ] `skills/edifice/SKILL.md` : `version: 0.1.0`, PLUGIN_DIR résout `plugins/hal/`
- [ ] `skills/hal/SKILL.md` : `version: 0.1.0`, trigger `/hal update`
- [ ] `scripts/obsidian/` : 8 scripts (`obsidian_api.py` + `note_schemas.py` + 6 scripts) + `references/schemas.md` bundlés depuis hal repo
- [ ] `scripts/hal_update.py` : import OK, CLI `--vault --text --force --dry-run`, schemas chargés depuis `obsidian/references/schemas.md`
- [ ] `marketplace.json` : `name: hal`, versions cohérentes
- [ ] Level 1–5 validation passent
- [ ] `CHANGELOG.md` entrée v0.1.0
- [ ] `CLAUDE.md` à jour (structure + versioning policy)

---

## Commit message

```
feat(hal): rename plugin to hal + add /hal update skill v0.1.0 (Obsidian vault)
```
