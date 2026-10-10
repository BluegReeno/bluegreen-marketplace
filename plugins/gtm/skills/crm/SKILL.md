---
name: crm
description: >
  Pipeline commercial d'un workspace company : quatre gestes qui portent un jugement — new (doublon,
  vocabulaire, ébauche BANT), qualify (fusion du bloc BANT), stage (raison avant une perte, mission
  créée sur un gain), review (pipeline, dormantes d'abord). Déclencher sur : "nouvelle opportunité",
  "qualifie X", "passe X en devis envoyé", "X est perdu", "X est gagné", "quel est mon pipeline",
  "qu'est-ce qui dort". NE PAS déclencher pour : loguer un appel (→ gtm:call), corriger un contact
  ou une interaction, attacher un document (→ outil nommé dans la phrase), tâches et sprints (→ work).
allowed-tools: "mcp__plugin_hal_hal-mcp__whoami mcp__plugin_hal_hal-mcp__list_companies mcp__plugin_hal_hal-mcp__create_company mcp__plugin_hal_hal-mcp__list_contacts mcp__plugin_hal_hal-mcp__create_contact mcp__plugin_hal_hal-mcp__list_projects mcp__plugin_hal_hal-mcp__create_project mcp__plugin_hal_hal-mcp__update_project mcp__plugin_hal_hal-mcp__update_project_stage mcp__plugin_hal_hal-mcp__list_interactions"
---

# CRM — le pipeline, quatre gestes

Une opportunité est un projet hal de `kind: "opportunity"`. Une commande n'existe ici que si elle
enchaîne plusieurs outils ou porte un jugement ; tout le reste (corriger un contact, une
interaction, un montant, attacher un document) est un outil nommé dans la phrase.

Premier mot de l'argument : `new <nom>`, `qualify <nom>`, `stage <nom> <étape>`, `review`.
Sorties en français, identifiants en anglais.

## Pre-flight (tous les gestes)

`whoami`, une fois. Échec → « ❌ hal-mcp non connecté. Reconnexion : `/mcp` → `plugin:hal:hal-mcp` →
`authenticate`. » Puis résoudre le workspace : un slug passé en argument, sinon
`default_workspace_slug`, sinon demander (jamais deviner). Contrôles, dans cet ordre, chacun s'arrête
en nommant la cause :

1. le workspace est `archived` → aucune écriture n'est acceptée (`review` reste permis) ;
2. `opportunity` n'est pas dans son `kinds_enabled` → ce workspace n'a pas de pipeline.

Les étapes viennent de `kind_stages.opportunity` (`active`, `terminal`, `won`) de **ce** workspace,
jamais d'une liste écrite ici. `tags`, `ecosystem`, `activity_type` : uniquement les valeurs de
`allowed_tags`, `allowed_ecosystems`, `allowed_activity_types` ; `other` si rien ne convient.

**Retrouver une entreprise, un contact ou une opportunité** : `list_companies` et `list_contacts`
prennent `search` (sous-chaîne insensible à la casse, un mot distinctif, à raccourcir à zéro résultat
avant « introuvable »). `list_projects(kind="opportunity")` n'a pas de `search` : filtrer la page par
nom, en passant `limit` si `truncated` est vrai. Plusieurs candidats → demander ; jamais choisir par rang.

## `new <nom>`

1. **Doublon d'abord.** Chercher l'entreprise (`list_companies search`) puis l'opportunité
   (`list_projects kind=opportunity`, y compris les fermées). Une opportunité de même nom ou de même
   entreprise existe → la montrer et demander : reprendre l'existante ou créer quand même.
2. **Le tiers est obligatoire** : une opportunité porte une entreprise (`company_id`) ou, à défaut, un
   contact (`primary_contact_id`), sinon hal refuse. Entreprise inconnue → `create_company` avec un
   `ecosystem` et un `activity_type` pris dans les listes du workspace (les proposer, ne pas inventer) ;
   contact inconnu → `create_contact` (rôle, email, `company_id`). Chaque création est confirmée.
3. **Ébauche BANT** depuis la conversation ou le CR collé, au format ci-dessous ; champ inconnu = `"?"`.
4. `create_project(kind="opportunity", stage=<première étape de kind_stages.opportunity.active>, name,
   company_id | primary_contact_id, amount_ht si dit, description=<bloc BANT>, tags)`.
5. Sortie : `✅ <nom> → create_project : <stage>` et le bloc BANT écrit.

## `qualify <nom>`

BANT = Budget · Authority · Need · Timeline. Il vit dans la `description` de l'opportunité :

```yaml
bant:
  budget: "~5 k€ / formation"
  authority: "Marion Haas, coordinatrice formation"
  need: "Sensibilisation des équipes à l'IA, deux demi-journées"
  timeline: "Rentrée septembre 2026"
```

1. Retrouver l'opportunité ; lire sa `description` entière.
2. Extraire le BANT de la conversation ou du CR **sans rien déduire que le texte n'énonce pas** ;
   inconnu = `"?"`.
3. **Fusionner, jamais écraser** : un bloc `bant:` existe → ne remplacer que les champs renseignés ;
   un champ connu ne devient jamais `"?"` ; aucun bloc → l'ajouter en fin de description. Le reste de
   la description (sections `## BANT (agrégé)` ou `## Appels (agrégé)` de gtm:call, notes) n'est pas touché.
4. Montrer les quatre lignes avant/après, puis `update_project(project_id, description=<entière>)`.

## `stage <nom> <étape>`

1. Retrouver l'opportunité ; valider l'étape contre `kind_stages.opportunity` (`active` ∪ `terminal`) ;
   étape inconnue → proposer les valeurs légales. Même étape que l'actuelle → ne rien faire.
2. **Une étape terminale hors `won`** (une perte, un abandon) : demander **une ligne de raison**, l'ajouter
   à la `description` (`update_project`, description entière, section `## Clôture`) **avant** de fermer.
   Pas de raison, pas de fermeture.
3. `update_project_stage(project_id, stage)`. hal pose `closed_at` sur une étape terminale et `won_at`
   sur une étape de `won`, une seule fois.
4. **Une étape de `won`** : proposer la mission, si `client` est dans `kinds_enabled` — `create_project(
   kind="client", name=<nom de l'opportunité>, stage=<première étape de kind_stages.client.active>,
   company_id | primary_contact_id repris, amount_ht repris, converted_from_id=<l'opportunité>)`. Le nom
   d'un projet est unique par kind : en cas de refus, proposer un autre nom. Jamais sans oui.

## `review`

1. `list_projects(kind="opportunity", limit=…)` jusqu'à `truncated: false`. Garder les étapes `active`.
2. Pour chaque opportunité, la date du dernier échange : `list_interactions(project_id, limit=1)` ; sans
   échange, `updated_at`.
3. Afficher groupé par étape, **les plus dormantes d'abord** dans chaque groupe :
   `<project_ref ou —> · <entreprise ou contact> · <montant ou —> · <nom> · dernier échange <date> (<n> j)`.
   Fermées : un compte par étape terminale, sans détail.
4. Sortir **sans** la `description` (BANT et notes internes). Proposer, sans les créer, une relance ou
   une perte pour ce qui dort depuis plus d'un mois.

## Garde-fous

- Confirmer avant toute écriture ambiguë ; `--dry-run` affiche les appels (outil + arguments) sans les exécuter.
- Ne jamais auto-créer : doublon douteux ou tiers manquant → demander.
- Erreur hal : `❌ <entité> → <outil> : <raison>`, tel quel, sans réessai ni contournement. Une valeur
  refusée est relue dans le message (il énumère les valeurs permises), pas devinée.
