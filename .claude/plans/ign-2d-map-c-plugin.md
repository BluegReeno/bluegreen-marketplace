# Plan C — IGN 2D Map : Plugin edifice-mission-report
**Repo** : `bluegreen-marketplace` (`/Users/renaud/Projects/bluegreen-marketplace`)
**Branche Archon** : `feat/ign-2d-map-c-plugin`
**Dépendances** : Plan A (edifice) doit être déployé — `get_mission_with_assets` doit retourner `latitude`, `longitude`, `building_2d_map_url`

---

## Contexte

Le plugin génère des rapports DOCX depuis les missions Edifice. Les variables `building.image_2d` et `building.image_2d_url` sont déjà **documentées** dans `TEMPLATE_VARIABLES.md` mais **pas encore implémentées** dans le code ni dans le template. Ce plan implémente le pipeline complet :

1. Template `.docx` — ajouter le placeholder image 2D
2. `build_context.py` — télécharger l'image depuis `building_2d_map_url` (ou générer via IGN WMS si null)
3. `render_diagnostic.py` — injecter l'image dans le docxtpl

---

## Préambule : identifier les chemins exacts

**Avant de commencer**, lister les fichiers du plugin pour confirmer les chemins :
```bash
find /Users/renaud/Projects/bluegreen-marketplace/plugins/edifice-mission-report -name "*.py" -o -name "*.docx" | head -30
```

Les chemins attendus (à ajuster si différents) :
- `plugins/edifice-mission-report/scripts/build_context.py`
- `plugins/edifice-mission-report/scripts/render_diagnostic.py`
- `plugins/edifice-mission-report/templates/ic-ingenieurs/diagnostic.docx`

---

## Tâche 1 — Template DOCX : ajouter le placeholder image 2D

**Fichier** : `plugins/edifice-mission-report/templates/ic-ingenieurs/diagnostic.docx`

Ouvrir le template avec un éditeur Word compatible (LibreOffice, Word). Dans la section "Présentation du bâtiment" (ou équivalent), ajouter un bloc image avec syntaxe docxtpl :

```
{%p if building.image_2d %}
{{ building.image_2d | image(width=150) }}
Localisation — vue cartographique IGN
{%p endif %}
```

**Règles docxtpl importantes** :
- `{%p ... %}` = balise de niveau paragraphe (supprime le paragraphe entier si false)
- `| image(width=150)` = largeur en mm (150mm = pleine page avec marges standard)
- Le bloc `{%p if %}...{%p endif %}` doit tenir sur des paragraphes séparés dans Word
- Positionner le bloc APRÈS le bloc `building.image_3d` existant s'il y en a un, ou dans la section description bâtiment

**Vérifier** après édition que la syntaxe docxtpl est valide (pas de guillemets Word typographiques qui cassent le parsing).

---

## Tâche 2 — `build_context.py` : télécharger ou générer l'image 2D

**Fichier** : `plugins/edifice-mission-report/scripts/build_context.py`

### 2a — Récupérer les champs building depuis le contexte MCP

Le JSON retourné par `get_mission_with_assets` contient maintenant dans `building` :
- `latitude`, `longitude`
- `building_2d_map_url` (URL Supabase Storage, ou null)

Extraire ces champs dans la section building du contexte :

```python
building_data = mcp_response.get("building") or {}
building_2d_map_url = building_data.get("building_2d_map_url")
latitude  = building_data.get("latitude")
longitude = building_data.get("longitude")
```

### 2b — Télécharger l'image si URL disponible

```python
import requests
import os

def download_building_2d_map(url: str, building_id: str, output_dir: str) -> str | None:
    """Télécharge building_2d_map_url → fichier local. Retourne le path local."""
    if not url:
        return None
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        # Vérifier qu'on a bien une image
        ct = resp.headers.get("Content-Type", "")
        if "xml" in ct or "text" in ct:
            return None
        local_path = os.path.join(output_dir, f"{building_id}_2d_map.png")
        with open(local_path, "wb") as f:
            f.write(resp.content)
        return local_path
    except Exception as e:
        print(f"[build_context] Warning: could not download 2D map: {e}")
        return None
```

### 2c — Fallback : générer via IGN WMS si URL absente

Déclenché si `building_2d_map_url` est null MAIS que `latitude` et `longitude` existent. Cette génération côté client est le filet de sécurité pour les bâtiments créés avant le déploiement de l'Edge Function.

```python
import math

def generate_ign_map(lat: float, lon: float, output_path: str, radius_m: int = 300) -> str | None:
    """Génère une carte IGN WMS GetMap. Retourne le path local ou None en cas d'erreur."""
    delta_lat = radius_m / 111320
    delta_lon = radius_m / (111320 * math.cos(math.radians(lat)))
    # WMS 1.3.0 + EPSG:4326 : ordre bbox = minLat, minLon, maxLat, maxLon
    bbox = f"{lat - delta_lat},{lon - delta_lon},{lat + delta_lat},{lon + delta_lon}"

    params = {
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "REQUEST": "GetMap",
        "LAYERS": "ORTHOIMAGERY.ORTHOPHOTOS,GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2",
        "FORMAT": "image/png",
        "CRS": "EPSG:4326",
        "BBOX": bbox,
        "WIDTH": "800",
        "HEIGHT": "600",
        "STYLES": "",
    }

    try:
        resp = requests.get("https://data.geopf.fr/wms-r", params=params, timeout=30)
        resp.raise_for_status()
        ct = resp.headers.get("Content-Type", "")
        if "xml" in ct or "text" in ct:
            print(f"[build_context] IGN WMS error: {resp.text[:200]}")
            return None
        with open(output_path, "wb") as f:
            f.write(resp.content)
        return output_path
    except Exception as e:
        print(f"[build_context] Warning: IGN WMS fallback failed: {e}")
        return None
```

### 2d — Orchestration dans `build_context.py`

```python
# Dans la fonction principale de construction du contexte building

image_2d_local = None

if building_2d_map_url:
    image_2d_local = download_building_2d_map(
        url=building_2d_map_url,
        building_id=building_data.get("id", "unknown"),
        output_dir=output_dir,
    )

if image_2d_local is None and latitude and longitude:
    print("[build_context] building_2d_map_url absent — fallback IGN WMS generation")
    fallback_path = os.path.join(output_dir, f"{building_data.get('id', 'unknown')}_2d_map_auto.png")
    image_2d_local = generate_ign_map(lat=latitude, lon=longitude, output_path=fallback_path)

# Ajouter au contexte building (utilisé par render_diagnostic.py)
building_context = {
    # ... champs existants ...
    "image_2d":     image_2d_local,        # chemin local absolu, ou None
    "image_2d_url": building_2d_map_url,   # URL d'origine (pour traçabilité)
}
```

---

## Tâche 3 — `render_diagnostic.py` : injecter l'image dans docxtpl

**Fichier** : `plugins/edifice-mission-report/scripts/render_diagnostic.py`

### 3a — Vérifier comment les images existantes sont injectées

Chercher dans le fichier comment `InlineImage` est utilisé pour les photos de désordres. La pattern docxtpl standard est :

```python
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm

# Dans la préparation du contexte de rendu :
if building.get("image_2d"):
    building["image_2d"] = InlineImage(
        doc,
        image_descriptor=building["image_2d"],
        width=Mm(150),
    )
```

### 3b — Implémenter l'injection

Dans la fonction de rendu, avant l'appel `doc.render(context)`, ajouter le traitement de `building.image_2d` :

```python
# Traiter l'image 2D du bâtiment
building = context.get("building", {})
if building.get("image_2d") and os.path.exists(building["image_2d"]):
    building["image_2d"] = InlineImage(
        doc,
        image_descriptor=building["image_2d"],
        width=Mm(150),
    )
else:
    building["image_2d"] = None  # Le {%p if %} dans le template gérera l'absence
```

**Note** : si `_inline_image_auto_orient()` est déjà utilisé pour les photos de désordres, appliquer la même fonction pour l'image 2D (auto-rotation EXIF). Les captures IGN n'ont pas d'EXIF de rotation mais les captures webapp via canvas peuvent en avoir.

---

## Tâche 4 — Tests

### Test unitaire rapide (hors Cowork)

```bash
cd /Users/renaud/Projects/bluegreen-marketplace/plugins/edifice-mission-report/scripts

python build_context.py --mission-id <uuid> --output-dir /tmp/test_2d_map/
# Vérifier que /tmp/test_2d_map/<building_id>_2d_map.png existe

python render_diagnostic.py --context /tmp/test_2d_map/context.json --output /tmp/rapport_test.docx
# Ouvrir rapport_test.docx et vérifier que la carte 2D apparaît dans la section bâtiment
```

### Test via Cowork (final)

```
/edifice pull <mission_id>
/edifice report
```

Vérifier dans le rapport DOCX généré :
- La carte IGN 2D est présente dans la section bâtiment
- Si le bâtiment a `building_2d_map_url` → image fidèle à la capture webapp
- Si le bâtiment n'a pas d'URL → image générée automatiquement depuis les coordonnées

---

## Fichiers créés/modifiés

| Fichier | Action |
|---------|--------|
| `plugins/edifice-mission-report/templates/ic-ingenieurs/diagnostic.docx` | Modifier — ajouter placeholder `building.image_2d` |
| `plugins/edifice-mission-report/scripts/build_context.py` | Modifier — télécharger/générer image 2D |
| `plugins/edifice-mission-report/scripts/render_diagnostic.py` | Modifier — injecter InlineImage dans docxtpl |
