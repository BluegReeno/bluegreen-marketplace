---
description: PM — gestion de projet interne Blue Green (tâches, sprints, projets, docs, notes)
argument-hint: "list [workspace] | tasks [workspace] [--mine] [--project <ref>] [--status <s>] [--all] [--tag <tag>] | new <projet> | task <titre> | log <note> | doc <url> | sprint | update <texte libre>"
allowed-tools: "Bash(uv *) Bash(python3 *) Bash(python *) Bash(git *) Bash(mkdir *) Bash(cat *) Read Write Edit Glob"
---

PM — Argument reçu : `$ARGUMENTS`

---

## 0. Pre-flight : vérifier hal-mcp

Appeler `whoami` (aucun argument) avant toute action. Mettre en cache la réponse :
- `default_workspace_slug` (résolution de workspace)
- `workspaces` (memberships, pour les messages d'erreur)
- `user_email` (utilisé par `tasks --mine`)

Si l'outil échoue ou est indisponible :
> ❌ **hal-mcp non connecté.**
> Reconnexion : **Claude Desktop → Paramètres → Connexions → hal-mcp → Activer**
> ⚠️ Ne pas lancer de commandes terminal — interface graphique uniquement.
> Relancer la commande après reconnexion.

Stopper si indisponible. Continuer si le call réussit.

---

## Route

### Workspace resolution (commun à toutes les sous-commandes)

1. Arg explicite (`ic` → `ic-ingenieurs-conseils`, autre → tel quel) → utiliser ce slug.
   RLS valide la membership côté serveur ; erreur MCP → afficher telle quelle.
2. Pas d'arg → utiliser `default_workspace_slug` depuis le cache `whoami`.
   - Non-null → l'utiliser.
   - Null avec `workspaces` non vide → lister les slugs et demander.
   - Null avec `workspaces` vide → `❌ Aucun workspace assigné à ton compte.`

---

### `list [workspace]`

Projets en kanban texte groupé par stage.

- Résoudre workspace (voir ci-dessus)
- Appeler `list_projects` sans filtre de stage (vue complète)
- Grouper par `stage` : actifs d'abord (projets avec `closed_at` null), terminaux en dernier
- Ligne : `{project_ref ou "—"} · {company.name ou "—"} · {amount_ht formaté ou "—"} · {location ou "—"} {#tag1 #tag2 si tags non vide}`
- Stages terminaux : préfixer `✓ `, ajouter `— terminé {closed_at[:10]}`
- Aucun projet → `Aucun projet dans le workspace <slug>.`
- Ne jamais afficher le champ `description`
- Filtres optionnels : `stage=<value>`, `kind=<value>`

---

### `tasks [workspace] [--mine] [--project <ref>] [--status <status>] [--all] [--tag <tag>]`

Tâches en kanban texte groupé par statut. **Scope par défaut : le sprint actuel.**

- Résoudre workspace (voir ci-dessus)
- **Résoudre le scope** :
  - **Mode requête explicite** (si `--status`, `--project`, `--all` ou `--tag`) → pas de
    scoping sprint, interroger le workspace directement. Flags en AND,
    sauf `--all` ignoré si un autre filtre est présent :
    - `--status <value>` → filtrer (`todo` | `in_progress` | `done` | `blocked`)
    - `--project <ref>` → `list_projects` pour résoudre `project_id`, puis filtrer
    - `--all` → aucun filtre, toutes les tâches du workspace
    - `--tag <value>` → passer `tags=["<value>"]` à `list_tasks`
  - **Mode sprint actuel** (défaut, aucun de ces flags) :
    1. `list_sprints(workspace_slug, status="actuel")`
    2. Sprint trouvé → filtrer `list_tasks` par `sprint_id` ; retenir `name` pour le header
    3. Aucun sprint actuel → `⚠️ Aucun sprint actuel dans <slug>. Affichage des tâches ouvertes du workspace.` puis `list_tasks` sans filtre sprint, en omettant le groupe `done`. **Jamais de board vide silencieux.**
  - `--mine` : filtre dans les deux modes → `assignee_email = user_email` du cache `whoami`
- Appeler `list_tasks` avec `workspace_slug` (+ filtres résolus)
- Ligne de scope en tête : `**<nom sprint>** · workspace <slug>`
  (ou `**Toutes les tâches**`, `**Statut : <s>**`, `**Tag : <valeur>**`, ou le ⚠️ du fallback)
- Grouper par `status` dans l'ordre fixe : `todo` → `in_progress` → `blocked` → `done`
- `done` est terminal → préfixer `✓ ` (omis dans le fallback sans sprint)
- Ligne : `{⚡ si priority=high}{title} · {assignee short ou "—"} · {due_date ou "—"} {[S] si sprint_id non null} {#tag1 #tag2 si tags non vide}`
- Aucune tâche → `Aucune tâche dans le workspace <slug>.` ; sprint actuel vide → `Aucune tâche dans le sprint « <nom> ».`

---

### `new <nom du projet>`

Créer un projet interne.

- Résoudre workspace
- Collecter `name` (requis, depuis l'argument), `description` et `kind` (optionnels)
- Appeler `create_project` avec `workspace_slug`, `name`, champs optionnels disponibles
- Output : `✅ Projet créé : <ref> · <name>`

---

### `task <titre>`

Créer une tâche.

- Résoudre workspace
- Titre depuis l'argument (requis)
- Champs optionnels si présents dans le contexte : `project_id` (fuzzy match `list_projects`),
  `due_date`, `assignee_email`, `priority`, `sprint_id` (résolu via `list_sprints(status="actuel")`)
- Appeler `create_task` avec `workspace_slug` et les champs collectés
- Output : `✅ Tâche créée : <title>`

---

### `log <note>`

Logger une note/interaction interne sur un projet.

- Résoudre workspace
- Identifier le projet depuis le contexte (fuzzy match `list_projects`). Si ambigu, demander.
- Appeler `log_interaction` avec `workspace_slug`, `channel` (meeting par défaut),
  `summary`, `project_id`
- Si projet introuvable (score < 50) → logger quand même, mettre le nom dans `summary`
- Output : `✅ Note loguée sur <projet>`

---

### `doc <url ou markdown>`

Attacher un document à un projet.

- Résoudre workspace
- Identifier le projet depuis le contexte. Si ambigu, demander.
- Appeler `save_document` avec `workspace_slug`, `title` (inférer ou demander),
  `content`, `project_id`
- Output : `✅ Document attaché : <title> → <projet>`

---

### `sprint`

Voir/créer/mettre à jour les sprints.

- Résoudre workspace
- Pas de sous-argument → `list_sprints(workspace_slug, status="actuel")` ; afficher nom, dates, statut
  (au plus un sprint `actuel` par workspace depuis hal-mcp v61 ; zéro reste possible — ne
  jamais en choisir un autre par défaut, afficher le message d'absence)
- "nouveau sprint S<N>", "créer sprint" → collecter `name`, `starts_at`, `ends_at` (optionnels),
  appeler `create_sprint`
- "renomme le sprint", "change le statut du sprint en X" (X ≠ `actuel`) → `list_sprints` → match →
  `update_sprint(workspace_slug, sprint_id, ...)` ; valeurs `status` valides :
  `passes` / `dernier` / `actuel` / `suivant` / `a_venir`
- "le sprint est actuel", "passe le sprint X en actuel" → `list_sprints` → match →
  `transition_sprint(workspace_slug, incoming_sprint_id)` — **jamais** `update_sprint` pour ce
  cas : un index unique partiel interdit un second `actuel`, et `update_sprint` refuse
  l'écriture. `transition_sprint` rétrograde l'`actuel` sortant en `dernier` et promeut
  l'entrant en `actuel`, en une seule transaction.

---

### `update <texte libre>`

| Intention | Outils MCP |
|-----------|-----------|
| "mes tâches", "todo list" | `list_tasks` (workspace default) |
| "ajouter tâche X", "todo : X", "créer une tâche" | `create_task` |
| "repousse X à lundi", "change l'échéance de X", "renomme X", "réassigne X", "X priorité haute" | `list_tasks` → fuzzy match → `update_task` (attributs : `title`, `description`, `due_date`, `project_id`, `assignee_email`, `priority`, `external_ref` — **pas** `status`/`sprint`) |
| "tâche X faite", "X → done", "c'est fait" | `list_tasks` → fuzzy match → `update_task_status` (done) |
| "X → in progress", "je commence X" | `list_tasks` → fuzzy match → `update_task_status` (in_progress) |
| "X bloqué", "X → blocked" | `list_tasks` → fuzzy match → `update_task_status` (blocked) |
| "X → todo", "remettre X en attente" | `list_tasks` → fuzzy match → `update_task_status` (todo) |
| "nouveau sprint S<N>" | `create_sprint` |
| "renomme le sprint", "statut du sprint → X" (X ≠ actuel) | `list_sprints` → match → `update_sprint` |
| "le sprint est actuel" | `list_sprints` → match → `transition_sprint` |
| "assigne tâche X au sprint Y" | `list_tasks` → match → `assign_task_to_sprint` |
| "nouveau projet interne [nom]" | `create_project` |
| "logger une note sur [projet]" | `log_interaction` (channel: meeting) |

Workspace résolu via la règle ci-dessus. Confirmer avant toute écriture ambiguë.
Output : `✅ [Entité] → [tool]: [valeur]` / `❌ [Entité] → [tool]: [erreur]`

---

Pour les instructions complètes et les règles de fuzzy match : charger le skill `pm` via le menu (`hal:pm`) ou une description naturelle.
