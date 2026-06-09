---
name: project-distribution
description: How the bluegreen-marketplace plugin is installed and updated by Renaud — Claude Desktop GUI, version-driven updates
metadata:
  type: project
---

Renaud installe le plugin `hal` via **Claude Desktop → Customize → Plugins personnels**.
Les mises à jour s'appliquent via le bouton "Mettre à jour" dans cette même interface — pas en CLI.

Claude Desktop compare `marketplace.json → plugins[0].version` (remote) avec la version installée localement. Le bouton "Mettre à jour" n'apparaît QUE si la version remote > version installée.

**Why:** C'est le seul mécanisme de distribution réel. Sans bump de version, Renaud (et tout autre client) reste bloqué sur l'ancienne version même après un `git push`.

**How to apply:** Chaque release DOIT bumper `marketplace.json` ET `plugin.json` (version identique). Sans ça, les nouvelles features (nouvelles commandes, nouveaux skills) ne seront jamais livrées. Vérifier le sync avec le script de validation avant chaque commit.

Screenshot confirmé 2026-06-09 : version 0.4.0 affichée dans Claude Desktop pendant que le repo était à 0.6.0 — l'update était disponible via le bouton "Mettre à jour".

[[project-versioning-policy]]
