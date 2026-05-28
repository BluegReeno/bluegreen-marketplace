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

# HAL — Obsidian vault updates (Claude Code)

## Path resolution — run at the start of every command

```bash
# Resolve PLUGIN_DIR
PLUGIN_DIR=$(python3 - <<'PYEOF'
import os, pathlib, sys, glob as _glob

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

# Resolve VAULT_PATH
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

---

## /hal update `<texte libre>`

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

Options :
- `--force` : skip la confirmation interactive même si le match est ambigu
- `--dry-run` : afficher le plan sans rien écrire

---

## Vault structure

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

## Field mapping NL → frontmatter

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

## Folder hint (parsing heuristic)

- "candidature", "poste", "entretien" → `CRM-JobSearch/`
- "client", "propale", "devis", "mission" → `CRM-BlueGreen/`
- "tâche", "faire", "task" → `Taches/`
- Pas de hint → recherche dans tout le vault, ranked par relevance

## Fuzzy match thresholds

- Score > 80 : match direct
- Score 50–80 : afficher les candidats, demander à l'utilisateur de choisir
- Score < 50 : note introuvable, proposer création (pas d'auto-création)

## Source de vérité pour les schemas

`hal_update.py` charge `$PLUGIN_DIR/scripts/obsidian/references/schemas.md` au démarrage
pour connaître les 11 types de notes, leurs dossiers et leurs champs frontmatter
valides. Aucun field mapping n'est hardcodé.
