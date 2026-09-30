---
name: brand
description: >
  Identité visuelle et légale de Blue Green (couleurs, police Poppins, logo,
  insigne, mentions légales SIRET/RCS, coordonnées) et rendu des documents Word
  à la charte à partir d'un Markdown. Déclencher dès qu'un livrable Blue Green
  sort en .docx ou doit être « à la charte » : convention, note, compte rendu,
  courrier, mise au propre d'un Word existant, ou quand un autre skill
  (docs:study-report, docs:proposal) demande le rendu. Fournit aussi les valeurs
  de marque pour tout autre support (page HTML, email, slides).
allowed-tools: "Bash(uv *) Bash(python3 *) Bash(pandoc *) Bash(soffice *) Bash(pdftoppm *) Bash(mkdir *) Read Write Edit Glob"
---

# Brand — charte Blue Green

Deux rôles :
1. **Identité** — `brand.yaml` est la seule source des couleurs, de la police, des mentions
   légales et des coordonnées ; `assets/` porte le logo, l'insigne et les visuels.
   Ne jamais recopier une de ces valeurs ailleurs : la lire ici.
2. **Rendu Word** — on écrit en Markdown, `scripts/md2docx.py` applique la charte.
   Aucune mise en forme à la main dans le Word.

Le contenu d'un rapport d'étude ou d'une proposition commerciale ne vit pas ici :
`docs:study-report` et `docs:proposal` le portent, puis reviennent ici pour le rendu.

## Plugin directory

```bash
PLUGIN_DIR=$(python3 - <<'PYEOF'
import glob, os, pathlib, sys
home = pathlib.Path.home()
env = os.environ.get('DOCS_PLUGIN_DIR', '')
if env and pathlib.Path(env, 'scripts', 'md2docx.py').exists():
    print(env); sys.exit(0)
cache = home / '.claude' / 'plugins' / 'cache' / 'bluegreen-marketplace' / 'docs'
hits = sorted(cache.glob('*/scripts/md2docx.py'), key=lambda p: p.stat().st_mtime, reverse=True)
hits += sorted((pathlib.Path(p) for p in glob.glob('/sessions/*/mnt/.remote-plugins/*/scripts/md2docx.py')),
               key=lambda p: p.stat().st_mtime, reverse=True)
for dev in [home / 'Projects' / 'bluegreen-marketplace' / 'plugins' / 'docs',
            home / 'projects' / 'bluegreen-marketplace' / 'plugins' / 'docs']:
    if (dev / 'scripts' / 'md2docx.py').exists():
        hits.append(dev / 'scripts' / 'md2docx.py')
print(hits[0].parent.parent if hits else 'PLUGIN_DIR_NOT_FOUND')
PYEOF
)
[ "$PLUGIN_DIR" = "PLUGIN_DIR_NOT_FOUND" ] && echo "ERROR: plugin docs introuvable. Définis DOCS_PLUGIN_DIR=<chemin>." && exit 1
```

## Rendu d'un document

1. Partir d'un Markdown avec front matter. Pour un document simple (note, convention,
   courrier, CR), copier `$PLUGIN_DIR/skills/brand/templates/document.md`.
2. Rester dans la syntaxe supportée — `references/markdown-support.md` au moindre doute.
3. Convertir :

   ```bash
   uv run --with python-docx --with pyyaml --with pypdf \
     python3 "$PLUGIN_DIR/scripts/md2docx.py" mon-doc.md -o mon-doc.docx --pdf
   ```

   Si `pandoc` est absent du poste : ajouter `--with pypandoc_binary`.
   `--pdf` produit aussi le PDF (LibreOffice, déjà présent dans Cowork et le bac à sable de
   Claude) ; les champs `{{?…}}` y deviennent des champs à remplir. Le sommaire y apparaît
   vide, Word le calcule à l'ouverture.
4. Contrôler le PDF en image (`pdftoppm -r 50 -png`) : page de garde, tableaux, sauts de page.
5. Livrer le .docx **et** le .md source.

### Mettre un Word existant à la charte

`pandoc source.docx -t markdown-simple_tables-multiline_tables-grid_tables --wrap=none -o source.md`,
puis nettoyer : titres en gras → `##`, blocs « **Libellé :** valeur » → tableau libellé/valeur,
tableaux HTML → tableaux pipe (ou grid si une cellule contient plusieurs paragraphes).
Ne pas toucher au texte.

## Champs à remplir

Le Markdown est la source que l'on relit et complète ; les trous restants se déclarent :

- `{{?Libellé}}` — champ nommé d'après le libellé ;
- `{{?JJ/MM/AAAA#date_client}}` — nom explicite, **obligatoire quand deux champs ont le même
  libellé** (sinon ils partagent la même valeur dans le PDF).

Dans le .docx, le champ est une case Word (contrôle de contenu) à fond bleu clair ; dans le PDF,
un champ de formulaire vide. La signature ne passe pas par un champ : le client signe avec
« Remplir et signer » (Acrobat Reader) ou Aperçu.

Ne jamais retoucher le .docx à la main : modifier le .md et réexporter.

## Front matter

```yaml
---
type: document              # document | report | proposal
title: "Titre"              # repris dans l'en-tête
subtitle: "Sous-titre"      # facultatif
client: "Destinataire"      # page de garde
date: "Septembre 2026"
header: "Texte d'en-tête"   # facultatif, remplace title dans l'en-tête
# surcharges : cover: true|false, toc: true|false, blue_green_page: true|false
---
```

| `type` | Page de garde | Sommaire | Page Blue Green |
|---|:-:|:-:|:-:|
| `document` | — | — | — |
| `report` | ✓ | ✓ | — |
| `proposal` | — | — | ✓ |

## Règles

- Aucune couleur, police ou taille dans le Markdown : tout vient de `brand.yaml`.
- `\newpage` seul sur sa ligne = saut de page.
- `<!-- blue-green-page -->` = position de la page Blue Green (sinon en fin de document) ;
  son contenu est `templates/blue-green-page.md`.
- `{{contact.email}}`, `{{company.legal_notice}}`… insèrent les valeurs de `brand.yaml`.
- Images : chemin relatif au .md, largeur en % (`{width=80%}`).

## Autres supports

Pour une page HTML, un email ou des slides : reprendre les couleurs, la police et les
mentions de `brand.yaml`, et les visuels de `assets/`. Ce skill ne produit pas de .pptx.
