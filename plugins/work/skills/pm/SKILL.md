---
name: pm
description: >
  Work — le pilier projets, tâches et sprints de hal. Deux gestes outillés : `/pm tasks` (le
  tableau du sprint, ou les tâches ouvertes d'un workspace sans sprint) et `/pm plan <projet>`
  (le point sur un projet : description, tâches ouvertes, dernier échange). Le reste — créer une
  tâche, dire « c'est fait », annuler, repousser, ouvrir un projet, loguer une note, changer
  d'étape, démarrer un sprint — se dit en une phrase et appelle un seul outil hal. Déclencher
  sur : "mes tâches", "tableau du sprint", "où en est <projet>", "fais le point sur", "nouvelle
  tâche", "c'est fait", "annule", "repousse", "nouveau projet", "logue une note sur le projet".
  NE PAS déclencher pour : opportunités, contacts, propales (→ gtm:crm), planifier la semaine
  (→ work:sprint-planner), candidatures (→ plugin jobsearch).
allowed-tools: "mcp__plugin_hal_hal-mcp__whoami mcp__plugin_hal_hal-mcp__list_projects mcp__plugin_hal_hal-mcp__create_project mcp__plugin_hal_hal-mcp__update_project mcp__plugin_hal_hal-mcp__update_project_stage mcp__plugin_hal_hal-mcp__list_companies mcp__plugin_hal_hal-mcp__create_company mcp__plugin_hal_hal-mcp__list_contacts mcp__plugin_hal_hal-mcp__create_contact mcp__plugin_hal_hal-mcp__list_tasks mcp__plugin_hal_hal-mcp__create_task mcp__plugin_hal_hal-mcp__update_task mcp__plugin_hal_hal-mcp__update_task_status mcp__plugin_hal_hal-mcp__assign_task_to_sprint mcp__plugin_hal_hal-mcp__list_sprints mcp__plugin_hal_hal-mcp__create_sprint mcp__plugin_hal_hal-mcp__update_sprint mcp__plugin_hal_hal-mcp__transition_sprint mcp__plugin_hal_hal-mcp__log_interaction mcp__plugin_hal_hal-mcp__list_interactions mcp__plugin_hal_hal-mcp__list_documents mcp__plugin_hal_hal-mcp__get_document mcp__plugin_hal_hal-mcp__get_document_link mcp__plugin_hal_hal-mcp__save_document"
---

# Work — projets, tâches, sprints via hal-mcp

hal-mcp porte déjà les règles : chaque valeur hors vocabulaire est refusée **en nommant la valeur
et la liste permise**. Ce skill n'en recopie aucune. Il garde ce que les outils ne savent pas :
dans quel workspace on écrit, quoi confirmer, comment présenter.

## Avant tout appel

1. `whoami`, une fois par session. Échec → « hal-mcp non connecté : `/mcp` → `plugin:hal:hal-mcp`
   → authenticate », et stop.
2. **Workspace.** Chaque appel passe `workspace_slug` : celui que l'utilisateur nomme, sinon
   `default_workspace_slug`. S'il est `null`, lister les workspaces **non archivés** et demander —
   jamais de slug deviné.
3. **Un workspace `archived` est en lecture seule** : toute écriture y est refusée par son nom, et
   il sort des listes par défaut. Ne pas tenter l'écriture : le dire, et proposer le workspace
   vivant qui convient.
4. Lire dans `whoami`, pour le workspace visé, ce qui varie : `type`, `kinds_enabled`,
   `kind_stages`, `allowed_tags`, `sprints_enabled`, `labels`. Parler à l'utilisateur avec les
   `labels` du workspace (ses mots pour tâche, sprint, chaque kind), pas avec les noms de colonnes.

## `/pm tasks [workspace] [--mine] [--all]`

Le tableau des tâches, groupé par statut.

- **Portée.** `sprints_enabled` vrai → `list_sprints(status="actuel")`, puis `list_tasks` filtré
  sur ce `sprint_id`. Aucun sprint actuel → les tâches ouvertes du workspace, avec une ligne
  `⚠️ Aucun sprint actuel dans <slug>`. Workspace sans sprints → ses tâches ouvertes, **sans note**
  « pas de sprint » : c'est son mode normal.
- `--mine` → `assignee_email` = `user_email` de `whoami`. `--all` → aucun filtre, `limit` ≥ `total`.
- `list_tasks` rend `{tasks, total, returned, truncated}` (100 lignes par défaut). Lire `.tasks`.
  Hors `--all`, si `truncated`, **le dire avant tout décompte** : `⚠️ <returned>/<total> tâches lues`.
- Ordre : `todo`, `in_progress`, `blocked`, `done` (préfixe ✓), `cancelled` (préfixe 🚫, **toujours
  dernier, jamais fondu dans `done`**, avec son `cancelled_reason`).
- Ligne : `⚡` si `priority` vaut `high` ou `urgent`, titre, responsable (partie locale de
  `assignee_email`), échéance, tags.

## `/pm plan <projet>`

Retrouver le projet : `list_projects` n'a pas de recherche par nom (il filtre par `kind`, `stage`,
`tags`, `parent_project_id`, `converted_from_id`) ; filtrer la liste côté skill. Plusieurs
candidats → les lister et demander. Puis trois lectures, rien d'écrit : sa `description` (c'est le
dossier, la montrer en entier), `list_tasks(project_id)` (les ouvertes), `list_interactions(project_id,
limit=1)` (le dernier échange). Pour un projet `internal` qui en groupe d'autres, ajouter
`list_projects(parent_project_id=…)`. Pour les trois autres kinds, afficher la contrepartie
(`company`, `contact`, déjà dans la ligne du projet).

## Projets : quatre kinds, une contrepartie

`create_project` exige `kind` ∈ `opportunity`, `client`, `provider`, `internal` — **un kind activé
dans ce workspace** (`kinds_enabled` ; sinon refus par son nom) — et un `stage` pris dans
`kind_stages[kind].active` de `whoami`, jamais écrit de mémoire.

| Kind | De qui il s'agit | Contrepartie |
|---|---|---|
| `opportunity` | quelqu'un à convaincre | `company_id` ou `primary_contact_id` |
| `client` | un client à qui on livre | idem ; `converted_from_id` = l'opportunité d'origine |
| `provider` | un prestataire ou un organisme qui nous sert, démarches administratives comprises | idem |
| `internal` | personne en face | **aucune** — en passer une est refusé |

- Les opportunités se créent et avancent par `gtm:crm`. Ici : `client`, `provider`, `internal`.
- Contrepartie manquante → `list_companies(search=…)` / `list_contacts(search=…)`. Introuvable :
  proposer de la créer (`create_company` / `create_contact`), avec confirmation ; ne jamais en
  inventer une pour satisfaire la règle. Sans contrepartie réelle, le projet est `internal`.
- `parent_project_id` désigne un projet **`internal`** qui en groupe d'autres, sur un seul niveau.
- Changer de `kind` (`update_project`) exige que l'étape actuelle existe dans le nouveau kind :
  déplacer d'abord par `update_project_stage`. Une étape terminale ferme le projet (`closed_at`) ;
  seule l'opportunité a des étapes « gagnées ».
- **La description est le dossier** : longue, datée, mise à jour au fil de l'eau par
  `update_project`, qui remplace le champ — relire, puis réécrire en entier. Les échéances sont des
  tâches liées par `project_id`. Une pièce est un document (`save_document` + `project_id`) cité
  par son slug dans la description.

## Tâches : trois outils, un champ chacun

- **Statut** → `update_task_status` seul : `todo`, `in_progress`, `blocked`, `done`, `cancelled`.
  « Annule X » → `cancelled` + `cancelled_reason` si un motif est donné. Jamais de préfixe de titre,
  jamais `done` pour une annulée : `done` pose `completed_at`, `cancelled` ne le pose jamais.
- **Sprint** → `assign_task_to_sprint` seul. Il écrase le sprint de la tâche : c'est aussi comme
  cela qu'on reporte. N'existe que là où `sprints_enabled`.
- **Le reste** (titre, description, échéance, projet, responsable, priorité, tags) → `update_task`,
  avec le seul champ nommé par l'utilisateur.
- `priority` ∈ `urgent`, `high`, `medium`, `low` ou `null` : « haute » → `high`, « basse » → `low`,
  « normale » → `medium`. Jamais le mot français.
- `tags` = le **domaine fonctionnel**, pris dans `allowed_tags` du workspace, `other` à défaut. Ce
  qu'une autre colonne porte déjà (projet, sprint, responsable) n'y va pas.
- **Retrouver une tâche** : `list_tasks` sans filtre de statut (« c'est fait » vise aussi une
  `todo`), rapprocher sur le titre. Un seul candidat net → agir. Plusieurs → les lister et demander.
  Aucun → proposer de créer, jamais sans confirmation. Si `truncated` et aucun match, le dire : on a
  comparé `<returned>/<total>` tâches, ce n'est pas une preuve d'absence.
- « C'est fait » après une action décrite : proposer l'écriture, ne pas l'enchaîner d'office.

## Sprints

Outils : `list_sprints`, `create_sprint` (`name` et `sprint_number` requis), `update_sprint` (nom,
dates, statut **autre qu'`actuel`**), `transition_sprint` (`incoming_sprint_id`). Passer un sprint
en `actuel` se fait **uniquement** par `transition_sprint` : l'ancien `actuel` devient `dernier`,
dans une seule transaction, et `update_sprint` refuse un second `actuel`. Le numéro d'un nouveau
sprint est `max(sprint_number) + 1` sur **tous** les sprints du workspace, jamais « actuel + 1 »
(la séquence a des trous). Planifier une semaine entière → `work:sprint-planner`.

## Notes et documents

- Note ou compte rendu interne → `log_interaction` (`channel` : `note` par défaut, `meeting` pour un
  CR), avec `project_id` quand il est clair. Ne jamais refuser de loguer faute de projet : le nommer
  dans `summary`. Un échange avec un client ou un prospect relève de `gtm`.
- Document : `save_document` demande `slug`, `domain` (dans `allowed_tags`), `kind`, `title`, et du
  contenu (`content_md`) **ou** un fichier déjà rangé, `storage {provider, uri}`. hal ne reçoit
  jamais le fichier, il en garde le lien. Avant de coiner un `kind`, lire
  `list_documents(summary_only=true)` → `by_kind`. Rattacher un document existant à un projet :
  son slug + `project_id`. Le contenu se relit par `get_document`, le lien du fichier par
  `get_document_link`.

## Garde-fous

- Ambigu → demander. Jamais d'écriture sur un rapprochement incertain.
- `--dry-run` → montrer l'appel (outil + arguments) sans l'exécuter.
- Erreur d'un outil : l'afficher telle quelle (`❌ <entité> → <outil> : <raison>`), corriger avec
  une valeur de la liste qu'elle donne, ne jamais contourner ni réessayer à l'aveugle.
- Écriture réussie : une ligne, `✅ <entité> → <outil> : <valeur>`.
- Le vault Obsidian n'est jamais écrit d'ici.
