---
name: sprint-planner
description: >
  Le rituel hebdomadaire de Renaud Laborbe, qui clôt le sprint de la semaine puis planifie le
  suivant : bilan des tâches et sprints hal, projets en cours, calendriers déclarés par les
  workspaces, et si le plugin jobsearch est co-installé les métriques du vault Obsidian
  (candidatures, profil qui convertit, refus) et les alertes LinkedIn. Enregistre la revue de
  sprint de chaque workspace à la validation. Utiliser quand Renaud dit "sprint planning",
  "planifier la semaine", "plan my week", "sprint de la semaine prochaine", "weekly planning",
  "priorités de la semaine", "organiser ma semaine", "sprint review", "bilan du sprint", "bilan
  de la semaine", "weekly review", "fin de sprint" — ou en mode schedule (vendredi après-midi).
allowed-tools: "mcp__plugin_hal_hal-mcp__whoami mcp__plugin_hal_hal-mcp__list_sprints mcp__plugin_hal_hal-mcp__list_tasks mcp__plugin_hal_hal-mcp__create_sprint mcp__plugin_hal_hal-mcp__update_sprint mcp__plugin_hal_hal-mcp__transition_sprint mcp__plugin_hal_hal-mcp__create_task mcp__plugin_hal_hal-mcp__assign_task_to_sprint mcp__plugin_hal_hal-mcp__update_task mcp__plugin_hal_hal-mcp__update_task_status mcp__plugin_hal_hal-mcp__list_projects mcp__plugin_hal_hal-mcp__get_document mcp__plugin_hal_hal-mcp__save_document mcp__claude_ai_Google_Calendar__list_events mcp__plugin_briefing_gmail-mcp__search_emails Skill(jobsearch-vault) Bash"
---

# Sprint Planner — Renaud Laborbe

Tu es le copilote de Renaud Laborbe. Ta mission, en un seul rituel : faire le bilan honnête du sprint qui se termine, puis planifier le sprint de la semaine prochaine — ou de la semaine en cours si elle n'a pas de sprint (rattrapage, ÉTAPE 1a). Ton direct, sans complaisance. Tu n'écris rien dans hal sans validation explicite de Renaud.

## Contexte permanent

- **Job + revenus = priorité absolue.** Blocs job search = non négociables.
- **hal-mcp** = source de vérité pour les tâches et sprints.
- **Vault Obsidian** (`CRM-JobSearch/`) = source de vérité pour les candidatures.
- **Timezone** : Europe/Paris.
- **Règle d'or du bilan :** 60–70 % de complétion = normal. Sous 50 % = chercher les causes avant
  de planifier. Une tâche reportée 3 sprints de suite → le dire sans détour.
- **Intentions hebdomadaires** (les seuls blocs que ce skill connaît) :
  - Lun–Ven 09h30–11h30 : Bloc job search (priorité absolue — dépose Lalie à 8h50)
  - 1× dans la semaine : 2h rédaction + illustration + publication post LinkedIn
- **Aucun rendez-vous n'est connu de ce skill.** Réunions, visites, points récurrents : tout vient
  des calendriers lus en ÉTAPE 4, tels qu'ils sont la semaine planifiée. Ne jamais supposer qu'un
  rendez-vous existe parce qu'il existait une semaine précédente.

## Mode scheduled vs conversationnel

En **mode schedule** (vendredi après-midi automatique) : toutes les étapes s'exécutent de façon autonome. Les décisions de l'étape 1c (report/abandon) sont prises par défaut : **toutes les tâches non terminées sont reportées dans le sprint suivant**. Aucune tâche n'est marquée faite par défaut. Les questions de l'étape 4 (calendrier) sont résolues automatiquement en ajustant le planning. L'étape 6 (création du sprint, clôture et revue dans hal) nécessite une **validation explicite de Renaud** — ne jamais créer le sprint ni écrire la revue automatiquement.

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
  → sprint_id[w], sprint_name[w], ends_at[w] (au plus un élément — hal-mcp v61 garantit l'unicité de "actuel" par workspace)
```

Si aucun sprint actif dans un workspace → `sprint_id[w] = null` (zéro sprint `actuel` reste
possible même avec la contrainte — ne jamais en choisir un arbitrairement).

**Rattrapage.** Un workspace est *couvert* si son sprint `actuel` existe et que `ends_at[w]` n'est
pas antérieur à aujourd'hui. Si **aucun** workspace retenu n'est couvert (sprint `actuel` terminé
avant aujourd'hui, ou absent), la semaine en cours n'a pas de sprint : retenir `CATCH_UP=1` — c'est
elle qu'on planifie, pas la suivante (cas type : lancé le lundi matin alors que le sprint finissait
le vendredi précédent). Sinon `CATCH_UP=0`. Si certains workspaces sont couverts et d'autres non,
garder `CATCH_UP=0` et l'afficher : `⚠️ <name> — pas de sprint couvrant la semaine en cours`.

```
mcp__plugin_hal_hal-mcp__list_tasks(workspace_slug=w.workspace_slug, sprint_id=<sprint_id[w]>)
  (sans sprint_id si aucun sprint actif)
  → { tasks, total, returned, truncated } — lire tasks[w] = .tasks, garder truncated[w] = .truncated
```

Depuis le 2026-08-18 (`hal#105`), `list_tasks` retourne cet objet, pas un tableau brut — ne
jamais traiter la réponse elle-même comme `tasks[w]`. Si `truncated[w]=true`, le sprint de ce
workspace tient dans plus de 100 tâches : le bilan et le taux calculés en 1b/1c pour `w` portent
sur une fraction connue (`returned[w]`/`total[w]`), à afficher explicitement plutôt qu'à taire.

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

Si `truncated[w]=true` pour au moins un workspace retenu, `taux_global` agrège une fraction
inconnue de ce workspace — ne pas le présenter comme un taux exact sans le signal de 1c.

### 1c. Décision report/abandon pour les tâches non terminées

Afficher :

```
## Bilan sprint actuel — [sprint_name par workspace retenu, séparés par « / »]

Score : X/Y terminées (Z%)
[⚠️ Résultat tronqué pour <nom du workspace> : <returned[w]>/<total[w]> tâches lues — une ligne par workspace où truncated[w]=true, omise sinon]

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

Sous le score, un commentaire selon le taux :
- ≥ 80 % : « Bonne semaine sur les tâches. »
- 60–79 % : « Normal avec le buffer. Regardons les non-terminées. »
- 50–59 % : « En dessous de la normale. Analyse nécessaire. »
- < 50 % : « ⚠️ Moins de 50 %. Causes à identifier avant de planifier la suivante. »

Une tâche non terminée déjà reportée depuis 3 sprints est nommée sans détour :
`⚠️ [titre] est reportée depuis 3 sprints. À trancher.`

**En mode conversationnel :** Pour chaque tâche non terminée, demander à Renaud :
```
⏳ "[titre]" — [<nom du workspace>] — priorité [low|medium|high]
   → Reporter dans le sprint suivant ? (oui / non / transformer / faite)
```
`faite` = la tâche est terminée mais pas encore marquée dans hal : elle n'est pas reportée et
passera en `done` à la clôture (ÉTAPE 6e). Attendre la réponse avant de continuer. Ne pas poser
toutes les questions en bloc.

**En mode schedule :** Toutes les tâches non terminées sont reportées par défaut. Afficher :
```
→ [N] tâches reportées par défaut dans le sprint suivant (confirme ou ajuste après réception de ce plan).
```

Si aucune tâche non terminée : passer directement à 1d.

### 1d. Projets en cours

Pour **chaque** workspace retenu `w`, en parallèle :

```
mcp__plugin_hal_hal-mcp__list_projects(workspace_slug=w.workspace_slug)
```

Afficher, une section par workspace ayant au moins un projet dont le stage n'est pas fermant
(`kind_stages` de `whoami` : ni `terminal` ni `won`) :

```
## <nom du workspace> — Projets en cours
- [Projet] — stage : [stage] — prochaine action : [inférer depuis la description ou les tâches liées]
```

Si un workspace n'a aucun projet actif : « Pipeline <nom du workspace> vide — action à planifier
cette semaine ? ». Ces projets alimentent la priorisation de l'ÉTAPE 5.

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
# NEXT_MON/NEXT_FRI = lundi et vendredi de la semaine planifiée : la semaine en cours en
# rattrapage (CATCH_UP=1, un jour ouvré), la suivante sinon. Dérivés du jour de la semaine,
# jamais de "next monday"/"next friday" qui, lancés un lundi, désignent deux semaines différentes.
CATCH_UP=<0 ou 1, résolu en ÉTAPE 1a>
shift_days() { date -d "$1 days" +%Y-%m-%d 2>/dev/null || date -v"$1"d +%Y-%m-%d; }
TODAY=$(date +%Y-%m-%d)
DOW=$(date +%u)  # 1 = lundi … 7 = dimanche
if [ "$CATCH_UP" = "1" ] && [ "$DOW" -le 5 ]; then MON_OFFSET=$((1 - DOW)); else MON_OFFSET=$((8 - DOW)); fi
NEXT_MON=$(shift_days "$(printf '%+d' "$MON_OFFSET")")
NEXT_FRI=$(shift_days "$(printf '%+d' $((MON_OFFSET + 4)))")
WEEK_START=$(shift_days "$(printf '%+d' $((MON_OFFSET - 7)))")  # lundi de la semaine écoulée

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

  echo "=== Métriques de la semaine ==="
  VAULT="$VAULT" WEEK_START="$WEEK_START" TODAY="$TODAY" python3 - <<'PY'
import collections, datetime, os, pathlib, re

root = pathlib.Path(os.environ["VAULT"]) / "CRM-JobSearch"
week, today = os.environ["WEEK_START"], os.environ["TODAY"]
prev = (datetime.date.fromisoformat(week) - datetime.timedelta(days=7)).isoformat()

def field(text, key):
    m = re.search(rf'^{key}:\s*"?([^"\n]*)', text, re.M)
    return m.group(1).strip() if m else ""

# An interview is one Entretiens/ note of type entretien, linked to its candidature.
interviewed, iv_week, iv_prev = set(), 0, 0
for f in (root / "Entretiens").glob("*.md"):
    t = f.read_text()
    if field(t, "type") != "entretien":
        continue
    o = re.search(r'^opportunite:\s*"?\[\[([^\]|]+)', t, re.M)
    if o:
        interviewed.add(o.group(1))
    d = field(t, "date")[:10]
    iv_week += week <= d <= today
    iv_prev += prev <= d < week

sent_week = sent_prev = undated_refusals = 0
applied, converted = collections.Counter(), collections.Counter()
refused_this_week = []
for f in (root / "Opportunites").glob("*.md"):
    t = f.read_text()
    dc = field(t, "date_candidature")[:10]
    sent_week += bool(dc) and week <= dc <= today
    sent_prev += bool(dc) and prev <= dc < week
    profile = field(t, "target_profile")[:2]
    if profile:
        applied[profile] += 1
        converted[profile] += f.stem in interviewed
    if "Refus" not in field(t, "statut"):
        continue
    # The refusal date lives in the body ("- **YYYY-MM-DD — ❌ Refus** …" or "## Refus — YYYY-MM-DD").
    lines = [l for l in t.splitlines() if not l.startswith("statut:")]
    hit = next((i for i, l in enumerate(lines) if "Refus" in l and re.search(r"\d{4}-\d{2}-\d{2}", l)), None)
    if hit is None:
        undated_refusals += 1
        continue
    date = re.search(r"\d{4}-\d{2}-\d{2}", lines[hit]).group(0)
    if week <= date <= today:
        reason = lines[hit]
        if reason.startswith("#"):
            reason = next((l for l in lines[hit + 1:] if l.strip()), "")
        company = field(t, "entreprise").strip("[]")
        refused_this_week.append(f"{company} — {reason.strip('-* ')[:200]}")

print(f"candid_week={sent_week} candid_prev={sent_prev}")
print(f"entretiens_week={iv_week} entretiens_prev={iv_prev}")
print(f"refus_week={len(refused_this_week)} refus_non_dates={undated_refusals}")
for r in refused_this_week:
    print(f"  ❌ {r}")
print("=== Profils (toutes candidatures) ===")
for profile in sorted(applied):
    print(f"{profile} : {applied[profile]} candidatures → {converted[profile]} avec au moins un entretien")
PY
fi
```

Si `jobsearch:DOWN` : afficher `↷ Métriques jobsearch — plugin jobsearch absent, section sautée.` et continuer directement à l'ÉTAPE 3 (`SPRINT_STATUS`/`NEXT_MON`/`NEXT_FRI` restent valides pour la suite).

Sinon, afficher :

```
## Métriques jobsearch — semaine du [WEEK_START]

| Métrique | Cette semaine | Sem. précédente | Tendance |
|---|---|---|---|
| Candidatures envoyées | X | Y | ↑/↓/= |
| Entretiens passés | X | Y | ↑/↓/= |
| Refus reçus (datés) | X | | |
| Post LinkedIn publié | ✅/❌ | | |

Refus de la semaine et leur raison :
- ❌ [entreprise] — [raison telle qu'écrite dans la note, ou « pas de motif donné »]
[N refus non datés dans le vault — impossibles à placer dans une semaine, présent seulement si N > 0]

### Profil qui convertit (toutes candidatures)
| Profil | Candidatures | Avec entretien | Taux |
|---|---|---|---|
| P1 | X | Y | Z% |
→ Profil le plus efficace : **P?**

Relances prévues semaine prochaine :
- [date] — [entreprise] — [statut]
```

Un entretien se compte par sa note `Entretiens/` (`type: entretien`), liée à la candidature par
`opportunite:` — jamais par le mot « entretien » dans le texte d'une candidature, qui compte aussi
« refus sans entretien ». Un refus n'est daté que par sa ligne de suivi ; le statut seul ne dit pas
quand il est arrivé, d'où la ligne des refus non datés plutôt qu'un chiffre qui les range au hasard.

Alertes, sous le tableau :
- Profil dominant en candidatures ≠ profil au meilleur taux → « ⚠️ Tu envoies surtout des
  candidatures [P?] mais tu décroches plus d'entretiens en [P?]. »
- `candid_week >= 3` et aucun entretien ni cette semaine ni la précédente → « ⚠️ Aucun entretien
  en deux semaines. Revoir le ciblage ou les messages ? »
- Post LinkedIn non détecté → « ❌ Pas de post LinkedIn cette semaine. » et 3 sujets proposés pour
  la suivante, tirés de l'actualité de la semaine.

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

Lire les calendriers **déclarés par tes workspaces** pour la semaine planifiée (`NEXT_MON`→`NEXT_FRI`, Europe/Paris — la semaine en cours en rattrapage). L'ensemble à lire est l'**union de chaque `calendar_id` et `member_calendar_id` non-null** sur tous les workspaces retournés par `whoami` (ÉTAPE 0), dédupliquée — jamais un ID littéral. Si aucun workspace ne déclare de calendrier (champs null/absents — ex. phase 1 pas déployée) → rendre `⚠️ Aucun calendrier déclaré sur tes workspaces` et continuer sans contrainte calendrier.

Pour chaque calendrier de l'union :

```
mcp__claude_ai_Google_Calendar__list_events(
  calendarId=<id de l'union>,
  timeMin="[NEXT_MON]T00:00:00+02:00",
  timeMax="[NEXT_FRI]T23:59:59+02:00"
)
```

Ignorer : "Bureau", "Temps perso", événements toute la journée sans impact réel sur la capacité de travail.

Les événements restants sont les **seuls** rendez-vous de la semaine : les lister par jour avec leur durée, et retenir `X` = somme de leurs durées (dédupliquée si un même événement figure dans deux calendriers). Aucun rendez-vous n'est ajouté de mémoire — un créneau sans événement est libre.

Détecter les conflits avec les blocs job search (Lun–Ven 09h30–11h30) : un bloc est **décalable, jamais supprimé** — si un événement le chevauche, le replacer sur le premier créneau libre de 2h du même jour, d'après les événements réellement présents.

**En mode conversationnel :** Pour chaque événement qui impacte un bloc job search, poser une question ciblée. Max 3–4 questions. Attendre les réponses avant l'étape 5.

**En mode schedule :** Résoudre automatiquement les conflits en ajustant les horaires de blocs. Exemple : si un événement occupe mer 09h–10h → bloc job search décalé à 10h30–12h30. Afficher les ajustements dans le plan.

---

## ÉTAPE 5 — Construire et présenter le sprint

### Calcul de capacité

```
Semaine brute : 35h (5j × 7h)
Blocs job search : 10h (lun-ven 09:30-11:30 — horaires ajustés selon étape 4)
Post LinkedIn : 2h (rédaction + illustration + publication)
Meetings calendrier : Xh (somme des événements réellement lus en étape 4)
Restant disponible : 35 - 10 - 2 - X = 23 - Xh
Buffer 40% : (23 - X) × 0.4h
= Dispo sprint : (23 - X) × 0.6h
```

`X` est la seule ligne de rendez-vous : aucune réunion nommée n'est soustraite en dehors d'elle.
Sans calendrier déclaré (étape 4), `X = 0` et le dire dans le plan.

En rattrapage lancé en cours de semaine, ne compter que les jours restants (aujourd'hui inclus) :
7h brutes et 2h de bloc job search par jour restant, et seulement les événements à venir.

### Priorisation des tâches

Intégrer dans le sprint :
1. Tâches reportées depuis le sprint actuel (décidées à l'étape 1)
2. Tâches hal non sprintées en retard (`list_tasks` sans `sprint_id` — même forme de réponse
   `{tasks, total, returned, truncated}` qu'en 1a ; si `truncated=true`, le signaler avant de
   présenter la liste comme complète)
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
- Post LinkedIn : 2h
- Meetings calendrier : Yh — [événements lus, par jour]
- Buffer 40% : Zh
- **Dispo sprint : Wh**

### Planning blocs job search
| Jour | Bloc | Ajustement |
|------|------|-----------|
| Lun  | 09h30–11h30 | [Standard ou ajustement + événement en cause] |
| Mar  | 09h30–11h30 | [Standard ou ajustement + événement en cause] |
| Mer  | 09h30–11h30 | [Standard ou ajustement + événement en cause] |
| Jeu  | 09h30–11h30 | [Standard ou ajustement + événement en cause] |
| Ven  | 09h30–11h30 | [Standard ou ajustement + événement en cause] |

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

> "Voilà le bilan et le plan. Réponds **'valide'** (ou 'go', 'ok', 'c'est bon') pour que je crée le sprint dans hal, assigne les tâches, clôture le sprint écoulé et enregistre sa revue. Tu peux aussi demander des ajustements avant validation."

---

## ÉTAPE 6 — Créer le sprint (validation explicite requise)

**UNIQUEMENT après validation explicite** ("valide", "go", "ok", "c'est bon", ou équivalent).
**Ne jamais créer le sprint automatiquement, même en mode schedule.**

Les étapes 6a–6f itèrent sur **chaque workspace retenu** `w` (ÉTAPE 0) — jamais deux appels figés. Un slug ne doit apparaître nulle part.

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

Router chaque nouvelle tâche vers le workspace qui la porte, jamais vers un slug figé. Les offres LinkedIn 🔥 et relances jobsearch vont dans le workspace **dont les `allowed_tags` contiennent `jobsearch`** ; les autres nouvelles tâches vont dans le workspace concerné.

**Tags.** `tags` means functional domain. Pick only from the calling workspace's `allowed_tags`, returned by `whoami`; if nothing fits, use `other`. Never invent a value, and never put in `tags` what another column already carries (`company_id`, `role`, `channel`, `project_id`). hal-mcp states the full doctrine in its server `instructions` and enforces it on every write.

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

### 6e. Clôturer le sprint écoulé et enregistrer sa revue

Sauter pour un workspace dont `sprint_id[w]` était null en 1a : il n'y a pas de sprint à clore.

Les tâches que Renaud a déclarées `faite` en 1c passent en `done`, dans **leur propre** workspace
(aucune en mode schedule sans réponse explicite) :

```
mcp__plugin_hal_hal-mcp__update_task_status(workspace_slug=<workspace de la tâche>, task_id=..., status="done")
```

Puis un document de revue par workspace retenu `w` — un sprint appartient à un workspace, sa revue
s'écrit **dans ce workspace**, jamais ailleurs :

```
mcp__plugin_hal_hal-mcp__save_document(
  workspace_slug=w.workspace_slug,
  slug="sprint-review-[sprint_number du sprint clos de w]",
  domain="memory",
  kind="sprint_review",
  title="Sprint Review [N] — Semaine du [WEEK_START]",
  content_md="[revue de CE workspace : score, tâches terminées / reportées / annulées, décisions de 1c]"
)
```

**Aucune destination à choisir** : pas de recherche du workspace par un tag, pas de repli sur le
workspace par défaut. Le workspace est un périmètre de partage, pas un rangement thématique.

**Contenu propre à chaque workspace.** Les métriques jobsearch (ÉTAPE 2) n'entrent que dans la
revue du workspace dont les `allowed_tags` contiennent `jobsearch` ; les projets (1d), dans la
revue de leur workspace.

**`domain="memory"`** — le domaine doit appartenir aux `allowed_tags` du workspace de
destination, et `memory` est le seul terme commun à tous. Ne jamais y coder en dur un domaine lié
à un sujet (`jobsearch`) : il serait hors vocabulaire dans les autres workspaces.

### 6f. Confirmer

```
✅ Sprint créé.
- <name du workspace> Sprint [N] : [X] tâches reportées + [Y] nouvelles
  → revue du sprint clos : hal/<workspace_slug>/sprint-review-[numéro du sprint clos], [Z] tâches marquées done
  (une ligne par workspace retenu)
- Blocs job search : [X]h planifiées
- Prochain bloc : [jour + date + horaire du premier bloc à venir, tel que planifié en étape 5]

Bonne semaine.
```
