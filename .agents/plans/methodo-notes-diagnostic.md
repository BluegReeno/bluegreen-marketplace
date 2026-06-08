# Plan : Tag methodo — Section Méthodologie dans le rapport diagnostic

**Status**: Ready for Archon  
**Branch**: `feat/methodo-notes-diagnostic`  
**Plugin version**: 0.1.1 → **0.1.2**  
**Issue**: bluegreen-marketplace #6  
**Repo**: bluegreen-marketplace only (PWA changes are in a separate brief — edifice)

---

## Contexte

Le rapport diagnostic IC Ingénieurs a une section **Méthodologie** avec deux paragraphes :
- *Visites terrain réalisées* (`detail_visite` — texte brut)
- *Moyens mis en œuvre* (`investigation_methods` — texte brut)

Aujourd'hui ces champs sont alimentés uniquement en texte brut via `/edifice improve`. Les notes terrain (photos de conditions de visite, photos d'outils utilisés) ne sont pas rendues dans ce rapport.

**Objectif** : les notes taguées `methodo:visite_terrain` ou `methodo:moyens` dans `context.json.notes[]` remontent automatiquement dans la section Méthodologie du rapport diagnostic, avec leur description et leur photo principale.

---

## Tuyauterie de données (ne pas modifier)

```
PWA note.tag = "methodo:visite_terrain"
    ↓ supabase-sync.ts (edifice repo) : metadata = { tag: note.tag, ...note.metadata }
    ↓ Supabase edifice_notes.metadata.tag = "methodo:visite_terrain"
    ↓ hal-mcp get_mission_with_assets → retourne les notes avec metadata
    ↓ build_context.py → routes note.type != "disorder" → notes[] (avec metadata préservé)
    ↓ context.json : notes[n].metadata.tag == "methodo:visite_terrain"
    ↓ render_diagnostic.py (à modifier) → filter → methodo_visite[]
    ↓ diagnostic.docx template (à modifier) → boucle Jinja2
```

`build_context.py` n'a **pas besoin d'être modifié** — `metadata` est déjà préservé dans `notes[]`.

---

## Décisions (ne pas remettre en question, implémenter tel quel)

1. **Photos** : toutes les photos de la note (`note.photos[]`) sont insérées séquentiellement dans le paragraphe, l'une à la suite de l'autre. Si `note.photos` est vide, fallback sur `note.photo`. Le technicien peut améliorer la mise en page manuellement dans le DOCX.
2. **Ordre** : ordre naturel dans `notes[]` (tel que retourné par le MCP, qui respecte `display_order`). Photos dans l'ordre de `note.photos[]`.
3. **Tags** : `methodo:visite_terrain` → "Visites terrain réalisées", `methodo:moyens` → "Moyens mis en œuvre".
4. **Rétrocompat** : `detail_visite` et `investigation_methods` continuent de fonctionner en texte brut si aucune note methodo n'existe.
5. **Photo size** : `max_width_cm=12.0, max_height_cm=8.0` par photo (même contrainte pour toutes).

---

## Fichiers à modifier

| Fichier | Modification |
|---------|-------------|
| `plugins/hal/scripts/render_diagnostic.py` | Ajouter `_render_methodo_item()` + filter dans `_build_context()` |
| `plugins/hal/templates/ic-ingenieurs/diagnostic.docx` | Ajouter boucles Jinja2 dans la section Méthodologie |
| `plugins/hal/skills/edifice/SKILL.md` | Documenter les tags `methodo:*` dans la section "Reclassifying notes ↔ observations" |
| `plugins/hal/CHANGELOG.md` | Ajouter entrée `[0.1.2]` |
| `plugins/hal/.claude-plugin/plugin.json` | `"version": "0.1.2"` |
| `.claude-plugin/marketplace.json` | `"version": "0.1.2"` (doit rester identique à plugin.json) |

---

## Implémentation — render_diagnostic.py

### Nouvelle fonction `_render_methodo_item()`

Ajouter **avant** `_build_context()` :

```python
def _render_methodo_item(note: dict, photos_dir: str, doc: DocxTemplate) -> dict:
    # Collect all photo filenames: prefer photos[] list, fallback to single photo field
    raw_photos = note.get("photos") or ([note["photo"]] if note.get("photo") else [])
    photos_img = []
    for p in raw_photos:
        filename = p if isinstance(p, str) else p.get("path", "") if isinstance(p, dict) else ""
        if not filename:
            continue
        path = Path(photos_dir) / filename
        if path.exists():
            try:
                photos_img.append(_inline_image_auto_orient(doc, path, max_width_cm=12.0, max_height_cm=8.0))
            except Exception:
                pass
    return {
        "name": note.get("name", ""),
        "description": note.get("description", ""),
        "photos": photos_img,  # list of InlineImage (may be empty)
    }
```

### Modifications dans `_build_context()`

Ajouter **après** la boucle qui construit `disorders` et **avant** le `return` :

```python
methodo_visite = [
    _render_methodo_item(n, photos_dir, doc)
    for n in context.get("notes", [])
    if (n.get("metadata") or {}).get("tag") == "methodo:visite_terrain"
]
methodo_moyens = [
    _render_methodo_item(n, photos_dir, doc)
    for n in context.get("notes", [])
    if (n.get("metadata") or {}).get("tag") == "methodo:moyens"
]
```

Ajouter ces deux clés dans le dict retourné par `_build_context()` :

```python
"methodo_visite": methodo_visite,
"methodo_moyens": methodo_moyens,
```

---

## Implémentation — diagnostic.docx template

Le template utilise **docxtpl** (syntaxe Jinja2). Il faut modifier le fichier `.docx` pour ajouter les boucles dans la section Méthodologie.

**Localiser le template** : `plugins/hal/templates/ic-ingenieurs/diagnostic.docx`

**Section à modifier** — la section Méthodologie contient actuellement :
- Un paragraphe ou tableau avec `{{detail_visite}}` (Visites terrain réalisées)
- Un paragraphe ou tableau avec `{{investigation_methods}}` (Moyens mis en œuvre)

**Ce qui doit être ajouté** :

Après le bloc `{{detail_visite}}` :
```
{%p for m in methodo_visite %}
{{ m.description }}
{%p for img in m.photos %}{{ img }}{%p endfor %}
{%p endfor %}
```

Après le bloc `{{investigation_methods}}` :
```
{%p for m in methodo_moyens %}
{{ m.description }}
{%p for img in m.photos %}{{ img }}{%p endfor %}
{%p endfor %}
```

Les photos sont insérées séquentiellement l'une sous l'autre. Le technicien peut réorganiser
la mise en page manuellement dans le DOCX généré.

**Comment modifier le template** :
- Utiliser python-docx pour inspecter le document et identifier les paragraphes contenant `detail_visite` et `investigation_methods`
- Insérer les nouveaux paragraphes avec la syntaxe docxtpl
- Le script de référence pour manipuler les templates est `scripts/prepare_diagnostic_template.py` et `scripts/create_devis_template.py`

**Alternative si la modification python-docx est complexe** : ouvrir le template avec `python-docx`, lire les paragraphes, identifier celui qui contient `detail_visite`, puis insérer après lui les paragraphes de boucle. La syntaxe `{%p ... %}` est une directive de ligne entière dans docxtpl.

---

## Implémentation — SKILL.md

Dans la section `### Reclassifying notes ↔ observations`, ajouter après le paragraphe existant sur la reclassification :

```markdown
### Notes méthodologie — tag `methodo:*`

Pour le service_type `diagnostic`, les notes taguées `methodo:visite_terrain` ou
`methodo:moyens` sont rendues dans la section Méthodologie du rapport :

- `methodo:visite_terrain` → paragraphe *Visites terrain réalisées* (conditions de visite,
  météo, accessibilité, participants)
- `methodo:moyens` → paragraphe *Moyens mis en œuvre* (protocoles expérimentaux, outils :
  ferroscan, pénétromètre, fouilles d'identification)

Ces notes ne doivent pas être dans `observations[]` (elles ne sont pas des désordres).
Le tag est posé sur la PWA au moment de la capture. `detail_visite` et
`investigation_methods` continuent de fonctionner en texte brut si aucune note
`methodo:*` n'existe.
```

---

## Acceptance criteria

- [ ] Une note avec `metadata.tag == "methodo:visite_terrain"` dans `context.json.notes[]` apparaît dans la section *Visites terrain réalisées* du rapport diagnostic
- [ ] Une note avec `metadata.tag == "methodo:moyens"` apparaît dans *Moyens mis en œuvre*
- [ ] Toutes les photos de la note sont rendues séquentiellement sous la description (fallback sur `note.photo` si `note.photos[]` est vide)
- [ ] Une note sans tag `methodo:*` ne remonte pas dans la méthodologie (comportement actuel préservé)
- [ ] `detail_visite` et `investigation_methods` continuent d'afficher leur texte brut même quand des notes methodo existent
- [ ] SKILL.md documente les tags `methodo:*`
- [ ] `plugin.json` version = `0.1.2`, `marketplace.json` version = `0.1.2` (synchronisés)

---

## Tests

Le dossier `plugins/hal/tests/` contient des tests pour `build_context.py`. Vérifier s'il faut ajouter un test pour le filtre methodo dans `render_diagnostic.py`.

Pour valider manuellement : utiliser la mission Jean Jaurès (DEV-168) si un `context.json` exporté est disponible, ou construire un `context.json` minimal avec des notes `methodo:*` dans le tableau `notes[]`.

---

## Commit message

```
feat(hal): methodo notes in diagnostic report — section Méthodologie [0.1.2]
```
