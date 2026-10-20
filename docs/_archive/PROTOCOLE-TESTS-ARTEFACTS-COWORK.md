# Protocole de test — capacités des artefacts Cowork

**Auteur du brief** : session Cowork du 30/07/2026
**Destinataire** : nouvelle session, **locale obligatoirement** (voir §2)
**Objet** : répondre par l'expérience à 5 questions qui conditionnent l'architecture de Command Center, hal et Edifice.

---

## 0. Pourquoi ce document

Une session entière a été passée à sonder la CSP des artefacts Cowork. Les résultats sont solides et ne doivent pas être re-litigés. Mais elle s'est aussi appuyée sur les **descriptions** des artefacts publiés pour conclure que l'affichage photo fonctionnait — alors qu'il n'a **jamais** fonctionné, ni dans `missions-edifice`, ni dans `missions-edifice-lab`, ni dans `edifice-front`.

> **Règle de méthode pour la nouvelle session** : la description d'un artefact décrit une *intention* au moment de la publication. Elle n'est pas une preuve. Seul un test cliqué dans la sidebar fait foi.

---

## 1. Acquis — ne pas retester

Établi par les sondes `csp-probe` et `csp-probe-2` (30/07/2026), et par la lecture du code de `command-center-quotidien`.

### 1.1 Content-Security-Policy effective

```
default-src 'self';
script-src  'self' 'unsafe-inline'
            https://cdn.jsdelivr.net/npm/chart.js@4.5.0/dist/chart.umd.js
            https://cdn.jsdelivr.net/npm/gridjs@5.0.2/dist/gridjs.umd.js
            https://cdn.jsdelivr.net/npm/mermaid@11.15.0/dist/mermaid.min.js;
style-src   'self' 'unsafe-inline' https://cdn.jsdelivr.net/npm/gridjs@5.0.2/dist/theme/mermaid.min.css;
img-src     'self' data:;
font-src    'self' data:;
connect-src 'none';
object-src  'none';
frame-src   'none';
form-action 'none';
base-uri    'self'
```

**Conséquences définitives :**

| Mécanisme | État | Note |
|---|---|---|
| `<img src="https://…">` | ❌ bloqué | `img-src` ne liste que `'self'` et `data:` |
| `fetch()` / XHR / WebSocket / SSE | ❌ bloqué | `connect-src 'none'` |
| `blob:` en `img-src` | ❌ bloqué | testé, violation CSP |
| `<iframe>`, `<object>`, `<embed>` | ❌ bloqué | |
| `window.open()` | ❌ renvoie `null` | popup blocker |
| `<a target="_blank">` | ✅ **fonctionne** | ouvre un vrai onglet navigateur, hors artefact |
| `data:` en `img-src` | ✅ jusqu'à ≥ 10,7 Mo/image, décodage 14 ms | testé sur bruit incompressible |
| `localStorage` | ✅ **fonctionne** | Command Center y mémorise le préfixe hal résolu |
| Chart.js, Grid.js, Mermaid via jsDelivr | ✅ autorisés explicitement | seules dépendances CDN permises |
| Appels MCP (`window.cowork.callMcpTool`) | ✅ | passent par le pont de l'hôte, **pas** par la pile réseau → non concernés par `connect-src` |

### 1.2 Environnement d'exécution

```
location.href    cowork-artifact://local/<artifact-id>/index.html
origin           cowork-artifact://local
isSecureContext  true
window.top === window.self   →  true   (pas d'iframe, pas de sandbox détecté)
```

Un chemin relatif (`./fichier.png`) échoue en **404 sans violation CSP** : le same-origin est autorisé par la politique, mais rien n'est servi à côté de `index.html`. Il n'existe aucun moyen connu d'y déposer un fichier.

### 1.3 Le pont MCP

Le bridge s'appelle **`window.cowork.callMcpTool(name, args)`**.

> ⚠️ La sonde `sonde-edifice-cowork` du 27/07 a conclu « aucun bridge » : elle testait `window.claude`, `window.anthropic`, `window.electronAPI`, `window.webkit`, `window.chrome.webview` — **mais pas `window.cowork`**. Faux négatif. Ne pas repartir de ses conclusions.

Enveloppe de réponse observée (Command Center, outils texte) :

```js
{ content: [ { type: "text", text: "…json…" } ], structuredContent: …, isError: false }
```

Pattern d'accès éprouvé, à réutiliser tel quel :

```js
const HAL_CANDIDATES = ["mcp__7898d523-5bb3-4502-b704-16db78ae0a8c__", "mcp__hal-mcp__"];
// essayer chaque préfixe sur whoami, garder celui qui répond, mémoriser en localStorage
```

Un artefact peut déclarer **plusieurs connecteurs** : Command Center combine Google Calendar et hal-mcp.

### 1.4 Publication — contraintes dures

- `mcp__remote-devices__create_artifact` (session **cloud**) n'accepte que `id`, `file_uuid`, `description`. **Aucun paramètre `mcp_tools`.** Un artefact publié depuis le cloud a une allowlist vide et ne peut appeler aucun outil.
- L'allowlist est **appliquée par l'hôte, par artefact**. Le bloc `<script id="cowork-artifact-meta">` du HTML est un *output* réécrit par la plateforme, pas un input.
- ⛔ **Ne jamais appeler `create_artifact` / `update_artifact` via `mcp__remote-devices__*` sur un artefact existant** : ça écrase la version qui marche. C'est arrivé à `edifice-front` le 28/07.

> **Donc : tous les tests de ce document exigent une session Cowork LOCALE**, avec l'outil de publication local qui accepte la déclaration `mcp_tools`.

---

## 2. Règles de sécurité pour la session de test

1. Session **locale** (desktop, « Run this task » → sur mon ordinateur). Vérifier au démarrage : si des outils `mcp__remote-devices__*` sont présents, c'est une session cloud → **arrêter**.
2. Chaque test = un **nouvel** artefact, id préfixé `t-` (`t-photo`, `t-write`…). Ne jamais réutiliser ni mettre à jour : `edifice-front`, `command-center-quotidien`, `missions-edifice`, `missions-edifice-lab`.
3. Un artefact de test = **un bouton, un appel, un dump brut**. Pas d'UI, pas de logique métier. Ce qu'on veut, c'est la forme exacte de la réponse.
4. Toujours afficher `JSON.stringify(réponse)` tronqué, **jamais** une interprétation. Les conclusions se tirent après, pas dans la page.
5. Relever les UUID de connecteurs **en direct** via `ListConnectors` — ils sont propres à chaque poste. Valeurs observées le 30/07 sur `lepecq-local`, à re-vérifier :
   - hal-mcp → `7898d523-5bb3-4502-b704-16db78ae0a8c`
   - Google Calendar → `6fd5fd1e-2c83-4b88-9e45-6b063ff778ec`

---

## 3. Inventaire des outils disponibles

### 3.1 hal-mcp — 34 outils

Relevé sur le registre de `hal-mcp` v69 (2026-08-29). `list_stages` a été retiré par hal#135 :
les étapes du pipeline arrivent désormais dans `whoami`, champ `kind_stages`.

**Lecture (15)**

| Outil | Domaine |
|---|---|
| `whoami` | identité / workspace — porte aussi `allowed_tags`, `allowed_ecosystems`, `allowed_activity_types`, `kind_stages` |
| `list_projects` · `list_sprints` · `list_tasks` | PM |
| `list_companies` · `list_contacts` · `list_interactions` | CRM |
| `list_documents` · `get_document` · `get_document_file` | documents |
| `list_edifice_missions` · `read_edifice_mission` · `get_mission_context` · `get_mission_with_assets` | Edifice |
| `get_mission_photo` | Edifice — **renvoie un bloc `type:"image"`, cas particulier, voir Q1** |

**Écriture (19)**

| Outil | Domaine |
|---|---|
| `create_project` · `update_project` · `update_project_stage` | PM |
| `create_sprint` · `update_sprint` · `transition_sprint` · `assign_task_to_sprint` | PM |
| `create_task` · `update_task` · `update_task_status` | PM |
| `create_company` · `update_company` · `create_contact` · `update_contact` · `enrich_contact` | CRM |
| `log_interaction` · `update_interaction` | CRM |
| `save_document` | documents |
| `push_mission_context` | Edifice |

> `update_task_status` est le candidat désigné pour Q4 : petit, idempotent, réversible.

### 3.2 Connecteurs compte

**Google Calendar (9)** — `list_calendars`, `list_events`, `get_event`, `search_events`, `suggest_time`, `create_event`, `update_event`, `delete_event`, `respond_to_event`

**Gmail (16)** — `search_threads`, `get_thread`, `get_message`, `list_labels`, `list_drafts`, `create_draft`, `update_draft`, `create_label`, `update_label`, `delete_label`, `label_message`, `unlabel_message`, `label_thread`, `unlabel_thread`, `apply_sensitive_message_label`, `apply_sensitive_thread_label`

**Google Drive (8)** — `search_files`, `list_recent_files`, `get_file_metadata`, `get_file_permissions`, `read_file_content`, `download_file_content`, `create_file`, `copy_file`

> ⚠️ Les artefacts ne peuvent appeler que des connecteurs **de niveau compte**, pas des serveurs MCP locaux ou de projet. hal-mcp est installé comme MCP de plugin (`plugins/hal/.mcp.json`). **À vérifier en premier** : est-il aussi déclaré dans Réglages → Connecteurs ? Si non, c'est peut-être la cause racine de tout, y compris de l'échec photo.

---

## 4. Les tests

### Q1 — Peut-on afficher une photo de visite de chantier ? 🔴 BLOQUANT

**État réel** : l'affichage photo n'a jamais fonctionné. Ni `edifice-front`, ni `missions-edifice`, ni `missions-edifice-lab`.

**Ce qui est déjà écarté** : la CSP n'est pas en cause pour un `data:` (10 Mo passent). Le bucket public/privé n'est pas en cause (aucune image distante ne peut entrer, quoi qu'il arrive).

**Hypothèse principale** : `window.cowork.callMcpTool` **ne transporte pas les blocs de contenu `type:"image"`**. Le seul artefact fonctionnel, Command Center, n'appelle que des outils renvoyant du texte. Le code Edifice fait `content.find(c => c.type === "image")` et lève « n'a renvoyé aucune image » quand il ne trouve rien — ce qui est exactement le symptôme attendu si le pont filtre les blocs image.

**Hypothèses secondaires** : (b) hal-mcp n'est pas un connecteur de niveau compte → aucun appel ne passe ; (c) plafond de taille sur la réponse d'un outil ; (d) timeout.

**Protocole** — artefact `t-photo`, `mcp_tools` = `list_edifice_missions`, `get_mission_context`, `get_mission_photo` (les deux préfixes).

1. Bouton A → `list_edifice_missions {limit:1}`. **Contrôle** : si ça échoue, on est sur l'hypothèse (b), tout le reste est sans objet.
2. Bouton B → `get_mission_context` sur cette mission. Afficher `photos.length` et le premier `photo_id`.
3. Bouton C → `get_mission_photo {photo_id, max_width: 400}`. Afficher **sans interprétation** :
   - `Object.keys(r)`
   - `Array.isArray(r.content)` et `r.content.map(c => c.type)`
   - pour chaque bloc : ses clés, et la longueur de `data`/`text` s'ils existent
   - `JSON.stringify(r).slice(0, 3000)`
   - durée de l'appel
4. Bouton D → même appel avec `max_width: 100`, pour séparer un problème de taille d'un problème de type.

**Critères de décision**

| Observation | Conclusion | Suite |
|---|---|---|
| `content` contient `{type:"image", data, mimeType}` | Le pont transporte l'image. Le bug est dans le rendu ou dans le `Promise.all`. | Corriger le front, cf. §5 |
| `content` ne contient que du texte, ou est vide | **Le pont filtre les blocs image.** | → contournement ci-dessous |
| Rejet / `isError` avec message d'allowlist | Problème de déclaration ou de niveau de connecteur | Traiter hypothèse (b) |
| OK en `max_width:100`, échec en 400 | Plafond de taille | Baisser la résolution, découper |

**Contournement conçu à l'avance** (si le pont filtre les images) : ajouter à hal-mcp un outil **`get_mission_photo_b64`** qui renvoie le même contenu en **bloc texte** — `{"mime":"image/jpeg","b64":"…"}` — que l'artefact reconstitue en `data:` lui-même. Le texte transite, c'est prouvé par Command Center. ~10 lignes de Python côté hal.

**Repli ultime** (si rien ne passe) : pas de photo dans l'artefact. Vignettes remplacées par des cartes cliquables, `<a target="_blank">` vers Supabase — mécanisme validé le 30/07. Le bucket doit alors rester public, ou hal renvoyer une URL signée (une chaîne, pas des octets).

---

### Q2 — L'artefact peut-il se mettre à jour quand la donnée change ?

**Déjà partiellement répondu.** Aucun `setInterval`, aucun abonnement dans Command Center ni dans le lab. Le « refresh » quotidien est le bouton **Reload de l'hôte** : il remonte la page, ce qui rejoue `init()`, ce qui rappelle les outils.

**Reste à établir**

1. Existe-t-il une API d'abonnement ? → l'artefact `cowork-api-probe` (déjà publié, section Q2) inventorie `on*`, `subscribe`, `watch`, `observe` sur les objets injectés. **Coller le bloc « Inventaire brut ».**
2. Un `setInterval` + `callMcpTool` fonctionne-t-il, et **déclenche-t-il un dialogue de permission à chaque tick** ? → artefact `t-poll` : un tick toutes les 20 s sur `whoami`, compteur de succès/échecs, horodatage. Laisser tourner 3 min.
3. La page est-elle suspendue quand la sidebar est masquée ? Le compteur le dira.

**Critère** : si le polling passe sans dialogue répété, un rafraîchissement auto de 30–60 s est viable pour Command Center. Sinon, le bouton Reload de l'hôte reste la réponse — et c'est déjà suffisant pour un usage quotidien.

---

### Q3 — Peut-on appeler un agent (ask AI) depuis l'artefact ?

**Ce qu'on sait** : aucune API de complétion identifiée. `window.cowork` expose `callMcpTool`. `window.claude` / `window.anthropic` sont à re-tester correctement (la sonde du 27/07 est invalide).

**Protocole** : lire le bloc « Inventaire brut » de `cowork-api-probe` — il énumère récursivement les objets injectés avec la signature de chaque fonction. Chercher `complete`, `ask`, `prompt`, `generate`, `sendMessage`, `runAgent`, `invoke`, `chat`, `query`.

**Si rien** — et c'est le pari : l'agent devient un **outil du serveur MCP**. hal-mcp expose `ask(prompt, context)`, appelle le modèle côté serveur, renvoie du texte. L'artefact l'invoque comme n'importe quel autre outil.

C'est architecturalement préférable de toute façon : la clé API et le prompt système ne descendent jamais dans la page, le raisonnement est journalisable côté serveur, et le même outil sert à Cowork, au CLI et à openclaw.

**À chiffrer dans la session** : coût d'un tel outil dans hal-mcp, et latence (l'artefact doit gérer une attente de plusieurs secondes sans figer l'UI).

---

### Q4 — Valider une tâche depuis l'artefact → écriture Supabase

**Inconnue totale.** Aucun des douze artefacts existants n'appelle un outil d'écriture. Les onze tools de Command Center sont tous en lecture.

**Protocole** — artefact `t-write`, `mcp_tools` = `create_task`, `list_tasks`, `update_task_status` (les deux préfixes).

1. Créer une tâche jetable dans le workspace `renaud` : `create_task` avec un titre horodaté explicite (`ZZZ-TEST-<timestamp>`).
2. Bouton « Valider » → `update_task_status` sur cette tâche.
3. Dump complet de l'enveloppe de réponse + durée.
4. Bouton « Relire » → `list_tasks` filtré, pour confirmer que l'écriture a bien atterri en base (et pas seulement renvoyé un OK).
5. Refaire l'étape 2 **une seconde fois** : le dialogue de permission réapparaît-il ?

**Points à consigner**

- L'appel d'écriture aboutit-il ? (`isError`, message)
- Un dialogue de permission s'ouvre-t-il ? À chaque appel, ou une fois par session ?
- Le round-trip est-il visible en base (étape 4) ?
- Latence.

**Enjeu** : si l'écriture passe proprement, Command Center devient un vrai poste de pilotage — cocher une tâche, clore une relance — au lieu d'un tableau de bord en lecture seule. C'est le gain le plus élevé des cinq questions.

---

### Q5 — Skill ou UI de plugin : quelle recommandation ?

**Question à instruire, pas à trancher d'emblée.** Commencer par une recherche web sur les bonnes pratiques artefacts Claude **à jour au 07/2026** — le sujet bouge vite et les conclusions de mai sont peut-être caduques. Sources à privilégier : `docs.claude.com`, notes de version du CLI, documentation « Artifacts call your MCP connectors ».

**Grille de décision à construire, axes proposés**

| Axe | Penche vers le **skill** | Penche vers l'**UI de plugin** |
|---|---|---|
| Opérateur | Claude fait le travail | Renaud manipule lui-même |
| Fréquence | ponctuel, à la demande | quotidien, récurrent |
| Sortie | un livrable (fichier, message) | un état qu'on consulte et re-consulte |
| Interaction | aucune, ou conversationnelle | filtres, onglets, sélection, validation |
| Fraîcheur | au moment de l'exécution | à chaque ouverture |
| Écriture | via les outils de la session | dépend de Q4 |
| Maintenance | markdown, versionné, diffable | HTML bundlé, republication manuelle |
| Portabilité | marche en CLI, cloud, mobile | **desktop uniquement** |

**Cas concrets à trancher avec cette grille** — chacun doit recevoir une réponse motivée :

- `morning-briefing` : skill qui rend un artefact — le bon découpage ?
- Command Center : UI, clairement. Mais qui la met à jour, et à quelle cadence ?
- Edifice front : UI ou skill qui génère un rapport ? **Dépend entièrement de Q1.**
- `/crm`, `/pm` : skills aujourd'hui. Une UI apporterait-elle quelque chose ?

**Contrainte structurante à ne pas oublier** : un artefact ne fonctionne **que sur le desktop**. Ni web, ni mobile. Tout ce qui doit être accessible depuis un téléphone reste un skill.

---

## 5. Si Q1 passe — dette connue à corriger

Dans `bluegreen-marketplace`, fichier `ui/edifice-front/src/mcp-data-adapter.ts` :

```ts
const results = await Promise.all(
  photos.map(async (p) => {
    const signedUrl = await callPhotoTool(p.id, PHOTO_MAX_WIDTH);  // 600
    …
  }),
);
```

Trois défauts cumulés :

1. **`Promise.all` est fail-fast** — une photo qui échoue efface toute la galerie. Aucune ne s'affiche.
2. **Aucune limite de concurrence** — 30 photos = 30 appels MCP simultanés.
3. **Aucune isolation par photo** — timeout, corruption, dépassement : même résultat.

Correctif : `Promise.allSettled`, concurrence bornée à 2–3, état par vignette, `PHOTO_MAX_WIDTH` à 400.

Le code carrie déjà son propre avertissement, jamais levé :

```ts
/* TODO: verify in Cowork — does this trigger more than the
   "at most one permission dialog on open" acceptance criterion in practice? */
```

**Référence contraire, dans le même dépôt** : `command-center-quotidien` fait `Promise.allSettled` avec un `catch` par panneau. Chaque bloc tombe seul. La bonne discipline existe déjà, un mois plus tôt.

---

## 6. Ordre d'exécution recommandé

1. **Vérifier le niveau du connecteur hal-mcp** (compte vs plugin) — §3.2. Peut invalider tout le reste.
2. **Q1** — bloquant, et le contournement `get_mission_photo_b64` est déjà conçu.
3. **Q4** — plus fort gain, indépendant de Q1.
4. **Q2** — largement répondu, reste le polling et le dialogue de permission.
5. **Q3** — probablement « non, passer par un outil MCP ». À confirmer par l'inventaire.
6. **Q5** — après recherche web, avec les résultats de Q1–Q4 en entrée.

**Livrable de la session de test** : un tableau à cinq lignes — question, verdict, preuve (ce qui a été cliqué et ce qui s'est affiché), décision d'architecture. Rien d'autre. Pas de nouveau front tant que Q1 n'est pas tranchée.
