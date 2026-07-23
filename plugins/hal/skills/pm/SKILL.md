---
name: pm
description: >
  Gestion de projet interne Blue Green — projets, tâches, sprints, documents,
  notes. Déclencher sur : /pm new, /pm task, /pm tasks, /pm log, /pm update,
  /pm list, /pm doc, /pm sprint, ou toute demande NL : "créer un projet",
  "nouvelle tâche", "mes tâches", "sprint actuel", "vue sprint", "logger une
  note sur le projet", "attacher un doc", "c'est fait", "done", "next".
  NE PAS déclencher pour : opportunités commerciales, contacts, propales, devis
  (→ /crm).
allowed-tools: "Bash(uv *) Bash(python3 *) Bash(python *) Bash(git *) Bash(mkdir *) Bash(cat *) Read Write Edit Glob"
---

# PM — Gestion de projet interne via hal-mcp (Claude Code)

Ce skill route les instructions NL vers le connecteur MCP `hal-mcp` (backend
Supabase). Zéro script, zéro Bash — pur NL → mapping MCP.

**Scope** : projets internes Blue Green, tâches, sprints, documents, notes
d'avancement. Les données CRM commerciales (opportunités, contacts, propales,
devis) sont hors scope → skill `/crm`.

---

## Pre-flight : vérifier hal-mcp

Avant toute opération MCP, vérifier que le connecteur est actif via `whoami` :

1. Appeler `whoami` (aucun argument).
2. **Succès** → connecteur opérationnel. Mettre en cache pour la commande en cours :
   - `default_workspace_slug` — utilisé par la résolution de workspace
   - `workspaces` — liste des memberships, sert pour les messages d'erreur
   - `user_email` — utilisé par `/pm tasks --mine`
3. **Échec** (outil indisponible / connexion refusée / timeout) :

> ❌ **hal-mcp non connecté.**
> Le serveur est fourni par le plugin `hal` (`plugin:hal:hal-mcp`).
> Reconnexion : `/mcp` → `plugin:hal:hal-mcp` → `authenticate`.
> Relancer la commande après reconnexion.

---

## Workspace resolution (s'applique à toutes les commandes /pm)

Chaque appel MCP doit passer un `workspace_slug`. Le pre-flight a déjà mis en
cache la réponse `whoami`. Résoudre dans cet ordre :

1. **Arg explicite** (`/pm tasks ic`, `/pm list blue-green`) → utiliser ce slug
   directement. Raccourci : `ic` → `ic-ingenieurs-conseils`. RLS valide la
   membership côté serveur ; si non-membre, l'outil MCP renvoie une erreur
   naturelle — l'afficher telle quelle.
2. **Pas d'arg** → utiliser `default_workspace_slug` depuis le cache `whoami`.
   - Non-null → l'utiliser comme `workspace_slug`.
   - `null` avec `workspaces` non vide (plusieurs memberships, aucun par défaut)
     → lister les slugs dispo et demander lequel utiliser. NE PAS fallback sur
     un slug hardcodé.
   - `null` avec `workspaces` vide → répondre et stopper :

     > ❌ Aucun workspace assigné à ton compte.
     > Demande à ton administrateur BlueGreen d'ajouter ton email aux workspaces concernés dans Supabase.

---

## /pm list `[workspace]`

Affiche les projets du workspace en kanban texte groupé par stage.

### Étapes

**1. Résoudre workspace** — règle standard ci-dessus.

**2. Appeler `list_projects`**

- `workspace_slug` (résolu ci-dessus)
- Pas de filtre de stage — vue complète
- Filtres optionnels : `stage=<value>`, `kind=<value>` si l'utilisateur les passe

**3. Grouper et afficher**

Grouper par `stage`. Ordre :
- **Stages actifs** = stages avec au moins un projet `closed_at` null (d'abord)
- **Stages terminaux** = stages où tous les projets ont `closed_at` non-null (en dernier)
- Dans chaque stage : ordre serveur (`created_at DESC`)

Format d'affichage :

```
### en_cours (2)
- PROJ-12 · Commercialisation Atelier IA · — · —
- PROJ-08 · Formation Blue Green · — · —

### ✓ termine (3)
- PROJ-05 · Setup Supabase hal — terminé 2026-05-20
```

Ligne par projet :
`{project_ref ou "—"} · {company.name ou "—"} · {amount_ht formaté ou "—"} · {location ou "—"} {#tag1 #tag2 si tags non vide}`

- Format `amount_ht` : milliers séparés par espace + ` €`. Afficher `—` si null.
- Tags : si non vide, ajouter `#tag1 #tag2` en suffixe.
- Stages terminaux : préfixer `✓ `, ajouter `— terminé {closed_at[:10]}`.
- Ne jamais afficher le champ `description`.

**4. Cas limites**

- Aucun projet → `Aucun projet dans le workspace <slug>.`
- Stage vide → ne pas afficher la section
- Filtre `kind` passé → ajouter `(kind: <value>)` après le nom du workspace dans l'en-tête

---

## /pm tasks `[workspace]` `[--mine]` `[--project <ref>]` `[--status <status>]` `[--all]` `[--tag <tag>]`

Tâches en kanban texte groupé par statut. **Scope par défaut : le sprint actuel.**

### Étapes

**1. Résoudre workspace** — règle standard ci-dessus.

**2. Résoudre le scope (sprint actuel par défaut)**

Deux modes selon les flags présents :

- **Mode requête explicite** — déclenché par `--status`, `--project`, `--all` ou
  `--tag`. Pas de scoping sprint ; interroger le workspace directement. Les flags
  se combinent en AND, sauf `--all` ignoré si un autre filtre est présent :
  - `--status <value>` → filtre `status` (`todo` | `in_progress` | `done` | `blocked`)
  - `--project <ref>` → `list_projects` pour résoudre `project_id` par nom/ref,
    puis filtre `project_id`
  - `--all` → aucun filtre ; toutes les tâches du workspace
  - `--tag <value>` → passer `tags=["<value>"]` à `list_tasks`
- **Mode sprint actuel** — défaut, aucun de ces flags :
  1. `list_sprints(workspace_slug, status="actuel")`
  2. Sprint trouvé → filtrer `list_tasks` par son `sprint_id` ; retenir son `name` pour le header
  3. Aucun sprint actuel → jamais de board vide silencieux. Afficher le message,
     puis fallback sur les tâches ouvertes :

     > ⚠️ Aucun sprint actuel dans `<slug>`. Affichage des tâches ouvertes du workspace.

     Appeler `list_tasks` sans filtre `sprint_id`, omettre le groupe `done`.

`--mine` est un filtre, pas un flag de scope : s'applique dans les deux modes,
ajoute `assignee_email: <user_email du cache whoami>` (jamais demander).

**3. Appeler `list_tasks`**

Avec `workspace_slug` (+ filtres résolus).

**4. Grouper et afficher**

Ligne de scope en tête :
- Mode sprint actuel → `**<nom sprint>** · workspace <slug>`
- `--all` → `**Toutes les tâches** · workspace <slug>`
- Filtre `--status`/`--project` → nommer, ex. `**Statut : blocked** · workspace <slug>`
- Filtre `--tag` → `**Tag : <value>** · workspace <slug>`
- Fallback (aucun sprint) → le ⚠️ ci-dessus tient lieu de scope line

Grouper par `status`. Ordre fixe : `todo` → `in_progress` → `blocked` → `done`.
`done` est terminal — préfixer `✓ ` (omis dans le fallback sans sprint).

Format d'affichage :

```
**Sprint 3 — Hal v0.8** · workspace blue-green

### todo (3)
- Écrire tests hal-mcp · renaud · 2026-06-20
- Préparer démo client · — · —

### in_progress (1)
- ⚡ Skill /pm · renaud · 2026-06-17 [S]

### ✓ done (2)
- Bump versions 0.8.0 · renaud · 2026-06-17
```

Ligne par tâche :
`{⚡ si priority=high}{title} · {assignee short ou "—"} · {due_date ou "—"} {[S] si sprint_id non null} {#tag1 #tag2 si tags non vide}`

- `assignee short` : partie locale de `assignee_email` (avant `@`). `—` si null.
- `[S]` : marker si `sprint_id` non null.
- Tags : si non vide, ajouter `#tag1 #tag2` en suffixe.

**5. Cas limites**

- Aucune tâche → `Aucune tâche dans le workspace <slug>.`
- Sprint actuel vide → `Aucune tâche dans le sprint « <nom> ».`
- Groupe vide → ne pas afficher la section
- `list_tasks` retourne `project_id` brut (UUID) — colonne omise sauf si `--project` utilisé

---

## /pm new `<nom du projet>`

Créer un nouveau projet interne.

### Étapes

1. **Résoudre workspace** — règle standard.
2. Collecter depuis la conversation ou demander si absent :
   - `name` (requis) — le nom passé après `/pm new`
   - `description` (optionnel) — contexte ou objectif
   - `kind` (optionnel) — type de projet si connu
3. Appeler `create_project` avec `workspace_slug`, `name`, et les champs optionnels
   disponibles.
4. Output : `✅ Projet créé : <ref> · <name>`

---

## /pm task `<titre>`

Créer une tâche dans le contexte courant.

### Étapes

1. **Résoudre workspace** — règle standard.
2. Collecter depuis la conversation ou demander si absent :
   - `title` (requis) — le titre passé après `/pm task`
   - `project_id` (optionnel) — si un projet est clairement mentionné dans le
     contexte, résoudre via `list_projects` (fuzzy match sur le nom/ref)
   - `due_date` (optionnel) — si une date est mentionnée
   - `assignee_email` (optionnel) — si une assignation est mentionnée
   - `priority` (optionnel) — `high` | `normal`
   - `sprint_id` (optionnel) — si "dans le sprint actuel" → résoudre via
     `list_sprints(status="actuel")`
3. Appeler `create_task` avec `workspace_slug` et les champs collectés.
4. Output : `✅ Tâche créée : <title>`

---

## /pm log `<note>`

Logger une note / CR interne sur un projet.

### Étapes

1. **Résoudre workspace** — règle standard.
2. Identifier le projet associé depuis le contexte conversation (fuzzy match).
   Si ambigu, demander.
3. Collecter :
   - `summary` (requis) — la note passée après `/pm log`
   - `channel` — `meeting` par défaut pour un CR, `email` si c'est un suivi email
   - `project_id` — résolu à l'étape 2
   - `occurred_at` (optionnel) — si une date est mentionnée ; défaut = maintenant
4. Appeler `log_interaction` avec `workspace_slug`, `channel`, `summary`, `project_id`.
5. Output : `✅ Note loguée sur <projet>`

**Règle** : ne jamais bloquer un log. Si le projet est introuvable (score < 50),
logger quand même en mettant le nom du projet dans `summary`.

---

## /pm doc `<url ou markdown>`

Attacher un document à un projet.

### Étapes

1. **Résoudre workspace** — règle standard.
2. Identifier le projet depuis le contexte (fuzzy match). Si ambigu, demander.
3. Collecter :
   - `title` — titre du document (inférer depuis l'URL ou demander)
   - `content` — URL ou contenu markdown
   - `project_id` — résolu ci-dessus
4. Appeler `save_document` avec `workspace_slug`, `title`, `content`, `project_id`.
5. Output : `✅ Document attaché : <title> → <projet>`

---

## /pm sprint `[sous-commande]`

Voir, créer ou mettre à jour les sprints du workspace.

### Afficher le sprint actuel (défaut)

Appeler `list_sprints(workspace_slug, status="actuel")`. Afficher le nom, les
dates de début/fin, le statut. Si aucun sprint actuel → message explicite +
lister les sprints disponibles.

### Créer un sprint

Si l'utilisateur dit "nouveau sprint S<N>", "créer sprint" :
- Collecter : `name` (requis), `starts_at`, `ends_at` (optionnels)
- Appeler `create_sprint`
- Output : `✅ Sprint créé : <name>`

### Mettre à jour un sprint

Si l'utilisateur dit "renomme le sprint", "change le statut du sprint en X",
"le sprint est actuel", "corrige le statut du sprint" :
- Résoudre le sprint cible via `list_sprints` (status filter ou matching sur le nom)
- Appeler `update_sprint(workspace_slug, sprint_id, ...)` — champs : `name`,
  `status`, `starts_at`, `ends_at`
- Valeurs `status` valides : `passes` / `dernier` / `actuel` / `suivant` / `a_venir`
- Output : `✅ Sprint mis à jour : <name> → <champ>: <valeur>`

---

## /pm update `<texte libre>`

1. Parser le texte pour détecter l'**intention** et l'**entité** (tâche, sprint,
   projet).
2. Résoudre les entités via les outils `list_*` appropriés (filtres pour garder
   les payloads légers).
3. Si la correspondance est ambiguë → lister les candidats et demander avant d'écrire.
4. Appeler l'outil MCP cible avec `workspace_slug` résolu.
5. Output : `✅ [Entité] → [tool]: [valeur]`.

Si l'utilisateur ajoute `--dry-run`, afficher le plan d'appels MCP (nom + args)
sans exécuter.

---

## Intent → tool mapping (PM)

| L'utilisateur dit | Outil(s) MCP |
|-------------------|-------------|
| "mes tâches", "todo list", "qu'est-ce que j'ai à faire" | `list_tasks` (workspace default) |
| "ajouter tâche X", "nouvelle tâche Y", "todo : Z", "créer une tâche" | `create_task` |
| "repousse X à lundi", "change l'échéance de X", "renomme X en Y", "réassigne X à [email]", "X priorité haute" | `list_tasks` → fuzzy match → `update_task` (attributs : `title`, `description`, `due_date`, `project_id`, `assignee_email`, `priority`, `external_ref` — **pas** `status`/`sprint`) |
| "tâche X faite", "X → done", "X terminé", "c'est fait" | `list_tasks` → fuzzy match → `update_task_status` (done) |
| "X → in progress", "je commence X", "en cours : X" | `list_tasks` → fuzzy match → `update_task_status` (in_progress) |
| "X bloqué", "X → blocked" | `list_tasks` → fuzzy match → `update_task_status` (blocked) |
| "X → todo", "remettre X en attente" | `list_tasks` → fuzzy match → `update_task_status` (todo) |
| "nouveau sprint S<N>", "créer sprint" | `create_sprint` |
| "renomme le sprint", "change le statut du sprint en X", "le sprint est actuel" | `list_sprints` → match → `update_sprint` |
| "assigne tâche X au sprint Y", "tâche X dans sprint Y" | `list_tasks` → match → `assign_task_to_sprint` |
| "nouveau projet interne [nom]", "créer un projet" | `create_project` |
| "logger une note sur [projet]", "CR interne", "note de projet" | `log_interaction` (channel: meeting) |

---

## Task resolution (fuzzy match)

Seuils : score **> 80** → match direct ; **50–80** → lister les candidats, demander ;
**< 50** → entité introuvable, proposer création.

- Matcher sur `title`. Appeler `list_tasks` **sans filtre `status`** — "X → done"
  doit matcher des tâches `todo` ou `in_progress`.
- Ambiguïté : plusieurs tâches au même score → lister, demander.
- **Trois writers à responsabilité unique** :
  - **status** → `update_task_status` (`workspace_slug`, `task_id`, `status` ∈
    `todo`/`in_progress`/`done`/`blocked`)
  - **sprint** → `assign_task_to_sprint` (`workspace_slug`, `task_id`, `sprint_id`)
  - **tout le reste** → `update_task` (attributs uniquement : `title`,
    `description`, `due_date`, `project_id`, `assignee_email`, `priority`,
    `external_ref` — **pas** `status` ni `sprint`)
  - Toujours passer `workspace_slug`. N'envoyer que les attributs nommés par l'utilisateur.
- Ne jamais auto-créer sur un match ambigu. Score < 50 → proposer création.
- "c'est fait" / "done" / "next" après une action décrite → proposer l'écriture MCP,
  ne pas auto-écrire.
- **Résolution sprint** : pour "le sprint actuel", appeler
  `list_sprints(workspace_slug, status="actuel")` — ne jamais demander un UUID.

---

## Guardrails

- **Confirmer avant toute écriture ambiguë.** Dans le doute, demander.
- **Dry-run** : si l'utilisateur ajoute `--dry-run`, afficher le plan MCP
  (nom tool + args) sans exécuter.
- **Ne jamais auto-créer.** Score < 50 → proposer création, attendre confirmation.
- **Format de sortie** : `✅ [Entité] → [tool]: [valeur]` par écriture réussie.
- **Erreur MCP** : `❌ [Entité] → [tool]: [raison d'erreur]`. Afficher
  immédiatement — ne pas réessayer automatiquement.

---

## Out of scope

- **CRM commercial** (→ `/crm`) : opportunités, propales, contacts, entreprises,
  interactions avec prospects, devis, stages commerciaux (`update_project_stage`).
- **Edifice missions** (→ `/edifice`) : rapports terrain, inspection bâtiments,
  outils `read_edifice_mission`, `get_mission_with_assets`, `push_mission_context`.
- **Job Search** (→ `obsidian-crm`) : candidatures, entretiens, CV. Jamais écrire
  le vault depuis ce skill.
- **`project_id` join** : `list_tasks` retourne un UUID brut pour `project_id`.
  Résolution automatique uniquement avec `--project <ref>` — sinon colonne omise.
