---
name: linkedin
description: >
  Le post LinkedIn hebdomadaire de Renaud, court, orienté recherche d'emploi, dans sa voix : idea
  (garder une idée dans le backlog), draft (rédiger le post en lisant tone_of_voice), log (le post est
  publié). Déclencher sur : "idée de post LinkedIn", "rédige le post sur X", "draft LinkedIn",
  "j'ai publié le post sur Y". NE PAS déclencher pour : voir le backlog (→ list_tasks nommé dans la
  phrase), opportunités commerciales (→ gtm:crm), tâches hors LinkedIn (→ work).
allowed-tools: "mcp__plugin_hal_hal-mcp__whoami mcp__plugin_hal_hal-mcp__create_task mcp__plugin_hal_hal-mcp__list_tasks mcp__plugin_hal_hal-mcp__update_task_status mcp__plugin_hal_hal-mcp__list_documents mcp__plugin_hal_hal-mcp__get_document mcp__plugin_hal_hal-mcp__save_document mcp__plugin_hal_hal-mcp__log_interaction mcp__plugin_hal_hal-mcp__list_interactions"
---

# LinkedIn — un post par semaine, court, pour la recherche d'emploi

Cadence : **un post par semaine**. Format : **court** (accroche d'une ligne, trois ou quatre
paragraphes brefs, 800 caractères au plus). Angle : ce que le post montre de Renaud à un recruteur ou
à un futur client, jamais une actualité générique. Voix : celle du document `tone_of_voice` de hal,
lu à chaque `draft`.

Premier mot de l'argument : `idea <titre>`, `draft <titre ou idée>`, `log <titre>`. Voir le backlog =
`list_tasks` nommé dans la phrase (filtre `tags` du backlog). Rien n'est publié par ce skill :
LinkedIn reste à la main. Les statistiques d'un post ne sont pas gérées ici.

## Pre-flight

`whoami`, une fois. Échec → « ❌ hal-mcp non connecté. Reconnexion : `/mcp` → `plugin:hal:hal-mcp` →
`authenticate`. » Workspace : celui qui porte `tone_of_voice` (voir `draft`) ; en l'absence d'argument,
`default_workspace_slug`, sinon demander. Un workspace `archived` n'accepte aucune écriture : s'arrêter
en le nommant. Le backlog est l'ensemble des tâches taguées `marketing` : ce tag doit figurer dans
`allowed_tags` du workspace ; sinon s'arrêter et le dire (ne jamais en inventer un, ni mettre le nom
de LinkedIn dans `tags`).

## `idea <titre>`

`create_task(title, tags=["marketing"], description=<angle : ce que le post montre de Renaud>,
due_date si une date est dite)`. Avant de créer, `list_tasks(tags=["marketing"])` : une idée au titre
voisin existe → la montrer et demander. Sortie : `✅ Idée : <titre>`.

## `draft <titre ou idée>`

1. **Cadence.** `list_interactions(channel="linkedin", limit=1)` : un post logué depuis moins de sept jours
   → le dire et demander s'il s'agit bien du post de la semaine suivante.
2. **L'idée.** `list_tasks(tags=["marketing"], status="todo")` : retrouver l'idée par son titre (plusieurs
   candidats → demander). Aucune idée correspondante → rédiger quand même, sans tâche liée.
3. **La voix, par un vrai appel.** `list_documents(domain="marketing", kind="tone_of_voice")` puis
   `get_document(slug)` : lire `content_md`. Faire de même pour `kind="brand_guidelines"` ; absent, le
   dire et continuer. **`tone_of_voice` introuvable → s'arrêter** : « aucun document tone_of_voice dans
   <workspace> » ; ne jamais rédiger de mémoire ni avec une voix générique.
4. **Rédiger** dans cette voix, au format ci-dessus. Montrer le texte et son nombre de caractères ; une
   relecture demandée = une nouvelle version, pas un nouveau document.
5. **Enregistrer le brouillon** : lire d'abord `list_documents(summary_only=true)` et réutiliser le `kind`
   de brouillon LinkedIn déjà employé dans `marketing` (`by_kind`) ; aucun → `linkedin_draft`.
   `save_document(slug=<linkedin-AAAA-MM-JJ-titre>, domain="marketing", kind, title="Post LinkedIn — <titre>",
   content_md=<le post>, knowledge=false)`. Même `slug` = même brouillon mis à jour.
6. Tâche liée → `update_task_status(task_id, status="in_progress")`.

## `log <titre>`

1. Retrouver la tâche (`list_tasks(tags=["marketing"])`, statut `in_progress` d'abord) ; plusieurs
   candidats ou aucun → demander, jamais choisir par rang.
2. Demander le lien du post (ou une note) et la date de publication si ce n'est pas aujourd'hui.
3. `update_task_status(task_id, status="done")`, puis `log_interaction(channel="linkedin",
   summary="Post LinkedIn publié : <titre>\n<lien>", occurred_at)` — sans `project_id` : un post ne
   concerne aucun projet.
4. Tâche introuvable après question : logger quand même l'interaction, sans toucher à une tâche.

## Garde-fous

- Ne jamais auto-créer une tâche depuis `draft` ou `log` : proposer `idea`.
- Un brouillon est un **document**, une idée est une **tâche** ; `knowledge` reste faux (un brouillon
  n'est pas une connaissance).
- Erreur hal : `❌ <entité> → <outil> : <raison>`, tel quel, sans réessai ni contournement.
