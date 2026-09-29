---
description: CRM — pipeline commercial Blue Green (opportunités, contacts, CRs, propales)
argument-hint: "list [workspace] | new <nom> | qualify <nom> | log update <interaction> | update <texte libre> | contact new <nom> | contact update <nom> | doc <url>"
allowed-tools: "Bash(uv *) Bash(python3 *) Bash(python *) Bash(git *) Bash(mkdir *) Bash(cat *) Read Write Edit Glob"
---

CRM — Argument reçu : `$ARGUMENTS`

---

## 0. Pre-flight : vérifier hal-mcp

Appeler `whoami` (aucun argument) avant toute action. Mettre en cache la réponse :
- `default_workspace_slug` (résolution de workspace)
- `workspaces` (memberships, pour les messages d'erreur)
- `user_email` (filtres assignee si besoin)

Si l'outil échoue ou est indisponible :
> ❌ **hal-mcp non connecté.**
> Reconnexion : **Claude Desktop → Paramètres → Connexions → hal-mcp → Activer**
> ⚠️ Ne pas lancer de commandes terminal — interface graphique uniquement.
> Relancer la commande après reconnexion.

Stopper si indisponible. Continuer si le call réussit.

**Les opportunités = projets hal avec `kind: "opportunity"`.** Toujours passer ce
filtre à `list_projects` et ce champ à `create_project`.

---

## Workspace resolution (commun à toutes les sous-commandes)

1. Arg explicite → utiliser ce slug directement.
2. Pas d'arg → utiliser `default_workspace_slug` depuis le cache `whoami`.
   - Non-null → l'utiliser.
   - Null avec `workspaces` non vide → lister les slugs et demander.
   - Null avec `workspaces` vide → `❌ Aucun workspace assigné à ton compte.`

---

### Tags (s'applique à toute écriture `tags` — `log update`)

**Tags.** `tags` means functional domain. Pick only from the calling workspace's `allowed_tags`, returned by `whoami`; if nothing fits, use `other`. Never invent a value, and never put in `tags` what another column already carries (`company_id`, `role`, `channel`, `project_id`). hal-mcp states the full doctrine in its server `instructions` and enforces it on every write.

---

### `list [workspace]`

Pipeline en kanban texte groupé par stage.

- Résoudre workspace (voir ci-dessus)
- Appeler `list_projects(workspace_slug, kind="opportunity")` — vue complète
- Grouper par `stage` : actifs d'abord (opportunités avec `closed_at` null), terminaux en dernier
- Ligne : `{project_ref ou "—"} · {company.name ou "—"} · {amount_ht formaté ou "—"} · {name}`
- Format `amount_ht` : milliers séparés par espace + ` €`. `—` si null.
- Stages terminaux : préfixer `✓ `, ajouter `— terminé {closed_at[:10]}`
- **Ne jamais afficher le champ `description`** (contient le BANT — données internes)
- Aucune opportunité → `Aucune opportunité dans le workspace <slug>.`

---

### `new <nom>`

Créer une opportunité commerciale.

- Résoudre workspace
- `name` depuis l'argument (requis)
- Champs optionnels si présents dans le contexte : `company_id` (`list_companies(search=<mot distinctif du nom>)`),
  `amount_ht`, `description`
- Appeler `create_project` avec `workspace_slug`, `name`, `kind: "opportunity"`, `stage: "Prospect"`
- Output : `✅ Opportunité créée : <ref> · <name> · Prospect`

---

### `qualify <nom>`

Qualifier avec la méthode BANT (Budget · Authority · Need · Timeline).

- Résoudre workspace
- Résoudre l'opportunité via `list_projects(kind="opportunity")` (fuzzy match)
- Analyser le contexte conversation pour extraire les 4 champs BANT
- Construire le bloc YAML :
  ```yaml
  bant:
    budget: "..."
    authority: "..."
    need: "..."
    timeline: "..."
  ```
  Valeur `"?"` si champ non identifiable.
- Fusionner avec la `description` existante (ne pas écraser les valeurs non-`"?"` déjà présentes)
- Appeler `update_project(workspace_slug, project_id, description=<description fusionnée>)`
- Output : `✅ BANT mis à jour : <nom>` + récapitulatif des 4 champs

---

### `log update <interaction>`

Corriger une interaction déjà loguée (`summary`, `transcript`, `channel`, `occurred_at`,
`contact_id`, `project_id`, `tags`) — pas de suppression, aucun outil MCP ne l'expose.

- Résoudre workspace
- **`interaction_id`** : depuis le contexte conversation (rapport d'un `/call` précédent dans
  la session, ou id collé par l'utilisateur), sinon `list_interactions(workspace_slug,
  search=<mot du summary>, since, until)` — plusieurs → lister et demander, jamais deviner.
- Logger un **nouvel** appel n'est pas ici : `/call` (skill `gtm:call`).
- Collecter uniquement les champs à corriger, mentionnés par l'utilisateur ; les champs
  omis restent inchangés côté serveur
- `tags` **remplace** le tableau existant (ne fusionne pas) — pour ajouter un tag,
  relire les tags actuels et renvoyer le tableau complet
- Appeler `update_interaction(workspace_slug, interaction_id, <champs partiels>)`
- Output : `✅ Interaction mise à jour : <opportunité ou contact> · <champ(s) modifié(s)>`

---

### `update <texte libre>`

| Intention | Outils MCP |
|-----------|-----------|
| "passe X à Qualification", "stage X → Devis" | `kind_stages` (cache `whoami`) → `update_project_stage` |
| "X perdu", "X → Gagné" | `kind_stages` (cache `whoami`) → `update_project_stage` (stage terminal) |
| "budget de X : 10k€", "montant X = 8k€" | `update_project` (`amount_ht`) |
| "renomme X en Y" | `update_project` (`name`) |
| "qualifier X", "BANT de X" | → flux `qualify` |
| "timeline de X = Q4 2026" | `update_project` (description — bloc BANT) |

Workspace résolu via la règle ci-dessus. Confirmer avant toute écriture ambiguë.
Output : `✅ <Opportunité> → <champ>: <valeur>` / `❌ <Opportunité> → <outil>: <erreur>`

---

### `contact new <nom>`

Créer un contact (et son entreprise si nécessaire).

- Résoudre workspace
- `name` depuis l'argument (requis)
- Champs optionnels depuis le contexte : `email`, `phone`, `role`
- Entreprise : `list_companies(search=<mot distinctif du nom>)` ; si introuvable et nom mentionné →
  `create_company(workspace_slug, name)` d'abord
- Appeler `create_contact(workspace_slug, name, ...)` avec les champs disponibles
- Output : `✅ Contact créé : <name> · <entreprise ou "—">`

### `contact update <nom>`

- Résoudre workspace
- Résoudre le contact via `list_contacts(search=<nom ou email>)` — une page de 100, jamais la liste complète
- Appeler `update_contact` si disponible ; sinon → informer que la mise à jour de
  contact n'est pas encore supportée par l'API
- Output : `✅ Contact mis à jour : <name>` ou message d'erreur clair

---

### `doc <url ou markdown>`

Attacher un document à une opportunité.

- Résoudre workspace
- Identifier l'opportunité depuis le contexte (fuzzy match). Si ambigu, demander.
- `title` : inférer depuis l'URL ou demander
- Appeler `save_document(workspace_slug, title, content, project_id)`
- Output : `✅ Document attaché : <title> → <opportunité>`

---

Pour les instructions complètes et les règles de fuzzy match : charger le skill `crm` via le menu (`gtm:crm`) ou une description naturelle.
