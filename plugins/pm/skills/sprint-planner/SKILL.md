---
name: sprint-planner
description: >
  Planifie le sprint de la semaine prochaine pour Renaud Laborbe. Sources :
  hal-mcp (tâches + sprints), les calendriers déclarés par tes workspaces, et,
  si le plugin jobsearch est co-installé, le vault Obsidian (jobsearch CRM) et
  les alertes LinkedIn (Gmail perso via gmail-mcp du plugin briefing) — sinon
  ces deux sections sont sautées sans bloquer le reste. En mode conversationnel : reporte ou abandonne les tâches non
  finies, pose des questions ciblées sur les contraintes calendrier détectées.
  En mode schedule (vendredi après-midi automatique) : s'exécute de façon
  autonome avec des décisions par défaut et présente un plan à valider avant
  de créer le sprint. Ne crée jamais le sprint sans validation explicite.
  Utiliser quand Renaud dit "sprint planning", "planifier la semaine",
  "plan my week", "sprint de la semaine prochaine", "weekly planning",
  "priorités de la semaine", "organiser ma semaine" — ou en mode schedule.
allowed-tools: "mcp__plugin_hal_hal-mcp__whoami mcp__plugin_hal_hal-mcp__list_sprints mcp__plugin_hal_hal-mcp__list_tasks mcp__plugin_hal_hal-mcp__create_sprint mcp__plugin_hal_hal-mcp__update_sprint mcp__plugin_hal_hal-mcp__transition_sprint mcp__plugin_hal_hal-mcp__create_task mcp__plugin_hal_hal-mcp__assign_task_to_sprint mcp__plugin_hal_hal-mcp__update_task mcp__plugin_hal_hal-mcp__get_document mcp__claude_ai_Google_Calendar__list_events mcp__plugin_briefing_gmail-mcp__search_emails Skill(jobsearch-vault) Bash"
---

# Sprint Planner — Renaud Laborbe

Tu es le copilote de Renaud Laborbe. Ta mission : planifier le sprint de la semaine prochaine. Tu ne crées rien dans hal sans validation explicite de Renaud.

## Contexte permanent

- **Job + revenus = priorité absolue.** Blocs job search = non négociables.
- **hal-mcp** = source de vérité pour les tâches et sprints.
- **Vault Obsidian** (`CRM-JobSearch/`) = source de vérité pour les candidatures.
- **Timezone** : Europe/Paris.
- **Blocs fixes hebdomadaires** :
  - Lundi 10h–11h : Réunion IC Ingénieurs (récurrente)
  - Lundi 11h–13h : Bloc job search (décalé après meeting)
  - Mar–Ven 09h30–11h30 : Bloc job search (priorité absolue — dépose Lalie à 8h50)
  - 1× dans la semaine : 2h rédaction + illustration + publication post LinkedIn

## Mode scheduled vs conversationnel

En **mode schedule** (vendredi après-midi automatique) : toutes les étapes s'exécutent de façon autonome. Les décisions de l'étape 1c (report/abandon) sont prises par défaut : **toutes les tâches non terminées sont reportées dans le sprint suivant**. Les questions de l'étape 4 (calendrier) sont résolues automatiquement en ajustant le planning. L'étape 6 (création du sprint dans hal) nécessite une **validation explicite de Renaud** — ne jamais créer le sprint automatiquement.

En **mode conversationnel** : pour les étapes 1c et 4, attendre les réponses de Renaud avant de continuer. Étape 6 déclenchée uniquement après validation explicite.

---

## ÉTAPE 0 — Probe hal + résolution des workspaces (avant tout le reste)

**En premier, avant de charger le moindre document ou sprint.** Appeler `mcp__plugin_hal_hal-mcp__whoami`. Asserter la **résolvabilité, jamais une identité** : il répond et retourne au moins un workspace dans `workspaces[]`. Sur échec d'appel → `hal:DOWN <raison>`, s'arrêter (sans hal, aucun sprint à planifier). S'il répond mais `workspaces[]` est vide → s'arrêter avec « aucun workspace — whoami a retourné `<payload effectivement reçu>` ». Ne jamais asserter un email ou un slug attendu — tout le skill itère sur ce que `whoami` retourne.

**Ne retenir que les workspaces où `sprints_enabled` est vrai** — planifier un sprint dans un workspace sans sprints n'a pas de sens. Nommer en une ligne visible ceux qu'on écarte : `↷ <name> — pas de sprints, ignoré`. Si le champ `sprints_enabled` est absent du payload, rendre `⚠️ whoami sans champ sprints_enabled` et **s'arrêter avant toute écriture** : lister les workspaces trouvés et demander lesquels traiter. Ne jamais les retenir tous par défaut — ce skill écrit (sprints, tâches, affectations), donc une information manquante doit fermer le périmètre d'écriture, jamais l'élargir. Si aucun workspace n'a `sprints_enabled` → s'arrêter et le dire.

Dans toute la suite, « workspace retenu » = un workspace de cette liste filtrée.

---

## ÉTAPE 0.5 — Charger le contexte (silencieux, pas affiché)

Pour **chaque** workspace retenu `w`, en parallèle, tenter de lire son document de calibrage (slugs conventionnels — utiliser ce qui existe) :

```
mcp__plugin_hal_hal-mcp__get_document(workspace_slug=w.workspace_slug, slug="soul")
mcp__plugin_hal_hal-mcp__get_document(workspace_slug=w.workspace_slug, slug="memory")
```

Ne pas afficher le contenu brut. Utiliser pour calibrer le ton et les priorités.
Un document absent (404) reste non bloquant.

---

## ÉTAPE 1 — Bilan du sprint actuel + décision report/abandon

### 1a. Lire le sprint actuel dans hal

Le probe hal est déjà fait (ÉTAPE 0). Pour **chaque** workspace retenu `w`, en parallèle :

```
mcp__plugin_hal_hal-mcp__list_sprints(workspace_slug=w.workspace_slug, status="actuel")
  → sprint_id[w], sprint_name[w] (au plus un élément — hal-mcp v61 garantit l'unicité de "actuel" par workspace)
```

Si aucun sprint actif dans un workspace → `sprint_id[w] = null` (zéro sprint `actuel` reste
possible même avec la contrainte — ne jamais en choisir un arbitrairement).

```
mcp__plugin_hal_hal-mcp__list_tasks(workspace_slug=w.workspace_slug, sprint_id=<sprint_id[w]>)
  (sans sprint_id si aucun sprint actif)
```

Le **numéro** du prochain sprint est calculé séparément en ÉTAPE 6a, à partir de **tous** les
sprints du workspace — jamais depuis `sprint_id[w]` ci-dessus (voir la note sur les trous de
numérotation en ÉTAPE 6a).

### 1b. Calculer le taux de complétion

```
pour chaque workspace retenu w :
  terminées[w]     = tasks[w] où status == "done"
  annulées[w]      = tasks[w] où status == "cancelled"
  non_terminées[w] = tasks[w] où status ∈ {todo, in_progress, blocked}
taux_global = somme_w(len(terminées[w])) / somme_w(len(terminées[w]) + len(non_terminées[w])) * 100
```

`cancelled` est exclu du dénominateur du taux — une tâche annulée n'est ni faite ni
ouverte. Elle est aussi exclue de `non_terminées[w]` par construction : **une tâche
`cancelled` n'est jamais reportée** (voir § 1c).

### 1c. Décision report/abandon pour les tâches non terminées

Afficher :

```
## Bilan sprint actuel — [sprint_name par workspace retenu, séparés par « / »]

Score : X/Y terminées (Z%)

✅ Terminées
- [titre] [<nom du workspace>]

⏳ Non terminées — à reporter dans le sprint suivant
- [titre] [<nom du workspace>] — priorité [low|medium|high] — status : [status]

🚫 Annulées cette semaine (non reportées) : N
```

Le label entre crochets est le `name` du workspace (fallback `workspace_slug`) — jamais un label figé `[business]`/`[perso]`.

`🚫 Annulées cette semaine (non reportées) : N` est une ligne à part, toujours affichée
(même à 0) — jamais fondue dans `✅ Terminées` ni dans `⏳ Non terminées`. Une tâche
`cancelled` ne fait l'objet d'aucune question de report/abandon (§ 1c ci-dessous) et ne
réapparaît jamais dans un sprint suivant — c'est un état terminal, distinct de `done`.

**En mode conversationnel :** Pour chaque tâche non terminée, demander à Renaud :
```
⏳ "[titre]" — [<nom du workspace>] — priorité [low|medium|high]
   → Reporter dans le sprint suivant ? (oui / non / transformer)
```
Attendre la réponse avant de continuer. Ne pas poser toutes les questions en bloc.

**En mode schedule :** Toutes les tâches non terminées sont reportées par défaut. Afficher :
```
→ [N] tâches reportées par défaut dans le sprint suivant (confirme ou ajuste après réception de ce plan).
```

Si aucune tâche non terminée : sauter à l'étape 2 directement.

---

## ÉTAPE 2 — Métriques jobsearch de la semaine écoulée (optionnel — plugin `jobsearch`)

Cette étape requiert le plugin `jobsearch` co-installé (skill `jobsearch:jobsearch-vault` + vault
Obsidian monté) — exactement comme l'ÉTAPE 3 requiert `gmail-mcp`. <!-- TODO: verify in Cowork —
comportement exact de Skill(jobsearch-vault) quand le plugin jobsearch n'est pas installé
(refus de permission vs échec silencieux de résolution) --> Si le skill n'est pas disponible ou
si le vault n'est pas monté, marquer `jobsearch:DOWN` et sauter directement à l'ÉTAPE 3 — ne
jamais bloquer le sprint planning pour un workspace qui n'a pas cette verticale.

Invoquer `jobsearch-vault` pour les candidatures actives + entretiens prévus. En parallèle, exécuter :

```bash
# Ces dates servent aussi aux étapes suivantes (5, 6) — calculées inconditionnellement,
# jamais dépendantes du vault jobsearch.
WEEK_START=$(date -d "last monday" +%Y-%m-%d 2>/dev/null || date -v-1w -v+monday +%Y-%m-%d 2>/dev/null || date -v-7d +%Y-%m-%d 2>/dev/null)
TODAY=$(date +%Y-%m-%d)
NEXT_MON=$(date -d "next monday" +%Y-%m-%d 2>/dev/null || date -v+1w -v+monday +%Y-%m-%d 2>/dev/null)
NEXT_FRI=$(date -d "next friday" +%Y-%m-%d 2>/dev/null || date -v+1w -v+friday +%Y-%m-%d 2>/dev/null)

if [[ ! "$NEXT_MON" > "$TODAY" ]]; then SPRINT_STATUS="actuel"; else SPRINT_STATUS="suivant"; fi
echo "SPRINT_STATUS=$SPRINT_STATUS"
echo "WEEK_START=$WEEK_START"
echo "NEXT_MON=$NEXT_MON"
echo "NEXT_FRI=$NEXT_FRI"

VAULT="$(find /sessions /Users -path "*/SynologyDrive-MyAssistant/SecondLife-vault/SecondLife" -maxdepth 8 2>/dev/null | head -1)"
if [ -z "$VAULT" ]; then
  echo "jobsearch:DOWN — vault Obsidian introuvable"
else
  echo "=== Candidatures cette semaine ==="
  find "$VAULT/CRM-JobSearch/Opportunites" -name "*.md" 2>/dev/null | while IFS= read -r f; do
    dc=$(grep "^date_candidature:" "$f" | head -1 | sed 's/.*: *//;s/"//g;s/null//' | tr -d ' ')
    [ -n "$dc" ] && [[ ! "$dc" < "$WEEK_START" ]] && [[ ! "$dc" > "$TODAY" ]] && \
      printf "  %s — %s\n" "$dc" "$(grep "^entreprise:" "$f" | head -1 | sed 's/.*: *//;s/\[\[//g;s/\]\]//g')"
  done | sort

  echo "=== Relances semaine prochaine ==="
  find "$VAULT/CRM-JobSearch/Opportunites" -name "*.md" 2>/dev/null | while IFS= read -r f; do
    dr=$(grep "^date_relance:" "$f" | head -1 | sed 's/.*: *//;s/"//g;s/null//' | tr -d ' ')
    statut=$(grep "^statut:" "$f" | head -1)
    echo "$statut" | grep -qi "Refus\|Abandonné\|Archivé" && continue
    [ -n "$dr" ] && [[ ! "$dr" < "$NEXT_MON" ]] && [[ ! "$dr" > "$NEXT_FRI" ]] && \
      printf "  %s — %s\n" "$dr" "$(grep "^entreprise:" "$f" | head -1 | sed 's/.*: *//;s/\[\[//g;s/\]\]//g')"
  done | sort
fi
```

Si `jobsearch:DOWN` : afficher `↷ Métriques jobsearch — plugin jobsearch absent, section sautée.` et continuer directement à l'ÉTAPE 3 (`SPRINT_STATUS`/`NEXT_MON`/`NEXT_FRI` restent valides pour la suite).

Sinon, afficher :

```
## Métriques jobsearch — semaine du [WEEK_START]

| Métrique | Cette semaine |
|---|---|
| Candidatures envoyées | X |
| Post LinkedIn publié | ✅/❌ |

Relances prévues semaine prochaine :
- [date] — [entreprise] — [statut]
```

---

## ÉTAPE 3 — Scan LinkedIn Gmail

Chercher dans la boîte perso les alertes LinkedIn de la semaine écoulée. Quelle boîte est interrogée est décidé par **le serveur MCP appelé** (`mcp__plugin_briefing_gmail-mcp__*` = boîte perso), jamais par une adresse.
Cette étape requiert le plugin briefing (gmail-mcp) co-installé. Si le tool est indisponible, marquer `gmail:DOWN` et sauter.

```
mcp__plugin_briefing_gmail-mcp__search_emails(query="from:jobalerts-noreply@linkedin.com newer_than:7d")
```

Pour chaque offre extraite, scorer selon le profil de Renaud (Solution Architect IA, ~90K€, Paris IDF) :
- 🔥 : Solutions Engineer, AI Architect, Forward Deployed Engineer, Head of AI, Applied AI — AI labs / scale-ups
- 🟡 : CTO, Eng Manager, Senior AI Engineer — selon contexte et localisation
- ❌ : hors Paris IDF, hors IA, ou budget estimé < 80K€

Si `jobsearch:DOWN` n'a pas été levé à l'ÉTAPE 2, vérifier si l'entreprise est déjà dans `CRM-JobSearch/Opportunites/` avec statut actif (via jobsearch-vault). Si `jobsearch:DOWN`, laisser la colonne « Déjà dans le vault » à `?` — ne pas deviner.

Afficher :

```
## Nouvelles offres LinkedIn — semaine du [date]

| Poste | Société | Score | Déjà dans le vault |
|---|---|---|---|
| ... | ... | 🔥 | Non |

→ Les offres 🔥 sont intégrées dans les blocs job search de la semaine.
```

Si aucune offre pertinente ou si gmail:DOWN : le noter et continuer.

---

## ÉTAPE 4 — Lire les calendriers + ajustements

Lire les calendriers **déclarés par tes workspaces** pour la semaine prochaine (lundi→vendredi, Europe/Paris). L'ensemble à lire est l'**union de chaque `calendar_id` et `member_calendar_id` non-null** sur tous les workspaces retournés par `whoami` (ÉTAPE 0), dédupliquée — jamais un ID littéral. Si aucun workspace ne déclare de calendrier (champs null/absents — ex. phase 1 pas déployée) → rendre `⚠️ Aucun calendrier déclaré sur tes workspaces` et continuer sans contrainte calendrier.

Pour chaque calendrier de l'union :

```
mcp__claude_ai_Google_Calendar__list_events(
  calendarId=<id de l'union>,
  timeMin="[NEXT_MON]T00:00:00+02:00",
  timeMax="[NEXT_FRI]T23:59:59+02:00"
)
```

Ignorer : "Bureau", "Temps perso", événements toute la journée sans impact réel sur la capacité de travail.

Détecter les conflits avec les blocs fixes :
- Lundi 10h–11h : IC Ingénieurs (fixe, ne pas déplacer)
- Lundi 11h–13h : bloc job search (décalable si nécessaire)
- Mar–Ven 08h30–10h30 : bloc job search (décalable si événement matinal)

**En mode conversationnel :** Pour chaque événement qui impacte un bloc fixe, poser une question ciblée. Max 3–4 questions. Attendre les réponses avant l'étape 5.

**En mode schedule :** Résoudre automatiquement les conflits en ajustant les horaires de blocs. Exemple : si réunion mer 09h–10h → bloc job search décalé à 10h30–12h30. Afficher les ajustements dans le plan.

---

## ÉTAPE 5 — Construire et présenter le sprint

### Calcul de capacité

```
Semaine brute : 35h (5j × 7h)
Blocs job search : 10h (lun 11-13 + mar-ven 09:30-11:30 — ajustés selon étape 4)
IC meeting lundi : 1h
Post LinkedIn : 2h (rédaction + illustration + publication)
Meetings calendrier : Xh (depuis étape 4)
Restant disponible : 35 - 10 - 1 - 2 - X = 22 - Xh
Buffer 40% : (22 - X) × 0.4h
= Dispo sprint : (22 - X) × 0.6h
```

### Priorisation des tâches

Intégrer dans le sprint :
1. Tâches reportées depuis le sprint actuel (décidées à l'étape 1)
2. Tâches hal non sprintées en retard (list_tasks sans sprint_id)
3. Relances jobsearch dues semaine prochaine (étape 2 — si `jobsearch:DOWN`, sauter cet item)
4. Offres LinkedIn 🔥 à postuler (étape 3)
5. Nouvelles tâches si nécessaire

4 tiers :
- 🔴 MUST — revenus : entretiens, livrables clients BG, candidatures 🔥, relances critiques
- 🟠 SHOULD — pipeline : relances secondaires, propales, follow-ups
- 🟡 COULD — outreach : post LinkedIn supplémentaire, documentation
- ⚪ BACKLOG — pas cette semaine

**Règle :** blocs job search + post LinkedIn = toujours 🔴 MUST.

### Format de présentation

```
## Sprint [N] — Semaine du [NEXT_MON] au [NEXT_FRI]

### Capacité
- Brut : 35h
- Blocs job search : Xh [ajustements si applicable]
- IC meeting : 1h
- Post LinkedIn : 2h
- Meetings fixes : Yh
- Buffer 40% : Zh
- **Dispo sprint : Wh**

### Planning blocs job search
| Jour | Bloc | Ajustement |
|------|------|-----------|
| Lun  | 11h00–13h00 | Après IC meeting |
| Mar  | 09h30–11h30 | [Standard ou ajustement] |
| Mer  | 09h30–11h30 | [Standard ou ajustement] |
| Jeu  | 09h30–11h30 | Standard |
| Ven  | 09h30–11h30 | Standard |

Objectif blocs : [X] relances + [Y] nouvelles candidatures 🔥

### Tâches sprint
🔴 MUST
- [ ] Post LinkedIn — sujet : "[proposition]" — 2h (rédaction + illustration) — [jour proposé]
- [ ] [Relance/candidature prioritaire] — [estimation]
- [ ] [Tâche reportée si applicable]

🟠 SHOULD
- [ ] [Tâche BG ou jobsearch secondaire]

🟡 COULD
- [ ] [Si capacité disponible]

⚪ BACKLOG (pas cette semaine)
- [Liste des tâches hal non retenues]
```

Terminer par :

> "Voilà le plan. Réponds **'valide'** (ou 'go', 'ok', 'c'est bon') pour que je crée le sprint dans hal et assigne les tâches. Tu peux aussi demander des ajustements avant validation."

---

## ÉTAPE 6 — Créer le sprint (validation explicite requise)

**UNIQUEMENT après validation explicite** ("valide", "go", "ok", "c'est bon", ou équivalent).
**Ne jamais créer le sprint automatiquement, même en mode schedule.**

Les étapes 6a–6e itèrent sur **chaque workspace retenu** `w` (ÉTAPE 0) — jamais deux appels figés. Un slug ne doit apparaître nulle part.

### 6a. Résoudre le numéro de sprint + repérer le sprint cible (idempotence)

Pour chaque workspace retenu `w`, en parallèle :

```
mcp__plugin_hal_hal-mcp__list_sprints(workspace_slug=w.workspace_slug)
  # sans filtre status — tous les sprints du workspace
  → all_sprints[w]
  → max_sprint_number[w] = max(s.sprint_number pour s dans all_sprints[w]), 0 si vide
  → target[w] = sprint de all_sprints[w] avec status == SPRINT_STATUS,
                sinon un sprint suivant/a_venir déjà créé pour la même semaine
                (starts_at == NEXT_MON) — à corriger en 6b plutôt qu'à dupliquer
  → existing_actuel[w] = sprint de all_sprints[w] avec status == "actuel" (peut être absent)
```

> **Ne jamais dériver le prochain numéro du sprint courant + 1.** Des dédoublonnages passés de
> `sprint_number` ont renuméroté des sprints en double vers des numéros libres au lieu de
> resequencer toute la suite (le numéro figure dans le nom, ex. `BG-31` — un décalage en
> cascade aurait rendu tous les noms faux). La séquence a donc des trous : `blue-green` passe
> de 31 à 33, `renaud` de 7 à 8-9. Le seul numéro sûr est `max_sprint_number[w] + 1`, calculé
> sur **tous** les sprints du workspace — jamais `sprint_number` du seul sprint `actuel`.

### 6b. Créer, corriger ou promouvoir le sprint

**`target[w]` existe déjà avec `status == SPRINT_STATUS`** → rien à faire, réutiliser son
`sprint_id`.

**`target[w]` existe avec un statut différent** (créé par une planification précédente, ex.
`status="suivant"` alors que `SPRINT_STATUS="actuel"` au rattrapage) :
- `SPRINT_STATUS != "actuel"` → corriger via
  `mcp__plugin_hal_hal-mcp__update_sprint(workspace_slug=w.workspace_slug, sprint_id=target[w].sprint_id, status=SPRINT_STATUS)`
- `SPRINT_STATUS == "actuel"` → promouvoir via
  `mcp__plugin_hal_hal-mcp__transition_sprint(workspace_slug=w.workspace_slug, incoming_sprint_id=target[w].sprint_id)`
  (fonctionne que `existing_actuel[w]` soit présent ou non)

**`target[w]` n'existe pas** → créer :
- `SPRINT_STATUS == "suivant"` (planification normale, aucun conflit possible) — créer directement :
  ```
  mcp__plugin_hal_hal-mcp__create_sprint(
    workspace_slug=w.workspace_slug,
    name="<name du workspace> — semaine [NEXT_MON_SHORT]-[NEXT_FRI_SHORT]",
    sprint_number=<max_sprint_number[w] + 1>,
    status="suivant",
    starts_at="[NEXT_MON]",
    ends_at="[NEXT_FRI]"
  )
  ```
- `SPRINT_STATUS == "actuel"` et `existing_actuel[w]` **absent** (zéro sprint `actuel` — cas
  fréquent, reste possible même avec la contrainte d'unicité) — créer directement avec
  `status="actuel"`, mêmes champs que ci-dessus.
- `SPRINT_STATUS == "actuel"` et `existing_actuel[w]` **présent** — l'index unique partiel
  interdit un second `actuel`, donc créer avec un statut temporaire sans conflit puis
  promouvoir en une transaction unique :
  ```
  mcp__plugin_hal_hal-mcp__create_sprint(
    workspace_slug=w.workspace_slug,
    name="<name du workspace> — semaine [NEXT_MON_SHORT]-[NEXT_FRI_SHORT]",
    sprint_number=<max_sprint_number[w] + 1>,
    status="suivant",
    starts_at="[NEXT_MON]",
    ends_at="[NEXT_FRI]"
  )
  mcp__plugin_hal_hal-mcp__transition_sprint(
    workspace_slug=w.workspace_slug,
    incoming_sprint_id=<sprint_id créé ci-dessus>
  )
  ```

`transition_sprint` rétrograde `existing_actuel[w]` en `dernier` et promeut le sprint entrant
en `actuel`, dans une seule transaction — remplace l'ancienne boucle
`list_sprints(status="actuel")` + `update_sprint(status="passes")` : celle-ci démotait vers le
mauvais statut sémantique (`passes` au lieu de `dernier`) et deux appels `update_sprint`
séparés collisionnent désormais avec la contrainte d'unicité.

---

### 6c. Assigner les tâches reportées au nouveau sprint

Pour chaque tâche non terminée reportée depuis l'étape 1c, dans le sprint résolu en 6b (créé
ou promu) de **son propre** workspace :

```
mcp__plugin_hal_hal-mcp__assign_task_to_sprint(
  workspace_slug=<workspace d'origine de la tâche>,
  task_id=<id>,
  sprint_id=<sprint_id de ce workspace, résolu en 6b>
)
```

### 6d. Créer les nouvelles tâches

Router chaque nouvelle tâche vers le workspace qui la porte, jamais vers un slug figé. Les offres LinkedIn 🔥 et relances jobsearch vont dans le workspace **dont les `allowed_tags` contiennent `jobsearch`** ; les autres nouvelles tâches vont dans le workspace concerné. N'utiliser que des tags présents dans les `allowed_tags` de ce workspace.

```
mcp__plugin_hal_hal-mcp__create_task(
  workspace_slug=<workspace de destination>,
  title="[titre]",
  sprint_id=<sprint_id de ce workspace>,
  tags=[<un tag présent dans allowed_tags du workspace de destination>],
  due_date="[YYYY-MM-DD]",
  priority="high"|"medium"
)
```

### 6e. Confirmer

```
✅ Sprint créé.
- <name du workspace> Sprint [N] : [X] tâches reportées + [Y] nouvelles
  (une ligne par workspace retenu)
- Blocs job search : [X]h planifiées
- Prochain bloc : lundi [date] 11h00–13h00

Bonne semaine.
```
