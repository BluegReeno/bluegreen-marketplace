---
description: Edifice — inspection missions IC Ingénieurs Conseils (list, pull, improve, report, push)
argument-hint: "list [status=active] [limit=N] | pull | improve | report | push"
allowed-tools: "Bash(uv *) Bash(pip *) Bash(python3 *) Bash(python *) Bash(curl *) Bash(chmod *) Bash(mkdir *) Bash(find *) Bash(ls *) Read Write Edit Glob"
---

Edifice — Argument reçu : `$ARGUMENTS`

---

## 0. Pre-flight : vérifier hal-mcp (list, pull, push)

Appeler `list_edifice_missions` avec `limit: 1` avant `list`, `pull`, ou `push`.

Si indisponible :
> ❌ **hal-mcp non connecté.**
> Reconnexion : **Claude Desktop → Paramètres → Connexions → hal-mcp → Activer**
> ⚠️ Interface graphique uniquement — ne pas utiliser le terminal.

`improve` et `report` ne nécessitent pas MCP — pas de pre-flight pour ces commandes.

---

## Route

**`list [status=<value>] [limit=N]`**
Lister les missions depuis Supabase, plus récentes d'abord.
Appeler `list_edifice_missions` (filtres optionnels : `status`, `limit`).
Tableau : Date | Nom | Type | Statut | Bâtiment / Adresse.
Ne jamais afficher `mission_context`. Afficher les UUIDs après le tableau.

**`pull`**
1. Lire `mission_id` dans `*.edifice.md` (champ `edifice_mission_id`)
2. Appeler `get_mission_with_assets` → obtenir `download_url`
3. `mkdir -p mission && curl -s "$DOWNLOAD_URL" > mission/mcp_response.json` (URL expire en 300 s)
4. `python3 $PLUGIN_DIR/scripts/build_context.py mission/mcp_response.json ./mission --photos-dir ./mission/photos`

**`improve`**
Lire `mission/context.json` (Read tool), comprendre la demande, éditer avec Edit/Write.
Reclasser notes ↔ observations si besoin. Afficher un résumé diff des changements.

**`report`**
```bash
uv run --with "docxtpl>=0.18" --with pillow \
  python3 $PLUGIN_DIR/scripts/render_report.py \
  mission/context.json --photos-dir mission/photos --output mission/rapport.docx
```
Output : `Rapport généré : mission/rapport.docx`

**`push`**
Lire `mission/context.json`, appeler `push_mission_context` avec les observations éditées.
Reporter `{ updated, skipped, errors }`.

---

Pour les instructions complètes (PLUGIN_DIR, schemas JSON, assessment mapping) : charger le skill `edifice` via le menu ou une description naturelle.
