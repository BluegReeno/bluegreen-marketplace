---
name: linkedin
description: >
  Gestion de contenu LinkedIn Blue Green — idées de posts, backlog éditorial,
  tendances, rédaction de drafts, suivi de publications.
  Déclencher sur : /linkedin idea, /linkedin backlog, /linkedin trend,
  /linkedin draft, /linkedin log, ou toute demande NL : "idée de post LinkedIn",
  "mon backlog LinkedIn", "tendances LinkedIn sur X", "rédiger un post sur Y",
  "j'ai publié le post sur Z".
  NE PAS déclencher pour : projets internes (→ /pm), opportunités commerciales
  (→ /crm), missions terrain (→ /edifice).
version: 0.1.0
allowed-tools: "Bash(uv *) Bash(python3 *) Bash(python *) Bash(git *) Bash(mkdir *) Bash(cat *) Read Write Edit Glob"
---

# LinkedIn — Gestion de contenu via hal-mcp + Bright Data (Claude Code)

Ce skill route les instructions NL vers le connecteur MCP `hal-mcp` (backend
Supabase) et les outils Bright Data. Zéro script, zéro Bash — pur NL → mapping MCP.

**Scope** : idées de posts LinkedIn, backlog éditorial, recherche de tendances,
rédaction et sauvegarde de drafts, log de publications. Les projets internes
(tâches, sprints) sont hors scope → skill `/pm`.

Les idées de posts sont des **tâches** hal taguées `linkedin`. Toutes les commandes
LinkedIn filtrent par `tags: ["linkedin"]` pour lire le backlog, et passent
`tags: ["linkedin"]` à la création.

---

## Pre-flight : vérifier hal-mcp

Requis pour `idea`, `backlog`, `draft`, `log`. Pas nécessaire pour `trend`
(Bright Data uniquement).

1. Appeler `whoami` (aucun argument).
2. **Succès** → connecteur opérationnel. Mettre en cache pour la commande en cours :
   - `default_workspace_slug` — utilisé par la résolution de workspace
   - `workspaces` — liste des memberships, sert pour les messages d'erreur
   - `user_email` — utilisé si besoin de filtres assignee
3. **Échec** (outil indisponible / connexion refusée / timeout) :

> ❌ **hal-mcp non connecté.**
> Reconnexion : **Claude Desktop → Paramètres → Connexions → hal-mcp → Activer**
> ⚠️ Ne pas lancer de commandes terminal — interface graphique uniquement.
> Relancer la commande après reconnexion.

---

## Workspace resolution (s'applique à toutes les commandes /linkedin)

Chaque appel hal-mcp doit passer un `workspace_slug`. Le pre-flight a déjà mis en
cache la réponse `whoami`. Résoudre dans cet ordre :

1. **Arg explicite** → utiliser ce slug directement.
2. **Pas d'arg** → utiliser `default_workspace_slug` depuis le cache `whoami`.
   - Non-null → l'utiliser comme `workspace_slug`.
   - `null` avec `workspaces` non vide → lister les slugs dispo et demander.
   - `null` avec `workspaces` vide → répondre et stopper :

     > ❌ Aucun workspace assigné à ton compte.
     > Demande à ton administrateur BlueGreen d'ajouter ton email aux workspaces concernés dans Supabase.

---

## /linkedin idea `<titre>`

Capturer une idée de post LinkedIn comme tâche hal.

### Étapes

1. **Pre-flight** — voir ci-dessus.
2. **Résoudre workspace** — règle standard.
3. Collecter depuis la conversation ou l'argument :
   - `title` (requis) — le titre de l'idée passé après `/linkedin idea`
   - `description` (optionnel) — angle, message clé, public cible si mentionné
   - `due_date` (optionnel) — si une date de publication est mentionnée
4. Appeler `create_task` avec :
   - `workspace_slug`
   - `title`
   - `tags: ["linkedin"]`
   - `description` (si fourni)
   - `due_date` (si fourni)
5. Output : `✅ Idée créée : <titre>`

---

## /linkedin backlog `[workspace]`

Afficher le backlog éditorial LinkedIn groupé par statut.

### Étapes

1. **Pre-flight** — voir ci-dessus.
2. **Résoudre workspace** — règle standard.
3. Appeler `list_tasks` avec :
   - `workspace_slug`
   - `tags: ["linkedin"]`
4. Grouper par `status`. Ordre fixe : `todo` → `in_progress` → `done`.
   - `done` est terminal — préfixer `✓ `.
5. Format d'affichage :

```
### todo (2)
- Idée IA dans l'ingénierie · — · —
- ⚡ Post retour conférence · renaud · 2026-07-01

### in_progress (1)
- Diagnostic numérique PME · renaud · —

### ✓ done (1)
- Lancement service Edifice · renaud · 2026-06-15
```

Ligne par tâche :
`{⚡ si priority=high}{title} · {assignee short ou "—"} · {due_date ou "—"}`

- `assignee short` : partie locale de `assignee_email` (avant `@`). `—` si null.
- Groupes vides → ne pas afficher la section.
- Aucune tâche → `Aucune idée LinkedIn dans le workspace <slug>.`

---

## /linkedin trend `[sujet]`

Rechercher les tendances LinkedIn sur un sujet pour informer la rédaction.

### Étapes

*Aucun pre-flight hal-mcp requis — Bright Data uniquement.*

1. **Construire la requête de recherche** :
   - Si `sujet` fourni → `"LinkedIn trending posts [sujet] 2026"`
   - Si pas de sujet → `"LinkedIn trending posts BlueGreen intelligence artificielle ingénierie 2026"`
2. Appeler `search_engine` avec la requête construite.
3. Appeler `web_data_linkedin_posts` (sujet en query parameter) pour des exemples de posts engageants.
4. Analyser les résultats et afficher :
   - 3–5 thèmes tendance identifiés (avec exemples de titres)
   - 2–3 posts LinkedIn avec format, angle, accroche remarquables
   - Insights : formats qui fonctionnent (liste, story, question, data), ton dominant
5. Output :

```
## Tendances LinkedIn — [sujet]

### Thèmes en traction
1. [thème 1] — [exemple de titre]
2. [thème 2] — ...

### Posts remarquables
- **"[accroche]"** — [format] · [engagement estimé]
  [angle / message clé]

### Insights formats
- [observation 1]
- [observation 2]
```

**Fallback** : si `web_data_linkedin_posts` échoue → continuer avec les résultats
`search_engine` seuls et le signaler.

---

## /linkedin draft `<titre ou idée>`

Rédiger un post LinkedIn et le sauvegarder comme document hal.

### Étapes

1. **Pre-flight** — voir ci-dessus.
2. **Résoudre workspace** — règle standard.
3. **Résoudre l'idée** — fuzzy match sur `title` via `list_tasks(tags=["linkedin"])`.
   Seuils : > 80 → match direct ; 50–80 → lister candidats, demander ;
   < 50 → rédiger quand même à partir du titre fourni (sans tâche liée).
4. **Rédiger le draft** (pur Claude, aucun MCP) :
   - Tenir compte du contexte conversation (angle, public cible, ton)
   - Format LinkedIn recommandé : accroche forte (1 ligne), corps (3–5 paragraphes courts),
     CTA clair, 3–5 hashtags pertinents
   - Limiter à ~1300 caractères (optimal pour l'algorithme LinkedIn)
5. Appeler `save_document` avec :
   - `workspace_slug`
   - `title` : `"Draft LinkedIn : <titre>"`
   - `content` : le texte du post rédigé (markdown)
   - `project_id` (optionnel — si l'idée est liée à un projet hal mentionné)
6. Si une tâche liée a été résolue (étape 3) → appeler `update_task_status` avec
   `task_id` et `status: "in_progress"`.
7. Output :

```
✅ Draft sauvegardé : Draft LinkedIn : <titre>
[texte du post affiché pour relecture]
```

---

## /linkedin log `<titre ou note>`

Marquer un post comme publié et enregistrer une trace dans hal.

### Étapes

1. **Pre-flight** — voir ci-dessus.
2. **Résoudre workspace** — règle standard.
3. **Résoudre la tâche** — fuzzy match sur `title` via `list_tasks(tags=["linkedin"])`.
   Seuils standard. Si score < 50 → demander confirmation avant de continuer.
4. Collecter depuis la conversation ou demander si absent :
   - `summary` (requis) — lien du post publié, ou note sur la publication
   - `occurred_at` (optionnel) — date de publication ; défaut = maintenant
5. Appeler `update_task_status` avec `workspace_slug`, `task_id`, `status: "done"`.
6. Appeler `log_interaction` avec :
   - `workspace_slug`
   - `channel: "note"`
   - `summary` : `"Post LinkedIn publié : <titre>\n<note ou lien>"`
   - `occurred_at`
   *(Note: `project_id` est nullable dans `halcrm_interactions` — l'omettre est intentionnel pour les posts LinkedIn qui ne sont pas liés à un projet CRM.)*
7. Output : `✅ Post publié : <titre>`

**Règle** : ne jamais bloquer le log. Si la tâche est introuvable (score < 50 et pas
de confirmation), logger quand même via `log_interaction` en incluant le titre dans
`summary`, sans appeler `update_task_status`.

---

## Intent → tool mapping (LinkedIn)

| L'utilisateur dit | Outil(s) MCP |
|-------------------|-------------|
| "idée de post sur X", "noter une idée LinkedIn" | `create_task` (tags: linkedin) |
| "mon backlog LinkedIn", "mes idées de posts", "qu'est-ce que j'ai à écrire" | `list_tasks` (tags: linkedin) |
| "tendances LinkedIn sur X", "qu'est-ce qui marche sur LinkedIn en ce moment" | `search_engine` + `web_data_linkedin_posts` |
| "rédiger un post sur X", "draft LinkedIn X", "écrire le post Y" | `list_tasks` → fuzzy → AI rédige → `save_document` (+ `update_task_status` in_progress) |
| "j'ai publié le post sur X", "post Y publié", "logger la publication" | `list_tasks` → fuzzy → `update_task_status` (done) + `log_interaction` |

---

## Guardrails

- **Confirmer avant toute écriture ambiguë.** Dans le doute, demander.
- **Ne jamais auto-créer une tâche.** Proposer `/linkedin idea` si l'idée n'existe pas.
- **`trend` ne touche pas hal-mcp.** Aucun appel `whoami` ni workspace résolution.
- **Draft = document hal, pas une tâche.** Utiliser `save_document`, pas `create_task`.
- **Format de sortie** : voir la section `Output :` de chaque commande.
- **Erreur MCP** : `❌ [Entité] → [tool]: [raison d'erreur]`. Afficher immédiatement.

---

## Out of scope

- **Projets internes BG** (→ `/pm`) : tâches non-LinkedIn, sprints, notes d'avancement.
- **CRM commercial** (→ `/crm`) : opportunités, contacts, propales, devis.
- **Edifice missions** (→ `/edifice`) : rapports terrain, inspection bâtiments.
- **Publication automatique** : ce skill gère le contenu, pas la publication sur LinkedIn.
- **Table Supabase dédiée** : V2 uniquement — tracking avancé (impressions, engagement).
