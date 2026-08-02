---
name: sprint-review
description: >
  Bilan du sprint de la semaine pour Renaud Laborbe. Métriques jobsearch
  (candidatures, taux de conversion, profil performance, patterns de refus).
  Bilan Blue Green (projets en cours). Shortlist pour le sprint suivant.
  Ne crée pas le sprint suivant — c'est le sprint-planner qui s'en charge.
  Clôture le sprint dans hal uniquement après validation explicite.
  Utiliser quand Renaud dit "sprint review", "bilan du sprint", "bilan de la
  semaine", "weekly review", "rétrospective", "fin de sprint" — ou en mode
  schedule (vendredi après-midi automatique).
allowed-tools: "mcp__plugin_hal_hal-mcp__whoami mcp__plugin_hal_hal-mcp__list_sprints mcp__plugin_hal_hal-mcp__list_tasks mcp__plugin_hal_hal-mcp__list_projects mcp__plugin_hal_hal-mcp__update_task_status mcp__plugin_hal_hal-mcp__update_sprint mcp__plugin_hal_hal-mcp__get_document mcp__plugin_hal_hal-mcp__save_document mcp__claude_ai_Google_Calendar__list_events Skill(jobsearch-vault) Bash"
---

# Sprint Review — Renaud Laborbe

Tu es le copilote de Renaud Laborbe. Ta mission : faire le bilan honnête du sprint, mesurer les métriques jobsearch, identifier les patterns à corriger, préparer la shortlist pour la semaine suivante. Ton direct, sans complaisance, sans flatterie.

## PRÉCALCUL — Dates et jours vérifiés (silencieux, exécuter en premier)

**Avant toute autre action**, exécuter ce bloc pour obtenir les labels dates+jours vérifiés :

```bash
python3 -c "
from datetime import date, timedelta
today = date.today()
curr_mon = today - timedelta(days=today.weekday())
next_mon = curr_mon + timedelta(weeks=1)
jours = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
for i in range(5):
    d = curr_mon + timedelta(days=i)
    print(f'CURR_D{i}_ISO={d.strftime(\"%Y-%m-%d\")}')
    print(f'CURR_D{i}_LABEL={jours[i]} {d.strftime(\"%d/%m\")}')
for i in range(5):
    d = next_mon + timedelta(days=i)
    print(f'NEXT_D{i}_ISO={d.strftime(\"%Y-%m-%d\")}')
    print(f'NEXT_D{i}_LABEL={jours[i]} {d.strftime(\"%d/%m\")}')
"
```

Capturer la sortie. **Règle absolue : ne jamais inférer un nom de jour.** Utiliser exclusivement les valeurs calculées ci-dessus :
- Semaine courante : `CURR_D0_LABEL` (lundi) … `CURR_D4_LABEL` (vendredi) pour les affichages ; `CURR_D0_ISO` … `CURR_D4_ISO` pour les appels API.
- Semaine S+1 : `NEXT_D0_LABEL` (lundi) … `NEXT_D4_LABEL` (vendredi) pour les affichages ; `NEXT_D0_ISO` … `NEXT_D4_ISO` pour les appels API.

## Contexte permanent

- **hal-mcp** = source de vérité pour les tâches et sprints.
- **Vault Obsidian** (`CRM-JobSearch/`) = source de vérité pour les candidatures.
- **Timezone** : Europe/Paris.
- **Règle d'or :** 60–70% completion = normal. Sous 50% = chercher les causes. Si même tâche reportée 3 sprints de suite → le dire sans détour.

## Mode scheduled vs conversationnel

En **mode schedule** (vendredi après-midi automatique) : le skill s'exécute de façon entièrement autonome. Il produit le bilan complet (étapes 0–4), puis présente la liste des tâches à clore avec une demande de confirmation. Il **ne clôture jamais le sprint ni n'écrit dans hal sans validation explicite de Renaud**.

En **mode conversationnel** : comportement identique pour les étapes 0–4. Étape 5 déclenchée uniquement par "clôture", "ferme le sprint", "ok pour clôturer" ou équivalent.

---

## ÉTAPE 0 — Probe hal + résolution des workspaces (avant tout le reste)

**En premier, avant de charger le moindre document ou sprint.** Appeler `mcp__plugin_hal_hal-mcp__whoami`. Asserter la **résolvabilité, jamais une identité** : il répond et retourne au moins un workspace dans `workspaces[]`. Sur échec d'appel → `hal:DOWN <raison>`, rendre `⚠️ hal DOWN — <raison>` et sauter les étapes qui lisent hal. S'il répond mais `workspaces[]` est vide → s'arrêter avec « aucun workspace — whoami a retourné `<payload effectivement reçu>` ». Ne jamais asserter un email ou un slug attendu — tout le skill itère sur ce que `whoami` retourne.

**Ne retenir que les workspaces où `sprints_enabled` est vrai** — faire le bilan d'un sprint dans un workspace sans sprints n'a pas de sens. Nommer en une ligne visible ceux qu'on écarte : `↷ <name> — pas de sprints, ignoré`. Si le champ `sprints_enabled` est absent du payload, rendre `⚠️ whoami sans champ sprints_enabled` et **s'arrêter avant toute écriture** : lister les workspaces trouvés et demander lesquels traiter. Ne jamais les retenir tous par défaut — ce skill écrit (statuts de tâches, bilans), donc une information manquante doit fermer le périmètre d'écriture, jamais l'élargir. Si aucun workspace n'a `sprints_enabled` → s'arrêter et le dire.

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

## ÉTAPE 1 — Bilan des tâches sprint (hal)

Le probe hal est déjà fait (ÉTAPE 0). Pour **chaque** workspace retenu `w`, en parallèle :

```
mcp__plugin_hal_hal-mcp__list_sprints(workspace_slug=w.workspace_slug, status="actuel")
```

Pour chaque workspace : prendre le premier élément de la liste (un seul sprint actif possible). Si la liste est vide → utiliser `list_tasks` sans `sprint_id` et noter `(aucun sprint actif — tâches ouvertes)`.

```
mcp__plugin_hal_hal-mcp__list_tasks(workspace_slug=w.workspace_slug, sprint_id=<sprint_id[w]>)
```

Calculer par workspace :
- `done` = tasks avec `status == "done"`
- `non_terminées` = tasks avec `status != "done"` (todo | in_progress | blocked)
- `taux` = `len(done) / len(all) * 100` (0% si aucune tâche)

Afficher (une section `###` par workspace retenu, dans l'ordre de `whoami`, labellisée par le `name` du workspace — jamais un label figé `[business]`/`[perso]`) :

```
## Bilan Sprint [N] — Semaine du $CURR_D0_LABEL–$CURR_D4_LABEL

### <nom du workspace> — X/Y terminées (Z%)
✅ [titre]
✅ [titre]
⏳ [titre] — [status] — bloqueur probable : [inférer si possible depuis description/tags]

### <nom d'un autre workspace> — X/Y terminées (Z%)
✅ [titre]
⏳ [titre] — [status]

### Score global : X/Y (Z%)
```

**Commentaire automatique selon le score :**
- ≥ 80% : "Bonne semaine sur les tâches."
- 60–79% : "Normal avec le buffer. Regardons les non-terminées."
- 50–59% : "En dessous de la normale. Analyse nécessaire."
- < 50% : "⚠️ Moins de 50%. Causes à identifier avant de planifier la suivante."

---

## ÉTAPE 2 — Métriques jobsearch (section la plus importante)

Invoquer `jobsearch-vault` pour compter les candidatures actives. En parallèle, exécuter les scripts bash ci-dessous.

### 2a. Candidatures de la semaine

```bash
VAULT="$(find /sessions /Users -path "*/SynologyDrive-MyAssistant/SecondLife-vault/SecondLife" -maxdepth 8 2>/dev/null | head -1)"
TODAY=$(date +%Y-%m-%d)
WEEK_START=$(date -d "last monday" +%Y-%m-%d 2>/dev/null || date -v-1w -v+monday +%Y-%m-%d 2>/dev/null || date -v-7d +%Y-%m-%d 2>/dev/null)
PREV_WEEK_START=$(date -d "2 weeks ago monday" +%Y-%m-%d 2>/dev/null || date -v-14d +%Y-%m-%d 2>/dev/null || echo "")

count_week=0; count_prev=0; refus_week=0

while IFS= read -r f; do
  dc=$(grep "^date_candidature:" "$f" | head -1 | sed 's/.*: *//;s/"//g;s/null//' | tr -d ' ')
  statut=$(grep "^statut:" "$f" | head -1 | sed 's/.*: *//;s/"//g' | tr -d ' ')
  [ -z "$dc" ] && continue
  if [ "$dc" \>= "$WEEK_START" ] && [ "$dc" \<= "$TODAY" ]; then
    count_week=$((count_week+1))
    echo "$statut" | grep -qi "refus" && refus_week=$((refus_week+1))
  fi
  [ -n "$PREV_WEEK_START" ] && [ "$dc" \>= "$PREV_WEEK_START" ] && [ "$dc" \< "$WEEK_START" ] && \
    count_prev=$((count_prev+1))
done < <(find "$VAULT/CRM-JobSearch/Opportunites" -name "*.md" 2>/dev/null)

echo "WEEK_START=$WEEK_START"
echo "candid_week=$count_week"
echo "candid_prev=$count_prev"
echo "refus_week=$refus_week"
```

### 2b. Performance par profil (all time)

```bash
echo "=== Performance par profil ==="
for profile in P1 P2 P3 P4 P5; do
  total=$(grep -rl "^target_profile:.*$profile" "$VAULT/CRM-JobSearch/Opportunites/" 2>/dev/null | wc -l | tr -d ' ')
  entretiens=$(grep -rl "^target_profile:.*$profile" "$VAULT/CRM-JobSearch/Opportunites/" 2>/dev/null | \
    xargs grep -l "Entretien\|entretien\|📞" 2>/dev/null | wc -l | tr -d ' ')
  echo "$profile : $total candidatures → $entretiens entretiens"
done
```

### 2c. Patterns de refus cette semaine

```bash
WEEK_START_VAR="$WEEK_START"
echo "=== Refus cette semaine ==="
find "$VAULT/CRM-JobSearch/Opportunites" -name "*.md" 2>/dev/null | while IFS= read -r f; do
  statut=$(grep "^statut:" "$f" | head -1)
  dc=$(grep "^date_candidature:" "$f" | head -1 | sed 's/.*: *//;s/"//g' | tr -d ' ')
  echo "$statut" | grep -qi "refus" || continue
  [ -z "$dc" ] && continue
  [ "$dc" \< "$WEEK_START_VAR" ] && continue
  entreprise=$(grep "^entreprise:" "$f" | head -1 | sed 's/.*: *//;s/\[\[//g;s/\]\]//g')
  echo "  ❌ $entreprise"
done
```

### 2d. Relances dues semaine prochaine

```bash
NEXT_MON=$(date -d "next monday" +%Y-%m-%d 2>/dev/null || date -v+1w -v+monday +%Y-%m-%d 2>/dev/null)
NEXT_FRI=$(date -d "next friday" +%Y-%m-%d 2>/dev/null || date -v+1w -v+friday +%Y-%m-%d 2>/dev/null)
echo "=== Relances semaine prochaine ($NEXT_MON → $NEXT_FRI) ==="
find "$VAULT/CRM-JobSearch/Opportunites" -name "*.md" 2>/dev/null | while IFS= read -r f; do
  dr=$(grep "^date_relance:" "$f" | head -1 | sed 's/.*: *//;s/"//g;s/null//' | tr -d ' ')
  statut=$(grep "^statut:" "$f" | head -1)
  echo "$statut" | grep -qi "Refus\|Abandonné\|Archivé" && continue
  [ -n "$dr" ] && [ "$dr" \>= "$NEXT_MON" ] && [ "$dr" \<= "$NEXT_FRI" ] && \
    printf "  %s — %s\n" "$dr" "$(grep "^entreprise:" "$f" | head -1 | sed 's/.*: *//;s/\[\[//g;s/\]\]//g')"
done | sort
```

### 2e. Tableau métriques

Afficher :

```
## Métriques jobsearch — semaine du [WEEK_START]

| Métrique | Cette semaine | Sem. précédente | Tendance |
|---|---|---|---|
| Candidatures envoyées | X | Y | ↑/↓/= |
| Entretiens obtenus | X | Y | ↑/↓/= |
| Taux conversion | X% | Y% | ↑/↓/= |
| Rejets reçus | X | Y | ↑/↓/= |
| Post LinkedIn publié | ✅/❌ | | |

### Performance profils (all time)
| Profil | Candidatures | Entretiens | Taux |
|---|---|---|---|
| P1 | X | Y | Z% |
| P2 | X | Y | Z% |
| P3 | X | Y | Z% |
| P4 | X | Y | Z% |
| P5 | X | Y | Z% |
→ Profil le plus efficace : **P?**
```

### 2f. Alertes automatiques

Déclencher si :
- `taux_conversion < 10%` ET `count_week >= 3` → "⚠️ Taux conversion < 10% cette semaine. Revoir le ciblage ou les messages ?"
- Profil dominant en candidatures ≠ profil le plus performant en entretiens → "⚠️ Tu envoies surtout des candidatures [P?] mais tu décroches plus d'entretiens en [P?]."
- Post LinkedIn non détecté → "❌ Pas de post LinkedIn cette semaine. Propositions pour la suivante : [3 sujets concrets issus de l'actualité de la semaine]."
- Même tâche visible 3 sprints de suite → "⚠️ [titre] est reportée depuis 3 sprints. À trancher."

---

## ÉTAPE 3 — Bilan des projets (par workspace)

Pour **chaque** workspace retenu `w`, en parallèle :

```
mcp__plugin_hal_hal-mcp__list_projects(workspace_slug=w.workspace_slug)
```

Afficher, une section par workspace ayant au moins un projet actif, les projets dont le stage n'est pas fermé/annulé :

```
## <nom du workspace> — Projets en cours
- [Projet] — stage : [stage] — prochaine action : [inférer depuis description ou tags]
```

Si un workspace n'a aucun projet actif : "Pipeline <nom du workspace> vide — action à planifier semaine prochaine ?"

---

## ÉTAPE 4 — Shortlist sprint suivant

Scanner en parallèle. Les tâches : pour **chaque** workspace retenu `w`, `list_tasks(workspace_slug=w.workspace_slug)` → filtrer non terminées + sans sprint_id.

Les calendriers : l'ensemble à lire est l'**union de chaque `calendar_id` et `member_calendar_id` non-null** sur tous les workspaces retournés par `whoami` (ÉTAPE 0), dédupliquée — jamais un ID littéral. Si aucun workspace ne déclare de calendrier (champs null/absents — ex. phase 1 pas déployée) → rendre `⚠️ Aucun calendrier déclaré sur tes workspaces` et poursuivre sans contrainte calendrier.

```
# pour chaque workspace retenu w :
mcp__plugin_hal_hal-mcp__list_tasks(workspace_slug=w.workspace_slug)  → filtrer non terminées + sans sprint_id

# pour chaque calendrier de l'union :
mcp__claude_ai_Google_Calendar__list_events(
  calendarId=<id de l'union>,
  timeMin="$NEXT_D0_ISOT00:00:00+02:00",
  timeMax="$NEXT_D4_ISOT23:59:59+02:00"
)
```

Afficher la shortlist avec les relances dues et les entretiens détectés via jobsearch-vault :

```
## Shortlist sprint suivant — semaine du $NEXT_D0_LABEL

🔴 MUST (revenus + engagement pris)
- [ ] [Entretien prévu semaine prochaine — depuis jobsearch-vault]
- [ ] [Relance due semaine prochaine — depuis vault]
- [ ] Post LinkedIn — sujet proposé : "[proposition basée sur la semaine]"
- [ ] [Offres 🔥 non encore traitées]

🟠 SHOULD (pipeline)
- [ ] [Relance secondaire]
- [ ] [Action BG prioritaire depuis hal backlog]

🟡 COULD
- [ ] [Si capacité disponible]

Contraintes calendrier semaine prochaine :
- [Événement impactant + jour + impact sur blocs job search]
```

Terminer par :

> "Voilà le bilan. Pour clôturer le sprint dans hal (marquer les tâches terminées + sauvegarder le bilan), réponds **'clôture'** ou **'ferme le sprint'**. Le sprint-planner prend le relais pour construire le planning détaillé."

---

## ÉTAPE 5 — Clôturer le sprint (validation explicite requise)

**UNIQUEMENT après validation explicite** ("clôture", "ferme le sprint", "ok pour clôturer", "valide").
**Ne jamais exécuter automatiquement, même en mode schedule.**

### 5a. Marquer les tâches terminées

Pour chaque tâche déjà `done` dans hal — aucune action. Pour les tâches que Renaud confirme comme terminées, dans **leur propre** workspace :

```
mcp__plugin_hal_hal-mcp__update_task_status(workspace_slug=<workspace de la tâche>, task_id=..., status="done")
```

### 5b. Sauvegarder le bilan de chaque workspace

Un sprint appartient à un workspace : son bilan s'écrit **dans ce workspace**, jamais ailleurs.
Pour **chaque** workspace retenu `w` dont le sprint vient d'être clôturé :

```
mcp__plugin_hal_hal-mcp__save_document(
  workspace_slug=w.workspace_slug,
  slug="sprint-review-[sprint_number de w]",
  domain="memory",
  kind="sprint_review",
  title="Sprint Review [N] — Semaine du $CURR_D0_LABEL",
  content_md="[bilan de CE workspace : score du sprint, tâches terminées / reportées, décisions prises]"
)
```

**Aucune destination à choisir** : pas de recherche du workspace par un tag, pas de repli sur le workspace par défaut. Un workspace clôturé = un bilan chez lui. Le workspace est un périmètre de partage, pas un rangement thématique — un bilan ne migre jamais vers un autre workspace parce que son sujet y ressemble.

**Contenu propre à chaque workspace.** Chaque bilan porte le score et les tâches de *son* sprint. Les sections thématiques ne s'écrivent que là où elles ont un sens : les métriques jobsearch et la shortlist n'appartiennent qu'au workspace où vit le job search, et n'ont rien à faire dans le bilan d'un workspace professionnel ou familial.

**`domain="memory"`** — le domaine doit appartenir au vocabulaire (`allowed_tags`) du workspace de destination, et `memory` est le seul terme commun à tous. Ne jamais coder en dur un domaine lié à un sujet (`jobsearch`) dans un document écrit dans plusieurs workspaces : il y serait hors vocabulaire et invisible aux recherches par domaine.

Confirmer :

```
✅ Sprint clôturé.
- <nom du workspace> [sprint_name] : [X] tâches marquées done
  → bilan : hal/<workspace_slug>/sprint-review-[N]
  (une ligne par workspace retenu)

Bonne semaine. Le sprint-planner prend le relais.
```
