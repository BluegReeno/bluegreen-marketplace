---
name: crm
description: >
  CRM commercial Blue Green — opportunités, contacts, entreprises, CRs de
  meeting. Déclencher sur : /crm new, /crm qualify, /crm log, /crm update,
  /crm list, /crm contact, /crm doc, ou toute demande NL : "nouvelle
  opportunité", "qualifier le lead", "logger un CR commercial", "pipeline
  commercial", "attacher une propale".
  NE PAS déclencher pour : projets internes, tâches, sprints (→ /pm).
allowed-tools: "Bash(uv *) Bash(python3 *) Bash(python *) Bash(git *) Bash(mkdir *) Bash(cat *) Read Write Edit Glob"
---

# CRM — Pipeline commercial Blue Green via hal-mcp (Claude Code)

Ce skill route les instructions NL vers le connecteur MCP `hal-mcp` (backend
Supabase). Zéro script, zéro Bash — pur NL → mapping MCP.

**Scope** : opportunités commerciales, contacts, entreprises, CRs de meeting,
propales, relances. Les projets internes Blue Green sont hors scope → skill `/pm`.

Les opportunités sont des **projets** hal avec `kind: "opportunity"`. Toutes les
commandes CRM filtrent par `kind="opportunity"` pour les lire, et passent
`kind: "opportunity"` à la création.

---

## Pre-flight : vérifier hal-mcp

Avant toute opération MCP, vérifier que le connecteur est actif via `whoami` :

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

## Workspace resolution (s'applique à toutes les commandes /crm)

Chaque appel MCP doit passer un `workspace_slug`. Le pre-flight a déjà mis en
cache la réponse `whoami`. Résoudre dans cet ordre :

1. **Arg explicite** (`/crm list blue-green`, `/crm new Mariana Haas ic`) → utiliser
   ce slug directement. RLS valide la membership côté serveur.
2. **Pas d'arg** → utiliser `default_workspace_slug` depuis le cache `whoami`.
   - Non-null → l'utiliser comme `workspace_slug`.
   - `null` avec `workspaces` non vide → lister les slugs dispo et demander.
   - `null` avec `workspaces` vide → répondre et stopper :

     > ❌ Aucun workspace assigné à ton compte.
     > Demande à ton administrateur BlueGreen d'ajouter ton email aux workspaces concernés dans Supabase.

---

## /crm list `[workspace]`

Affiche le pipeline commercial en kanban texte groupé par stage.

### Étapes

**1. Résoudre workspace** — règle standard ci-dessus.

**2. Appeler `list_projects`**

- `workspace_slug` (résolu)
- `kind: "opportunity"`
- Pas de filtre de stage — vue pipeline complète

**3. Grouper et afficher**

Grouper par `stage`. Ordre :
- **Stages actifs** = stages avec au moins une opportunité `closed_at` null (d'abord)
- **Stages terminaux** = stages où toutes les opportunités ont `closed_at` non-null (en dernier)
- Dans chaque stage : ordre serveur (`created_at DESC`)

Format d'affichage :

```
### Prospect (2)
- OPP-04 · Mariana Haas · ~5k€ · Formation IA
- OPP-01 · Cabinet Dupont · — · —

### Qualification (1)
- OPP-02 · CFA Montpellier · 12 000 € · Diagnostic numérique

### ✓ Perdu (1)
- OPP-03 · Société X · — · — terminé 2026-05-10
```

Ligne par opportunité :
`{project_ref ou "—"} · {company.name ou nom ou "—"} · {amount_ht formaté ou "—"} · {name}`

- Format `amount_ht` : milliers séparés par espace + ` €`. Afficher `—` si null.
- Stages terminaux : préfixer `✓ `, ajouter `— terminé {closed_at[:10]}`.
- Ne jamais afficher le champ `description` (contient le BANT — données internes).

**4. Cas limites**

- Aucune opportunité → `Aucune opportunité dans le workspace <slug>.`
- Stage vide → ne pas afficher la section

---

## /crm new `<nom>`

Créer une nouvelle opportunité commerciale.

### Étapes

1. **Résoudre workspace** — règle standard.
2. Collecter depuis la conversation ou demander si absent :
   - `name` (requis) — le nom passé après `/crm new`
   - `company_id` (optionnel) — si une entreprise est mentionnée, résoudre via
     `list_companies` (fuzzy match)
   - `amount_ht` (optionnel) — montant estimé si mentionné
   - `description` (optionnel) — contexte ou notes initiales
3. Appeler `create_project` avec :
   - `workspace_slug`
   - `name`
   - `kind: "opportunity"`
   - `stage: "Prospect"` (stage initial fixe)
   - champs optionnels disponibles
4. Output : `✅ Opportunité créée : <ref> · <name> · Prospect`

---

## /crm qualify `<nom>`

Qualifier une opportunité avec la méthode BANT.

BANT = **B**udget · **A**uthority · **N**eed · **T**imeline

### Étapes

1. **Résoudre workspace** — règle standard.
2. **Résoudre l'opportunité** — fuzzy match sur `name` via `list_projects(kind="opportunity")`.
   Seuils : > 80 → match direct ; 50–80 → lister candidats, demander ; < 50 → introuvable.
3. **Extraire BANT** — analyser le contexte conversation (CR partagé, notes, échanges)
   pour identifier :
   - `budget` — enveloppe budgétaire ou ordre de grandeur
   - `authority` — décisionnaire ou prescripteur identifié
   - `need` — besoin principal, problématique ou objectif
   - `timeline` — horizon de décision ou de démarrage
4. **Construire le bloc BANT** :

```yaml
bant:
  budget: "~5k€ / formation"
  authority: "Marion Haas, coordinatrice formation"
  need: "Sensibilisation équipes à l'IA, 2 demi-journées"
  timeline: "Rentrée septembre 2026"
```

   Si un champ n'est pas identifiable → valeur `"?"`.

5. **Fusionner avec la description existante** :
   - Si `description` contient déjà un bloc `bant:` → remplacer uniquement les champs renseignés
     (ne pas écraser les valeurs existantes par `"?"`).
   - Sinon → ajouter le bloc BANT en fin de description.
6. Appeler `update_project` avec `workspace_slug`, `project_id`, `description` mise à jour.
7. Output :

```
✅ BANT mis à jour : <nom>
  Budget : ~5k€ / formation
  Authority : Marion Haas, coordinatrice formation
  Need : Sensibilisation équipes à l'IA, 2 demi-journées
  Timeline : Rentrée septembre 2026
```

   Afficher `?` pour les champs non identifiés.

---

## /crm log `<note ou CR markdown>`

Enregistrer un CR de meeting ou une note commerciale liée à une opportunité.

### Étapes

1. **Résoudre workspace** — règle standard.
2. **Identifier l'opportunité** depuis le contexte conversation (fuzzy match sur `name`
   via `list_projects(kind="opportunity")`). Si ambigu, demander.
3. Collecter :
   - `summary` (requis) — la note ou le CR passé après `/crm log`
   - `channel` — `meeting` par défaut pour un CR, `email` si suivi email
   - `project_id` — résolu à l'étape 2
   - `occurred_at` (optionnel) — si une date est mentionnée ; défaut = maintenant
4. **Structurer le CR** si un texte libre est passé. Format attendu :

```markdown
## CR — [Entreprise] — [Date]
**Participants :** [liste]
**Durée :** XX min

### Notes clés
...

### BANT extrait
- **Budget :** ...
- **Authority :** ...
- **Need :** ...
- **Timeline :** ...

### Next steps
- [ ] action 1
- [ ] action 2
```

5. Appeler `log_interaction` avec `workspace_slug`, `channel`, `summary` (CR structuré),
   `project_id`, `occurred_at`.
6. **Extraction BANT automatique** — après le log, tenter d'extraire le BANT depuis le CR :
   - Si des infos BANT sont identifiables → appeler `update_project` pour mettre à jour
     la description (même logique que `/crm qualify`).
   - Si rien n'est extractable → ne pas mettre à jour la description, ne pas signaler.
7. Output : `✅ CR logué sur <opportunité>` (+ `✅ BANT mis à jour` si extraction réussie).

**Règle** : ne jamais bloquer un log. Si l'opportunité est introuvable (score < 50),
logger quand même en incluant le nom de l'opportunité dans `summary`.

---

## /crm update `<texte libre>`

Mettre à jour le stage, le budget, la timeline, les contacts ou tout autre champ
d'une opportunité.

### Étapes

1. **Résoudre workspace** — règle standard.
2. **Parser l'intention** : détecter l'opportunité cible et le(s) champ(s) à modifier.
3. **Résoudre l'opportunité** — fuzzy match sur `name` (seuils standard).
4. **Router l'écriture** :
   - `stage` → appeler `list_stages(workspace_slug)` pour valider le stage cible,
     puis `update_project_stage(workspace_slug, project_id, stage)`
   - `amount_ht`, `description`, `name`, `location` → `update_project`
   - Si le texte contient "BANT" ou des infos budget/authority/need/timeline →
     appliquer la logique `/crm qualify` sur l'opportunité résolue
5. Confirmer avant toute écriture ambiguë.
6. Output : `✅ <Opportunité> → <champ>: <valeur>`

### Intent → tool mapping

| L'utilisateur dit | Outil(s) MCP |
|-------------------|-------------|
| "passe X à Qualification", "stage X → Devis", "X perdu" | `list_stages` → `update_project_stage` |
| "budget de X : 10k€", "montant X = 8k€" | `update_project` (`amount_ht`) |
| "renomme X en Y" | `update_project` (`name`) |
| "X → Gagné", "fermer X comme gagné" | `list_stages` → `update_project_stage` (stage gagné) |
| "qualifier X", "BANT de X" | → flux `/crm qualify` |
| "mettre à jour la timeline de X" | `update_project` (`description` — bloc BANT) |

---

## /crm contact `new <nom> | update <nom>`

Gérer les contacts et entreprises liés au CRM.

### `contact new <nom>`

1. **Résoudre workspace** — règle standard.
2. Collecter depuis la conversation ou demander si absent :
   - `name` (requis)
   - `email` (optionnel)
   - `phone` (optionnel)
   - `role` (optionnel) — ex. "coordinatrice formation"
   - Entreprise associée : chercher via `list_companies` (fuzzy match). Si introuvable
     et nom mentionné → proposer de créer l'entreprise d'abord.
3. Si l'entreprise doit être créée :
   - Appeler `create_company(workspace_slug, name)`.
   - Output : `✅ Entreprise créée : <name>`
4. Appeler `create_contact(workspace_slug, name, ...)` avec les champs collectés.
5. Output : `✅ Contact créé : <name> · <entreprise ou "—">`

### `contact update <nom>`

1. **Résoudre workspace** — règle standard.
2. Résoudre le contact via `list_contacts` (fuzzy match sur `name`).
3. Si le connecteur MCP expose un outil `update_contact` → l'appeler avec les champs
   modifiés. Sinon → informer que la mise à jour de contact n'est pas encore supportée
   par l'API et proposer de recréer le contact.
4. Output : `✅ Contact mis à jour : <name>` ou message d'erreur clair.

---

## /crm doc `<url ou markdown>`

Attacher un document (propale, brochure, Google Doc) à une opportunité.

### Étapes

1. **Résoudre workspace** — règle standard.
2. **Identifier l'opportunité** depuis le contexte (fuzzy match). Si ambigu, demander.
3. Collecter :
   - `title` — inférer depuis l'URL ou le contexte, ou demander
   - `content` — URL ou contenu markdown
   - `project_id` — résolu ci-dessus
4. Appeler `save_document` avec `workspace_slug`, `title`, `content`, `project_id`.
5. Output : `✅ Document attaché : <title> → <opportunité>`

---

## Opportunity resolution (fuzzy match)

Seuils : score **> 80** → match direct ; **50–80** → lister les candidats, demander ;
**< 50** → entité introuvable, proposer création.

- Matcher sur `name`. Appeler `list_projects(kind="opportunity")` sans filtre de stage.
- Ambiguïté : plusieurs opportunités au même score → lister, demander.
- Ne jamais auto-créer sur un match ambigu. Score < 50 → proposer `/crm new`.

---

## Guardrails

- **Confirmer avant toute écriture ambiguë.** Dans le doute, demander.
- **Dry-run** : si l'utilisateur ajoute `--dry-run`, afficher le plan MCP
  (nom tool + args) sans exécuter.
- **Ne jamais auto-créer.** Score < 50 → proposer création, attendre confirmation.
- **BANT** : ne jamais écraser un champ BANT existant avec `"?"`. Fusionner,
  ne pas remplacer.
- **Format de sortie** : `✅ [Entité] → [tool]: [valeur]` par écriture réussie.
- **Erreur MCP** : `❌ [Entité] → [tool]: [raison d'erreur]`. Afficher
  immédiatement — ne pas réessayer automatiquement.
- **Description = champ privé** : ne jamais afficher le contenu de `description`
  dans `/crm list` — il contient le BANT et des notes internes.

---

## Out of scope

- **Projets internes BG** (→ `/pm`) : tâches, sprints, notes d'avancement,
  outils `create_task`, `list_tasks`, `create_sprint`, `assign_task_to_sprint`.
- **Edifice missions** (→ `/edifice`) : rapports terrain, inspection bâtiments.
- **Job Search** (→ `obsidian-crm`) : candidatures, entretiens, CV.
- **Facturation** : les devis et factures ne sont pas encore dans hal — à venir.
