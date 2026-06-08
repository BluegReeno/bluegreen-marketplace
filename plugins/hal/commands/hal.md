---
description: HAL CRM — list pipeline, update projects, log interactions, generate devis
argument-hint: "list [workspace] | update <texte libre> | devis [--workspace SLUG]"
allowed-tools: "Bash(uv *) Bash(python3 *) Bash(python *) Bash(git *) Bash(mkdir *) Bash(cat *) Read Write Edit Glob"
---

HAL CRM — Argument reçu : `$ARGUMENTS`

---

## 0. Pre-flight : vérifier hal-mcp

Appeler `list_stages` avec `workspace_slug: "blue-green"` avant toute action.

Si l'outil échoue ou est indisponible :
> ❌ **hal-mcp non connecté.**
> Reconnexion : **Claude Desktop → Paramètres → Connexions → hal-mcp → Activer**
> ⚠️ Ne pas lancer de commandes terminal — interface graphique uniquement.

Stopper si indisponible. Continuer si le call réussit.

---

## Route

### `list [workspace]` (défaut : `blue-green`)

Pipeline CRM en kanban texte groupé par stage.

- Résoudre workspace : `ic` / `ic-ingenieurs-conseils` → `"ic-ingenieurs-conseils"` ; autre arg → tel quel ; sans arg → `"blue-green"`
- Appeler `list_projects` sans filtre de stage (vue complète)
- Grouper par `stage` : actifs d'abord (projets avec `closed_at` null), terminaux en dernier
- Ligne : `{project_ref ou "—"} · {company.name ou "—"} · {amount_ht formaté ou "—"} · {location ou "—"}`
- Stages terminaux : préfixer `✓ `, ajouter `— soldé/perdu {closed_at[:10]}`
- Aucun projet → `Aucun projet dans le workspace <slug>.`
- Ne jamais afficher le champ `description`
- Filtres optionnels : `stage=<value>`, `kind=<value>`

### `update <texte libre>`

| Intention | Outils MCP |
|-----------|-----------|
| "propale envoyée", "stage → X" | `list_projects` (filtré) → fuzzy match → `update_project_stage` |
| "perdu", "refus", "dead", "sans suite" | `update_project_stage` → stage `perdu` |
| "gagné", "signé", "soldé" | `update_project_stage` → stage `solde` |
| "call avec", "RDV", "mail envoyé" | `list_contacts` → `log_interaction` |
| "nouveau client [nom]" | `create_company` |
| "nouveau contact [nom] chez [client]" | `list_companies` → `create_contact` |
| "nouvelle mission/propale" | `list_companies` → `create_project` |

Toujours `workspace_slug: "blue-green"`. Confirmer avant toute écriture ambiguë.
Output : `✅ [Entité] → [tool]: [valeur]` / `❌ [Entité] → [tool]: [erreur]`

### `devis [--workspace SLUG]`

DOCX devis IC Ingénieurs Conseils (défaut) ou Blue Green.

1. Collecter : `client.name`, `project.name`, `scope`, `workpackages` (ref, title, price)
2. `HAL_ROOT=$(git -C "$(pwd)" rev-parse --show-toplevel 2>/dev/null || echo "$HOME/Projects/hal")`
3. `mkdir -p /tmp/hal_devis` puis écrire `/tmp/hal_devis/context.json` (Write tool)
4. `cd "$HAL_ROOT" && uv run python scripts/generate_devis.py --workspace <slug> --json /tmp/hal_devis/context.json`
5. Output : `✅ Devis généré : <chemin absolu>`

---

Pour les instructions complètes et les règles d'entité resolution : charger le skill `hal` via le menu (`hal:hal`) ou une description naturelle.
