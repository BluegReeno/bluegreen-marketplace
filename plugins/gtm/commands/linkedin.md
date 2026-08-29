---
description: LinkedIn — gestion de contenu éditorial (idées, backlog, tendances, drafts, publications)
argument-hint: "idea <titre> | backlog [workspace] | trend [sujet] | draft <titre> | log <titre>"
allowed-tools: "Bash(uv *) Bash(python3 *) Bash(python *) Bash(git *) Bash(mkdir *) Bash(cat *) Read Write Edit Glob"
---

LinkedIn — Argument reçu : `$ARGUMENTS`

---

## 0. Pre-flight : vérifier hal-mcp

Requis pour `idea`, `backlog`, `draft`, `log`. **Pas nécessaire pour `trend`.**

Appeler `whoami` (aucun argument) avant toute action hal-mcp. Mettre en cache :
- `default_workspace_slug` (résolution de workspace)
- `workspaces` (memberships, pour les messages d'erreur)
- `user_email` (filtres assignee si besoin)

Si l'outil échoue ou est indisponible :
> ❌ **hal-mcp non connecté.**
> Reconnexion : **Claude Desktop → Paramètres → Connexions → hal-mcp → Activer**
> ⚠️ Ne pas lancer de commandes terminal — interface graphique uniquement.
> Relancer la commande après reconnexion.

Stopper si indisponible. Continuer si le call réussit.

**Les idées LinkedIn = tâches hal taguées `marketing`** (le workspace `blue-green`
n'autorise pas de tag `linkedin` dédié — voir `allowed_tags`). Toujours passer
`tags: ["marketing"]` à `list_tasks` et à `create_task`.

---

## Workspace resolution (commun à toutes les sous-commandes hal-mcp)

1. Arg explicite → utiliser ce slug directement.
2. Pas d'arg → utiliser `default_workspace_slug` depuis le cache `whoami`.
   - Non-null → l'utiliser.
   - Null avec `workspaces` non vide → lister les slugs et demander.
   - Null avec `workspaces` vide → `❌ Aucun workspace assigné à ton compte.`

---

### Tags (s'applique à toute écriture `tags`)

**Tags.** `tags` means functional domain. Pick only from the calling workspace's `allowed_tags`, returned by `whoami`; if nothing fits, use `other`. Never invent a value, and never put in `tags` what another column already carries (`company_id`, `role`, `channel`, `project_id`). hal-mcp states the full doctrine in its server `instructions` and enforces it on every write.

---

### `idea <titre>`

Capturer une idée de post LinkedIn.

- Pre-flight (hal-mcp)
- Résoudre workspace
- `title` depuis l'argument (requis)
- Champs optionnels depuis le contexte : `description` (angle, message clé), `due_date`
- Appeler `create_task(workspace_slug, title, tags=["marketing"], description?, due_date?)`
- Output : `✅ Idée créée : <titre>`

---

### `backlog [workspace]`

Backlog éditorial LinkedIn groupé par statut.

- Pre-flight (hal-mcp)
- Résoudre workspace
- Appeler `list_tasks(workspace_slug, tags=["marketing"])`
- Grouper par `status` (cinq statuts possibles — hal#98), ordre fixe :
  `todo` → `in_progress` → `blocked` → `done` → `cancelled`
- `blocked` → section dédiée entre `in_progress` et `done`, préfixer `⛔ `
- `done` est terminal → préfixer `✓ `
- `cancelled` est terminal → section dédiée en dernier (après `done`), préfixer `✗ `
- Ligne : `{⚡ si priority=high}{title} · {assignee short ou "—"} · {due_date ou "—"}`
- Groupes vides → ne pas afficher la section
- Aucune tâche (tous statuts confondus) → `Aucune idée LinkedIn dans le workspace <slug>.`

---

### `trend [sujet]`

Tendances LinkedIn via Bright Data — **aucun pre-flight hal-mcp**.

- Construire requête : `"LinkedIn trending posts [sujet] 2026"` (ou sujet par défaut BlueGreen IA)
- Appeler `search_engine` avec la requête
- Appeler `web_data_linkedin_posts` pour des exemples de posts engageants
- Afficher : thèmes en traction (3–5), posts remarquables (2–3), insights formats
- Fallback : si `web_data_linkedin_posts` échoue → continuer avec `search_engine` seul et le signaler

---

### `draft <titre>`

Rédiger un post LinkedIn et le sauvegarder.

- Pre-flight (hal-mcp)
- Résoudre workspace
- Fuzzy match sur `list_tasks(tags=["marketing"])` pour trouver la tâche liée
  (seuils : > 80 match ; 50–80 lister candidats ; < 50 rédiger sans tâche liée)
- Rédiger le post (pur Claude) : accroche 1 ligne, 3–5 paragraphes courts, CTA, 3–5 hashtags, ~1300 chars
- Appeler `save_document(workspace_slug, title="Draft LinkedIn : <titre>", content=<post>)`
- Si tâche liée résolue → `update_task_status(workspace_slug, task_id, status="in_progress")`
- Output : `✅ Draft sauvegardé : Draft LinkedIn : <titre>` + texte du post affiché

---

### `log <titre>`

Marquer un post comme publié.

- Pre-flight (hal-mcp)
- Résoudre workspace
- Fuzzy match sur `list_tasks(tags=["marketing"])` (seuils standard)
- Collecter `summary` (lien ou note, requis) et `occurred_at` (optionnel)
- Appeler `update_task_status(workspace_slug, task_id, status="done")`
- Appeler `log_interaction(workspace_slug, channel="note", summary="Post LinkedIn publié : <titre>\n<note>", occurred_at?)`
- Si tâche introuvable (score < 50) → logger quand même via `log_interaction` sans `update_task_status`
- Output : `✅ Post publié : <titre>`

---

Pour les instructions complètes et les règles de fuzzy match : charger le skill `linkedin` via le menu (`hal:linkedin`) ou une description naturelle.
