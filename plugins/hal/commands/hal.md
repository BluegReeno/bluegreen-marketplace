---
description: HAL CRM — list pipeline, list tasks, update CRM/tasks, generate devis
argument-hint: "list [workspace] | tasks [workspace] [--mine] [--project <ref>] [--status <s>] | update <texte libre> | devis [--workspace SLUG]"
allowed-tools: "Bash(uv *) Bash(python3 *) Bash(python *) Bash(git *) Bash(mkdir *) Bash(cat *) Read Write Edit Glob"
---

HAL CRM — Argument reçu : `$ARGUMENTS`

---

## 0. Pre-flight : vérifier hal-mcp

Appeler `whoami` (aucun argument) avant toute action. Mettre en cache la réponse pour la commande en cours :
- `default_workspace_slug` (résolution de workspace)
- `workspaces` (memberships, pour les messages d'erreur)
- `user_email` (utilisé par `tasks --mine`)

Si l'outil échoue ou est indisponible :
> ❌ **hal-mcp non connecté.**
> Reconnexion : **Claude Desktop → Paramètres → Connexions → hal-mcp → Activer**
> ⚠️ Ne pas lancer de commandes terminal — interface graphique uniquement.

Stopper si indisponible. Continuer si le call réussit.

---

## Route

### Workspace resolution (commun à `list`, `tasks`, `update`)

1. Arg explicite (`ic` → `ic-ingenieurs-conseils`, autre → tel quel) → utiliser ce slug.
   RLS valide la membership côté serveur ; si non-membre, l'outil MCP renvoie une erreur — l'afficher telle quelle.
2. Pas d'arg → utiliser `default_workspace_slug` depuis la réponse `whoami` cachée par le pre-flight.
   - Non-null → l'utiliser comme `workspace_slug`.
   - Null avec `workspaces` non vide → lister les slugs dispos et demander à l'utilisateur de choisir. Pas de fallback hardcodé.
   - Null avec `workspaces` vide → répondre :
     > ❌ Aucun workspace assigné à ton compte. Demande à ton administrateur BlueGreen d'ajouter ton email aux workspaces concernés dans Supabase.
3. `/hal devis` est l'exception : voir sa section.

### `list [workspace]`

Pipeline CRM en kanban texte groupé par stage.

- Résoudre workspace (voir au-dessus)
- Appeler `list_projects` sans filtre de stage (vue complète)
- Grouper par `stage` : actifs d'abord (projets avec `closed_at` null), terminaux en dernier
- Ligne : `{project_ref ou "—"} · {company.name ou "—"} · {amount_ht formaté ou "—"} · {location ou "—"}`
- Stages terminaux : préfixer `✓ `, ajouter `— soldé/perdu {closed_at[:10]}`
- Aucun projet → `Aucun projet dans le workspace <slug>.`
- Ne jamais afficher le champ `description`
- Filtres optionnels : `stage=<value>`, `kind=<value>`

### `tasks [workspace] [--mine] [--project <ref>] [--status <status>]`

Tâches en kanban texte groupé par statut.

- Résoudre workspace (voir au-dessus)
- Résoudre filtres :
  - `--mine` → `assignee_email` = `user_email` depuis la réponse `whoami` cachée (ne jamais demander)
  - `--project <ref>` → `list_projects` pour résoudre `project_id`, puis filtrer
  - `--status <value>` → filtrer (`todo` | `in_progress` | `done` | `blocked`)
- Appeler `list_tasks` avec `workspace_slug` (+ filtres)
- Grouper par `status` dans l'ordre fixe : `todo` → `in_progress` → `blocked` → `done`
- `done` est terminal → préfixer `✓ ` dans le header
- Ligne : `{⚡ si priority=high}{title} · {assignee short ou "—"} · {due_date ou "—"} {[S] si sprint_id non null}`
  - `assignee short` = partie locale de `assignee_email` (avant `@`)
  - `[S]` = marker si `sprint_id` non null
- Aucune tâche → `Aucune tâche dans le workspace <slug>.`
- Groupe vide → ne pas afficher la section
- `list_tasks` retourne `project_id` brut (UUID) — colonne omise sauf si `--project` utilisé

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
| "mes tâches", "todo list", "qu'est-ce que j'ai à faire" | `list_tasks` (workspace default) |
| "ajouter tâche X", "todo : X", "créer une tâche" | `create_task` |
| "tâche X faite", "X → done", "c'est fait" | `list_tasks` → fuzzy match → `update_task_status` (done) |
| "X → in progress", "je commence X" | `list_tasks` → fuzzy match → `update_task_status` (in_progress) |
| "X bloqué", "X → blocked" | `list_tasks` → fuzzy match → `update_task_status` (blocked) |
| "X → todo", "remettre X en attente" | `list_tasks` → fuzzy match → `update_task_status` (todo) |
| "nouveau sprint S<N>" | `create_sprint` |
| "assigne tâche X au sprint Y" | `list_tasks` → match → `assign_task_to_sprint` |

Workspace résolu via la règle "Workspace resolution" ci-dessus (arg explicite ou
`whoami.default_workspace_slug`). Confirmer avant toute écriture ambiguë.
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
