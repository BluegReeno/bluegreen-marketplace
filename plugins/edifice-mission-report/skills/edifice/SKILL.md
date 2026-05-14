---
name: edifice
description: >
  This skill should be used when the user is in a directory containing a
  *.edifice.md file, or asks to "pull an Edifice mission", "generate an
  Edifice report", "create a diagnostic report", "generate a devis", or
  "run edifice". Also activates when the user says "/edifice pair" or
  "pair edifice" or "connecter edifice" when the laptop has not been
  paired yet.
version: 0.3.4
allowed-tools: "Bash(uv *) Bash(pip *) Bash(python3 *) Bash(python *) Bash(curl *) Bash(chmod *) Bash(mkdir *) Bash(find *) Bash(ls *) Read Write Edit Glob"
---

# Edifice — Mission Workflow (Claude Code)

## Plugin directory

```bash
# Resolve PLUGIN_DIR — priority: config.json → env var → marketplace cache → known dev paths → error
PLUGIN_DIR=$(python3 - <<'PYEOF'
import json, os, pathlib, sys

home = pathlib.Path.home()

# 1. config.json explicit plugin_dir
cfg = home / '.edifice-mission-report' / 'config.json'
if cfg.exists():
    try:
        d = json.loads(cfg.read_text())
        pd = d.get('plugin_dir', '')
        if pd and pathlib.Path(pd, 'pull_mission.py').exists():
            print(pd); sys.exit(0)
    except Exception:
        pass

# 2. env var
env = os.environ.get('EDIFICE_PLUGIN_DIR', '')
if env and pathlib.Path(env, 'pull_mission.py').exists():
    print(env); sys.exit(0)

# 3. Claude Code marketplace cache (bluegreen-marketplace or legacy edifice-marketplace)
for _mkt in ['bluegreen-marketplace', 'edifice-marketplace']:
    cache_root = home / '.claude' / 'plugins' / 'cache' / _mkt / 'edifice-mission-report'
    if cache_root.exists():
        candidates = sorted(cache_root.glob('*/pull_mission.py'), key=lambda p: p.stat().st_mtime, reverse=True)
        if candidates:
            print(str(candidates[0].parent)); sys.exit(0)

# 4. Cowork app sandbox: /sessions/*/mnt/.remote-plugins/plugin_*/pull_mission.py
import glob as _glob
for pat in ['/sessions/*/mnt/.remote-plugins/*/pull_mission.py']:
    matches = sorted(_glob.glob(pat), key=lambda p: os.path.getmtime(p), reverse=True)
    if matches:
        print(os.path.dirname(matches[0])); sys.exit(0)

# 5. Known dev paths (Mac + Windows)
for dev_path in [
    home / 'Projects' / 'edifice' / 'plugins' / 'edifice-mission-report',
    home / 'projects' / 'edifice' / 'plugins' / 'edifice-mission-report',
    pathlib.Path('C:/Users') / os.environ.get('USERNAME', '') / 'Projects' / 'edifice' / 'plugins' / 'edifice-mission-report',
]:
    if dev_path.joinpath('pull_mission.py').exists():
        print(str(dev_path)); sys.exit(0)

print('PLUGIN_DIR_NOT_FOUND')
PYEOF
)
if [ "$PLUGIN_DIR" = "PLUGIN_DIR_NOT_FOUND" ]; then
  echo "ERROR: Plugin dir introuvable. Lance /edifice pair ou définis EDIFICE_PLUGIN_DIR."
  exit 1
fi
```

## Path resolution — run at the start of every command

```bash
# Briefing file in current directory
BRIEFING=$(find . -maxdepth 1 -name "*.edifice.md" | head -1)
echo "Briefing: $BRIEFING"

# Mission output dir (created by /edifice pull)
MISSION_DIR="./mission"
```

---

## /edifice pull

Pull mission data via `pull_mission.py`. Reads the `*.edifice.md` briefing,
downloads project + building + notes + photos from Supabase (with auto token
refresh), writes the result to `./mission/`, and prints a structured summary.

### Steps

**0. Setup Cowork sandbox — faire EN PREMIER**

Vérifier si on tourne dans le sandbox Cowork :
```bash
pwd
```
Si le résultat commence par `/sessions/`, on est dans le sandbox. Deux choses à faire avant tout.

#### A. BRIEFING — toujours utiliser le chemin sandbox

Le dossier de travail est monté dans la VM à `/sessions/<name>/mnt/`. Utiliser `find .` pour obtenir le chemin sandbox automatiquement — **ne jamais utiliser le chemin Mac** (`/Users/.../CloudStorage/...`) pour lancer des scripts bash : ça deadlocke (OSError errno 35 EDEADLK).

```bash
BRIEFING=$(find . -maxdepth 1 -name "*.edifice.md" | head -1)
# → ./mission.edifice.md (chemin sandbox via virtiofs — pas de deadlock)
```

#### B. Credentials — bootstrap depuis le Mac via Read tool

`~/.edifice-mission-report/` sur le Mac n'est **pas monté** dans la VM (seul le dossier de travail l'est). Bootstrapper en début de session :

1. Utiliser le **Read tool** pour lire `~/.edifice-mission-report/config.json` (= dernier compte pairé)
   - Si `EDIFICE_USER` est défini → lire `~/.edifice-mission-report/config-<EDIFICE_USER>.json` à la place
2. Écrire le contenu dans le home du sandbox via bash :
```bash
mkdir -p ~/.edifice-mission-report
cat > ~/.edifice-mission-report/config.json << 'CREDS'
{ ... contenu lu par Read tool ... }
CREDS
```

> Le Read tool s'exécute côté Mac (pas dans la VM) → accède à `~` Mac sans problème.
> Le `cat >` s'exécute dans la VM → écrit dans `~` sandbox (éphémère, durée de session).
> L'email de l'utilisateur n'est **pas** dans le `.edifice.md` — `config.json` (dernier pairé) suffit dans le cas standard.

**1. Parse mission ID from briefing**
```bash
python3 -c "
import re, pathlib, sys
text = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')
m = re.search(r'edifice_mission_id:\s*([0-9a-f-]{36})', text)
print(m.group(1) if m else 'NOT_FOUND')
" "$BRIEFING"
```

**2. Pull data + photos avec auto-refresh**
```bash
python3 $PLUGIN_DIR/pull_mission.py "$BRIEFING" --pull-only
```

`pull_mission.py` :
- Lit `~/.edifice-mission-report/config.json` (bootstrappé à l'étape 0B)
- Auto-refresh le token si expiré (stdlib urllib — aucune dépendance externe)
- Télécharge projet, bâtiment, notes, photos
- Écrit `mission/data/` + `mission/photos/` + `mission/context.json` → dans le dossier de travail, donc directement dans GDrive/OneDrive

En cas d'erreur "Credentials not found" → vérifier que l'étape 0B a bien été faite.

**3. Display mission summary**
```bash
python3 - <<'EOF'
import json, pathlib

data_dir = pathlib.Path("mission/data")
ctx = json.loads(pathlib.Path("mission/context.json").read_text())
project = json.loads((data_dir / "project.json").read_text())
building = json.loads((data_dir / "building.json").read_text()) or {}
notes = json.loads((data_dir / "notes.json").read_text())
photos = json.loads((data_dir / "photos.json").read_text())

print(f"Mission : {project.get('name', '')}")
print(f"Type    : {project.get('type', 'inconnu')}")
print(f"Bâtiment: {building.get('name', '')} — {building.get('address', '')}")
print(f"Notes   : {len(notes)}")
print(f"Photos  : {len(photos)}")
print()
print("Observations:")
for obs in ctx.get("observations", []):
    ref = obs.get("ref", "")
    name = obs.get("name", "")
    text = (obs.get("observation") or "")[:80]
    zone = obs.get("zone") or "—"
    ie = obs.get("ie")
    ie_str = f"IE={ie}" if ie else ""
    print(f"  {ref:8} | {zone:4} {ie_str:5} | {name:25} | {text}")
EOF
```

Present the output clearly to the user. Mention the mission type — it determines
which template `/edifice report` will use.

---

## /edifice improve

The user describes improvements to one or more observations. Claude reads
`mission/context.json`, edits the relevant entries directly, then confirms.

### How to handle the user's request

1. Read `mission/context.json` with the Read tool.
2. Understand what the user wants to change:
   - "note 3 doit mentionner une fissure de 3mm" → update `observations[2].desordre`
   - "groupe toutes les notes par zone APT/BAL/CAV/FAC et ajoute les IE" → update
     `zone` and `ie` fields for all observations, and rename `ref` (APT-01, etc.)
   - "améliore la description de l'observation APT-02" → enrich the `desordre` text
   - "ajoute une synthèse globale" → update the `synthese` field
3. Edit `mission/context.json` with the Edit tool (or Write to replace entirely for
   large restructures).
4. Show the user a diff-style summary of what changed.

### Context.json — champs éditables par type

**`diagnostic`** — champs à enrichir :
`description_batiment`, `objet_visite`, `synthese`, `conclusion`
Observations : `zone`, `localisation`, `desordre`, `ie`, `action`

**`suivi_chantier`** — champs à enrichir :
`participants`, `objet_visite`, `synthese`, `conclusion`
Observations : `etage_facade`, `observation`, `action`

**`devis`** — champs à enrichir :
`type_acteur`, `interlocuteur_nom`, `interlocuteur_role`, `declencheur`,
`livrable`, `urgence`, `description_batiment`, `documents_fournis`,
`proposition_mission`, `incertitudes`, `chiffrage`
Observations : `localisation`, `desordre`, `donnees_cles`, `ref_photo`

**IE scale** (diagnostic uniquement) :
- 1 = Risque de ruine immédiate → mise en sécurité immédiate
- 2 = Désordres graves sans ruine → réparation court terme
- 3 = Dégradation sans gravité → entretien moyen terme
- 4 = Dégradation légère → entretien long terme
- 5 = Bon état → surveillance

---

## /edifice report

Generate the DOCX report from the current `mission/context.json`.
Uses `render_report.py` — a unified dispatcher that requires no Supabase connection.

### Steps

**1. Generate (all types — diagnostic, suivi_chantier, devis)**
```bash
uv run \
  --with "docxtpl>=0.18" \
  --with pillow \
  python3 $PLUGIN_DIR/render_report.py \
  mission/context.json \
  --photos-dir mission/photos \
  --output mission/rapport.docx
```

`render_report.py` reads `project_type` from `context.json` and routes automatically:
- `diagnostic`      → `render_diagnostic.py`  + `templates/ic-ingenieurs/diagnostic.docx`
- `suivi_chantier`  → `render_cr_visite.py`   + `templates/ic-ingenieurs/suivi_chantier.docx`
- `devis`           → `render_devis.py`        + `templates/ic-ingenieurs/devis.docx`

Org override: `--org ic-ingenieurs` (default) or env var `EDIFICE_ORG=ic-ingenieurs`.

**2. Confirm to user**
Tell the user: "Rapport généré : `mission/rapport.docx`" and provide the file path.

---

## Types de rapports — schemas JSON et renderers

### `diagnostic` — Rapport de diagnostic structurel
Renderer : `render_diagnostic.py` | docxtpl + `templates/ic-ingenieurs/diagnostic.docx`

```json
{
  "project_type": "diagnostic",
  "titre_service": "Diagnostic structurel planchers bois",
  "client": "",
  "residence": "Rue de varenne",
  "adresse": "46 Rue de Varenne 75007 Paris",
  "ref_dossier": "",
  "date_visite": "2026-04-28",
  "description_batiment": "Hôtel particulier XVIIIe siècle...",
  "objet_visite": "Dans le cadre d'une rénovation complète...",
  "synthese": "Le diagnostic révèle...",
  "conclusion": "",
  "observations": [
    {
      "ref": "OBS-01",
      "zone": "Chambre 1",
      "localisation": "Plancher — côté fenêtre",
      "desordre": "Flèche visible du plancher bois",
      "ie": 3,
      "action": "Contrôle des appuis des solives",
      "photo": "filename.jpg"
    }
  ]
}
```

Zones valides : libre (par pièce ou par type). IE : 1=Critique | 2=Grave | 3=Modéré | 4=Mineur | 5=Bon état

### `suivi_chantier` — Compte-rendu de visite de chantier
Renderer : `render_cr_visite.py` + `templates/ic-ingenieurs/suivi_chantier.docx`

```json
{
  "project_type": "suivi_chantier",
  "titre_service": "Suivi réfection balcons",
  "client": "SDC ...",
  "residence": "Résidence ...",
  "batiments_visites": "Bâtiment A",
  "adresse": "...",
  "code_postal_ville": "93600 Aulnay-sous-Bois",
  "ref_dossier": "DE0328",
  "date_visite": "2026-04-28",
  "participants": [
    {"nom": "R. Laborbe", "fonction": "M.O", "entreprise": "IC Ingénieurs Conseils", "contact": "06 50 96 61 98"}
  ],
  "objet_visite": "IC Ingénieurs Conseils assure le suivi...",
  "synthese": "L'inspection a permis...",
  "conclusion": "La visite confirme...",
  "observations": [
    {
      "ref": "V1-01",
      "etage_facade": "10ème — Façade Est",
      "observation": "Traces de truelle visibles",
      "action": "Reprendre les traces",
      "photo": "photo1.jpg"
    }
  ]
}
```

### `devis` — Rapport préliminaire / demande de devis
Renderer : `render_devis.py` | docxtpl + `templates/ic-ingenieurs/devis.docx`

```json
{
  "project_type": "devis",
  "titre_service": "Diagnostic structurel planchers bois",
  "client": "Nom du client",
  "type_acteur": "Particulier",
  "interlocuteur_nom": "Jean Dupont",
  "interlocuteur_role": "Propriétaire",
  "interlocuteur_contact": "email — tel",
  "type_mission": "Diagnostic",
  "declencheur": "Travaux de rénovation ayant révélé des dégradations structurelles",
  "livrable": "Rapport DOCX avec observations et recommandations",
  "urgence": "Normal",
  "adresse": "46 Rue de Varenne 75007 Paris",
  "type_batiment": "Immeuble résidentiel — hôtel particulier",
  "annee_construction": "XVIIIe siècle",
  "nb_etages": "R+2 + combles",
  "description_batiment": "...",
  "documents_fournis": [
    {"document": "Plans architecte", "fourni": false}
  ],
  "observations": [
    {
      "localisation": "Chambre 1",
      "desordre": "Linteau dégradé, pourriture avancée",
      "donnees_cles": "L=2,20m — section 25×25cm",
      "ref_photo": "P1"
    }
  ],
  "proposition_mission": "Diagnostic structurel complet...",
  "incertitudes": "Accès conditionné à la dépose des faux-plafonds.",
  "chiffrage": [
    {"prestation": "Déplacement terrain", "nb_heures": "2", "montant_ht": ""},
    {"prestation": "Visite terrain", "nb_heures": "3", "montant_ht": ""},
    {"prestation": "Rédaction du rapport", "nb_heures": "4", "montant_ht": ""}
  ],
  "technicien": "R. Laborbe",
  "date_visite": "2026-04-28",
  "date_envoi": ""
}
```

---

## /edifice push

Push the updated `mission/context.json` observations back to Supabase
(`edifice_notes` table).

### Steps

**1. Push**
```bash
python3 $PLUGIN_DIR/push_mission.py "$BRIEFING"
```

The script reads `mission/context.json`, updates each note in Supabase using
its `note_id`, and reports how many were updated.

**2. Confirm to user**
Tell the user how many notes were pushed and whether any errors occurred.

---

## /edifice pair

First-time laptop pairing. Run once per laptop (Mac or Windows).
Requires: Python 3.8+, no external dependencies.

### Steps

**1. Résoudre PLUGIN_DIR** (voir section "Plugin directory" en haut du skill)

**2. Lancer pair.py**
```bash
python3 $PLUGIN_DIR/pair.py
```

Le script :
- Appelle hal-gateway device flow (init → poll)
- Affiche le code à entrer dans la PWA
- Attend la confirmation
- Sauvegarde les credentials dans `~/.edifice-mission-report/config.json`
- Enregistre hal-mcp dans `~/.claude.json`

**3. Dire à l'utilisateur de redémarrer Claude Code**

> "✅ Pairing terminé. **Redémarre Claude Code** pour activer hal-mcp, puis tu pourras utiliser `/edifice pull`."
