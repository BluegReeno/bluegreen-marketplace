# Artefacts Cowork × serveurs MCP — état des lieux

> **Date** : 2026-07-31. **Session** : Cowork **cloud** (desktop app, dossiers montés).
> **Consolide** : le protocole de test du 30/07, `docs/cowork-artifact-publishing.md` (session
> locale du 30/07), la lecture de `ui/edifice-front/src/`, et les mesures cliquées du 31/07.
>
> **Règle de méthode.** Chaque affirmation porte sa provenance :
> **[M]** mesuré, un clic ou un appel d'outil · **[C]** code lu · **[D]** déduit, non vérifié.
> Une description d'artefact, un commentaire de code ou une note d'intention ne sont **pas**
> des preuves — deux erreurs de ce document et du précédent viennent exactement de là.

---

## 1. L'environnement d'exécution

**[M]** Relevé dans `t-bridge`, 2026-07-31 :

```
location.href    cowork-artifact://local/<artifact-id>/index.html
origin           cowork-artifact://local
isSecureContext  true
window.top === window.self   →  true
userAgent        … Claude/1.24012.9 Chrome/148.0.7778.280 Electron/42.7.0 …
localStorage     présent et fonctionnel
```

L'artefact tourne dans une fenêtre Electron, sur un protocole custom, **hors iframe**.
Ce n'est pas une page web : c'est un document servi par l'hôte, sans rien à côté de lui.

**[M]** Un chemin relatif (`./fichier.png`) rend un **404 sans violation CSP**. Le same-origin
est autorisé, mais rien n'est servi. Il n'existe aucun moyen connu d'y déposer un fichier.

### Content-Security-Policy effective

**[M]** Établie par `csp-probe` et `csp-probe-2` (30/07) :

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

| Mécanisme | État | Note |
|---|---|---|
| `<img src="https://…">` | ❌ bloqué | `img-src` ne liste que `'self'` et `data:` |
| `fetch()` / XHR / WebSocket / SSE | ❌ bloqué | `connect-src 'none'` |
| `blob:` en `img-src` | ❌ bloqué | testé, violation CSP |
| `<iframe>` / `<object>` / `<embed>` | ❌ bloqué | |
| `window.open()` | ❌ renvoie `null` | popup blocker |
| `<a target="_blank">` | ✅ | ouvre un vrai onglet navigateur, hors artefact |
| `data:` en `img-src` | ✅ | testé jusqu'à ≥ 10,7 Mo/image, décodage 14 ms |
| `localStorage` | ✅ | |
| Chart.js · Grid.js · Mermaid via jsDelivr | ✅ | **seules** dépendances CDN autorisées |
| `window.cowork.callMcpTool` | ✅ | passe par le pont de l'hôte, **pas** par la pile réseau → hors `connect-src` |

**Conséquence structurante** : la seule façon de faire entrer une image dans un artefact est
un `data:` URI, donc des octets qui ont transité par le pont MCP. Aucune URL, signée ou non,
ne peut être rendue. Ce n'est pas une question de bucket public ou privé.

---

## 2. La surface du pont

**[M]** Inventaire récursif de `window`, `t-bridge` du 31/07. L'objet injecté s'appelle
**`window.cowork`** et expose **exactement trois** fonctions :

```
window.cowork.callMcpTool        fn() arity=0
window.cowork.askClaude          fn() arity=0
window.cowork.runScheduledTask   fn() arity=0
```

**[M]** Sont **absents** : `window.claude`, `window.anthropic`, `window.electronAPI`,
`window.webkit`, `window.chrome.webview`, `window.mcp`, `window.host`, `window.bridge`,
`window.artifact`, `window.__COWORK__`, `window.ClaudeAPI`, `window.parentPort`.
Balayage complet de `window` sur `/cowork|claude|anthropic|mcp|artifact|bridge|electron|host|agent|tool/i` :
une seule clé retenue, `cowork`.

> ⚠️ La sonde `sonde-edifice-cowork` du 27/07 concluait « aucun bridge ». Elle ne testait pas
> `window.cowork`. **Faux négatif — ne pas repartir de ses conclusions.**

**[D]** Les `arity=0` ne renseignent sur rien : `callMcpTool` prend deux arguments et affiche
aussi `arity=0`. Ce sont des wrappers variadiques. La signature de `askClaude` et de
`runScheduledTask` reste **inconnue** — voir §7.

### Forme de la réponse de `callMcpTool`

**[M]** Enveloppe MCP standard, `Promise` :

```js
{ content: [ { type: "text", text: "…" } ], structuredContent: …, isError: false }
```

**[M]** Un refus d'allowlist arrive **comme une réponse normale**, pas comme un rejet :

```json
{"content":[{"type":"text",
  "text":"Tool \"mcp__hal-mcp__whoami\" is not in this artifact's mcp_tools allowlist."}],
 "isError":true}
```

Latence du refus : **2 à 5 ms**, **sans dialogue de permission**. Le contrôle est côté hôte,
avant tout appel réseau.

> **Piège de lecture.** `isError: true` avec un bloc `text` ressemble à s'y méprendre à une
> réponse valide vide. Tout code qui cherche un bloc sans tester `isError` d'abord
> transformera un refus de permission en « l'outil n'a rien renvoyé ». C'est le diagnostic
> ambigu qui a coûté trois jours sur Edifice.

### Le pont refuse *quelque chose* dans la réponse photo — le quoi n'est pas établi

**[M]** Erreur verbatim relevée le 30/07, côté artefact :

```
Error invoking remote method '$eipc_message$_…_$_claude.coworkArtifact_$_CoworkArtifactBridge_$_callMcpTool':
Error: Result from method "callMcpTool" in interface "CoworkArtifactBridge" failed to pass validation
```

**[M]** Ce qui est prouvé : le validateur de résultat du pont **a refusé** la réponse de
`get_mission_photo`. **[M]** Et que les blocs texte/JSON passent sans problème — onze outils de
`command-center-quotidien` le démontrent tous les jours.

**[D]** Ce qui **n'est pas** prouvé : que la cause soit le **type** de bloc `image`.
« failed to pass validation » est une chaîne générique. Causes non exclues :

- taille du payload sérialisé sur le canal eIPC ;
- `mimeType` absent ou mal formé dans la réponse hal ;
- forme de l'enveloppe côté hal, indépendamment du type de bloc.

> ⚠️ Le document `cowork-artifact-publishing.md` §4 écrit « the validator accepts text/JSON and
> rejects image content blocks » comme un constat. C'est une **interprétation** d'une chaîne
> générique, reprise ensuite comme un fait — y compris par ce document, jusqu'au 31/07.

**[D] Hypothèse concurrente, plus simple, jamais écartée** : `PHOTO_MAX_WIDTH` valait **600**,
largeur **jamais mesurée**, et `resolveGalleryPhotos` utilisait `Promise.all`, qui est
fail-fast. Une seule photo lente à 600 px effaçait **toute** la galerie. Cela suffit à
expliquer 100 % du symptôme observé **sans aucune panne de pont** — et c'est exactement ce que
le correctif du 31/07 traite.

**Contournement si la panne A est confirmée** : renvoyer les octets en base64 **dans un bloc
texte** (`{"mime":"image/jpeg","b64":"…"}`), que l'artefact recompose en `data:` lui-même.
Côté hal : issue #89, ~10 lignes. **À n'implémenter qu'après le test `t-photo` en local** —
voir §9.4.

---

## 3. L'allowlist — le point le plus mal compris

### Deux objets à ne pas confondre

| | `mcp_tools` | `mcpTools` |
|---|---|---|
| Nature | **paramètre d'entrée** de l'outil de publication | champ du bloc `<script id="cowork-artifact-meta">` |
| Rôle | **la permission** | un **reçu**, régénéré par la plateforme après publication |
| Modifiable ? | oui, à chaque publication | l'éditer dans le HTML **ne donne rien** (prouvé par PR #59) |

**[M]** Il n'existe **pas** de paramètre `mcpServerNames`. La plateforme le dérive des préfixes
de `mcp_tools`.

### Seule une session LOCALE peut déclarer une allowlist

**[M]** Outils de publication d'une session **locale** :

| Outil | Paramètres |
|---|---|
| `mcp__cowork__create_artifact` | `id`, `html_path`, `description`, **`mcp_tools`** |
| `mcp__cowork__update_artifact` | `id`, `html_path`, `update_summary`, `description`, **`mcp_tools`** |

**[M]** Outils d'une session **cloud** — les seuls disponibles ici :

| Outil | Paramètres |
|---|---|
| `mcp__remote-devices__create_artifact` | `id`, `file_uuid`, `description` |
| `mcp__remote-devices__update_artifact` | `id`, `file_uuid`, `update_summary`, `description` |

**Aucun `mcp_tools`.** Un artefact publié depuis le cloud part avec une allowlist vide et ne
peut appeler aucun outil.

**[M] Preuve décisive — `t-photo`, 31/07.** Un artefact publié depuis le cloud avec **12 ids
d'outils en littéraux entiers**, les deux formes d'adressage, sur 6 outils (`list_edifice_missions`,
`get_mission_context`, `get_mission_photo`, `create_task`, `update_task_status`, `list_tasks`).
Son propre bloc `cowork-artifact-meta`, lu à l'exécution :

```json
{ "name": "T Photo", "schemaVersion": 1, "mcpTools": [], "mcpServerNames": [] }
```

Et les 12 appels refusés un par un : `is not in this artifact's mcp_tools allowlist`.

> **Ce que ça tue.** Le commentaire en tête de `cowork-mcp.ts` affirmait que la plateforme
> dérive `mcpTools` **en scannant les littéraux du bundle**. C'est **faux** : des littéraux
> parfaitement formés donnent `mcpTools: []`. L'allowlist ne vient **que** du paramètre
> `mcp_tools` de l'outil de publication. Le conseil « déclarer les ids en littéraux entiers »
> reste bon pour la lisibilité et le grep, mais il n'accorde **rien**.
>
> C'est aussi la mesure propre que `t-bridge` n'était pas : `t-bridge` concaténait ses ids,
> son refus était donc compatible avec deux causes. Ici, plus d'ambiguïté possible.

> ⛔ **Ne jamais appeler `mcp__remote-devices__update_artifact` sur un artefact qui marche.**
> Le chemin cloud ne transporte pas l'allowlist : il écrase une version fonctionnelle par une
> version muette. C'est arrivé à `edifice-front` le 28/07.

### Règles de publication

1. **Repasser la liste complète à chaque republication.** `mcp_tools` **remplace** la liste
   stockée, et la déclaration ne vit pas dans le HTML : elle est irrécupérable depuis le fichier.
2. **Appeler au moins un outil hal dans la session avant de publier.** Le schéma dit
   « only list tools you actually called this session » — c'est une exigence de la plateforme.
3. **Déclarer les ids comme littéraux entiers dans le bundle.** L'artefact de référence
   `command-center-quotidien` fait `const T_SPRINTS = "mcp__<uuid>__list_sprints"` — **[C]**
   vérifié, lignes 188-192. Ne jamais assembler un id par concaténation à l'exécution.
   *(Ma propre sonde `t-bridge` a fait cette faute : elle construisait `prefix + "whoami"`.
   Sa conclusion tient par recoupement avec le doc du 30/07, pas par la propreté du test.)*

---

## 4. Deux formes d'adressage, et laquelle répond n'est pas stable

**[M]** Le même connecteur répond sous deux noms :

- nom court → `mcp__hal-mcp__<outil>`
- UUID d'annuaire → `mcp__7898d523-5bb3-4502-b704-16db78ae0a8c__<outil>`

**[M]** Observé dans une seule et même session locale, le 30/07 :

| Contexte | Forme réellement utilisée |
|---|---|
| Les noms d'outils de la session de chat | **UUID** |
| Le runtime de l'artefact publié | **nom court** |

Le 28/07, c'était **exactement l'inverse**.

**Deux conséquences, toutes deux obligatoires :**

1. Déclarer **les deux formes** dans `mcp_tools` — 6 ids pour 3 outils. Une allowlist est une
   permission, pas une table de routage : y lister un nom jamais utilisé ne coûte rien.
2. **Résoudre dynamiquement dans le bundle** : essayer les formes candidates, garder celle qui
   répond, mémoriser en `localStorage`. Ne jamais figer une forme, ni dériver le nom du runtime
   des noms d'outils que voit la session.

### UUID des connecteurs — à revérifier par poste

**[M]** Relevés le 31/07 sur `lepecq-local`. **Ils sont propres à chaque machine.**

| Connecteur | UUID |
|---|---|
| hal-mcp | `7898d523-5bb3-4502-b704-16db78ae0a8c` |
| Google Calendar | `6fd5fd1e-2c83-4b88-9e45-6b063ff778ec` |

**[M]** **hal-mcp est un connecteur de niveau compte**, pas seulement un MCP de plugin :
`connected: true`, présent dans l'annuaire avec un UUID et une URL. Aucune installation
supplémentaire n'est nécessaire. *(Cette question bloquait tout le reste : elle est réglée.)*

**[M]** Le nom de l'outil qui lit l'annuaire **diffère selon le contexte** — `ListConnectors`
en cloud, `mcp__mcp-registry__list_connectors` en local — et les champs rendus aussi
(`installedServerId`/`enabledInChat` vs `directoryUuid`/`connected`). Lire l'annuaire à
l'exécution, ne jamais coder un nom de champ en dur.

---

## 5. Les cinq questions — verdicts

| Q | Verdict | Preuve |
|---|---|---|
| **Q1 — afficher une photo** | ✅ **Répondue.** Deux pannes indépendantes, pas une. | §6 ci-dessous |
| **Q2 — rafraîchissement** | ✅ **Aucune API d'abonnement.** | **[M]** inventaire `t-bridge` : zéro `on*`, `subscribe`, `watch`, `observe`, `addListener` sur `window.cowork` |
| **Q3 — appeler un agent** | 🟠 **`askClaude` existe.** Signature inconnue. | **[M]** inventaire `t-bridge` |
| **Q4 — écrire depuis l'artefact** | ⛔ **Non testée.** Exige une allowlist, donc une session locale. | — |
| **Q5 — skill ou UI** | 🟠 **Grille ci-dessous**, non instruite par recherche web. | — |

### Q1 — deux pannes, pas une

**[M]** Mesuré le 30/07 en **chat** (donc **sans pont dans le chemin**), photo
`3d7700c2-1760-45b8-805b-852170c0b8c0`, mission « Suivi des travaux », 36 Rue Bayen :

| # | `max_width` | Résultat |
|---|---|---|
| 1 | 320 | ✅ image valide, latence normale |
| 2 | 1200 | ❌ `tool "get_mission_photo" timed out after 180s` |
| 3 | 320 | ❌ « The connector's server isn't responding » — juste après l'appel à 1200 |
| 4 | 320 | ✅ image valide — l'instance a récupéré |

- **Panne A — transport.** Le pont rejette les blocs image (§2). Correctif : base64 en bloc
  texte, hal#89.
- **Panne B — redimensionnement serveur.** À ~1200 px, l'appel ne rend pas la main en 180 s
  et laisse l'isolate muet pour l'appel suivant. Suspects : coût/mémoire de `magick-wasm`,
  limites CPU/mémoire de l'Edge Function, démarrage à froid (14,6 Mo de wasm par isolate).

**Ces deux pannes sont indépendantes.** Changer le transport ne change pas le
redimensionnement. Et comme **`max_width` vaut 1200 par défaut**, un appel en mode JSON qui
omet le paramètre retombe droit dans la panne B.

**320 est la seule largeur mesurée.** 400 (recommandé par le protocole) et 600 (valeur du
code) n'ont **jamais** été mesurés.

### Q2 — ce qui reste possible

Il n'y a pas d'abonnement, donc trois options seulement :

1. **Le bouton Reload de l'hôte** — remonte la page, rejoue `init()`, rappelle les outils.
   C'est ce que fait `command-center-quotidien` aujourd'hui, et c'est suffisant pour un usage
   quotidien.
2. **`setInterval` + `callMcpTool`** — non testé. Deux inconnues : un dialogue de permission
   apparaît-il à chaque tick, et la page est-elle suspendue quand la sidebar est masquée ?
3. **`runScheduledTask`** — piste inexplorée, voir §7.

### Q5 — grille de décision skill vs UI d'artefact

*Non instruite par recherche web ; à confronter à la doc à jour avant d'être figée.*

| Axe | Penche **skill** | Penche **UI d'artefact** |
|---|---|---|
| Opérateur | Claude fait le travail | Renaud manipule lui-même |
| Fréquence | ponctuel, à la demande | quotidien, récurrent |
| Sortie | un livrable (fichier, message) | un état qu'on consulte et reconsulte |
| Interaction | aucune, ou conversationnelle | filtres, onglets, sélection, validation |
| Fraîcheur | au moment de l'exécution | à chaque ouverture |
| Écriture | via les outils de la session | dépend de Q4 |
| Maintenance | markdown, versionné, diffable | HTML bundlé, republication manuelle **depuis une session locale** |
| Portabilité | CLI, cloud, mobile | **desktop uniquement** |

**Contrainte structurante** : un artefact ne fonctionne que sur le desktop, et ne peut être
(re)publié utilement que depuis une session locale. Tout ce qui doit être atteignable depuis
un téléphone reste un skill. Cette seule ligne tranche la plupart des cas.

---

## 6. Ce qui a été corrigé le 31/07 dans `ui/edifice-front/`

Quatre fichiers, écrits sur disque, **non compilés ni republiés** — `npm run build` puis
republication depuis une session locale restent à faire.

### `src/cowork-mcp.ts`

- **Les deux formes d'adressage** déclarées comme littéraux entiers (8 ids pour 4 outils),
  avec résolution dynamique et mémorisation en `localStorage`. L'ancienne version ne
  connaissait que la forme UUID.
- **`classifyError` recâblé sur les vraies chaînes d'erreur.** L'ancienne version testait
  `includes("timeout")` alors que la chaîne réelle est `timed out after 180s` : **[C]** aucune
  branche ne se déclenchait jamais, tout tombait en `upstream_error`. Le `TODO: verify against
  real error text` du fichier attendait ces chaînes ; elles existaient depuis le 30/07 dans le
  document d'à côté.
- **Deux codes d'erreur nouveaux** : `tool_not_allowed` et `bridge_rejected_image`, qui
  nomment enfin les deux causes réelles au lieu de les fondre dans « erreur inattendue ».
- **`callPhotoTool` passe par `get_mission_photo_b64` en premier**, et ne retombe sur
  `get_mission_photo` que si le tool b64 est absent de l'allowlist — pour dégrader vers une
  erreur précise, pas vers une galerie blanche.
- **`PHOTO_MAX_WIDTH = 320`**, toujours passé explicitement, avec la mesure en commentaire.

### `src/mcp-data-adapter.ts`

- **`Promise.all` remplacé par un pool borné à 2**, chaque photo isolée. L'ancienne version
  était fail-fast : **une** photo en échec effaçait **toute** la galerie — et comme l'échec le
  plus fréquent était un timeout, le résultat courant était une galerie vide avec un seul
  message d'erreur.
- La fonction **ne rejette plus** pour une photo ; elle renvoie `{ photos, failures }`.
  Elle ne rejette que pour les pannes de canal (`no_cowork`, `not_hydrated`), où rien ne
  chargera jamais.
- Ordre d'origine des photos préservé malgré la concurrence.

### `src/components/MissionDetail.tsx` · `src/components/ErrorBanner.tsx`

- Galerie **partielle** affichée + bandeau ambre « N photos sur M n'ont pas pu être chargées »
  avec le détail de la première erreur. Le bandeau rouge pleine largeur n'apparaît plus que si
  **rien** n'a chargé.
- Messages d'aide pour les deux nouveaux codes, qui disent quoi faire : republier depuis une
  session locale avec les deux formes, ou déployer `get_mission_photo_b64`.

### Reste à faire côté hal

**`get_mission_photo_b64`** — même contenu que `get_mission_photo`, renvoyé en bloc **texte** :
`{"mime":"image/jpeg","b64":"…"}`. ~10 lignes de Python. **C'est le seul élément qui manque
pour que la photo s'affiche.** La panne B (redimensionnement) reste ouverte mais est contournée
tant que tous les appelants passent `max_width: 320` explicitement.

---

## 7. Pistes à essayer, par ordre de rendement

### 7.1 `window.cowork.askClaude` — signature inconnue 🔴

C'est le renversement de la session : l'API d'agent que le protocole du 30/07 déclarait
inexistante **existe**. Reste à savoir comment l'appeler et ce qu'elle rend.

**À tester** — artefact `t-ask`, **session locale** : `Function.prototype.toString` complet,
puis cinq formes d'appel — `askClaude("texte")`, `{prompt}`, `{message}`, `("texte", {})`,
sans argument — avec dump brut du retour, du type (`Promise` ? `asyncIterable` ?) et de la durée.

> ⚠️ **Ce test a été refusé deux fois par le classifieur de sécurité en session cloud**, sur
> deux formulations différentes, y compris une version réduite au seul `askClaude`. Un artefact
> qui invoque le modèle de sa propre initiative est un vecteur d'injection de prompt, et le
> garde-fou ne distingue pas un protocole de test d'un usage hostile. **À reprendre en local**,
> et si le refus persiste, considérer la piste comme fermée par conception.

**Même si ça marche, ce n'est probablement pas la bonne fondation** : faire passer l'agent par
un outil du serveur MCP (`hal.ask(prompt, context)`) garde la clé API et le prompt système hors
de la page, rend le raisonnement journalisable côté serveur, et sert le même outil à Cowork, au
CLI et à openclaw. `askClaude` serait un raccourci desktop-only.

### 7.2 `window.cowork.runScheduledTask` — totalement inexploré 🔴

Absent de toute documentation. **[D]** Si un artefact peut déclencher une tâche planifiée, c'est
un chemin d'**écriture** qui ne passe pas par `mcp_tools` du tout — donc potentiellement une
réponse à Q4 **et** un pivot pour Q5 (un bouton qui lance un skill au lieu d'appeler un outil).

**À tester** — session locale, appel sans argument puis avec `{}`, pour lire le message d'erreur
qui révèle en général le schéma attendu. Bouton isolé et clairement étiqueté : la fonction peut
avoir des effets de bord.

### 7.3 Q4 — écriture MCP depuis l'artefact 🟠

Aucun des treize artefacts existants n'appelle un outil d'écriture. **[D]** Rien n'indique que
ce soit interdit — l'allowlist ne distingue pas lecture et écriture — mais rien ne le prouve.

**Protocole** — artefact `t-write`, session locale, `mcp_tools` = `create_task`, `list_tasks`,
`update_task_status`, **les deux formes** :

1. Créer une tâche jetable dans le workspace `renaud`, titre horodaté `ZZZ-TEST-<timestamp>`.
2. Bouton « Valider » → `update_task_status`. Dump complet de l'enveloppe + durée.
3. Bouton « Relire » → `list_tasks` filtré, pour confirmer que l'écriture a atterri **en base**
   et pas seulement rendu un OK.
4. Refaire l'étape 2 une seconde fois : le dialogue de permission réapparaît-il ?

`update_task_status` est le bon candidat : petit, idempotent, réversible.

**Enjeu** : si l'écriture passe, `command-center-quotidien` devient un poste de pilotage —
cocher une tâche, clore une relance — au lieu d'un tableau de bord en lecture seule.

### 7.4 Q2 — polling 🟡

Artefact `t-poll`, un tick toutes les 20 s sur `whoami`, compteur succès/échecs + horodatage,
laissé tourner 3 min, sidebar masquée une partie du temps. Répond à deux questions d'un coup :
dialogue de permission répété ? page suspendue ?

**Rendement faible** : le bouton Reload de l'hôte suffit déjà à l'usage quotidien.

### 7.5 Panne B — le redimensionnement serveur 🟡

Indépendante de Cowork, à instruire côté hal : profiler `magick-wasm`, mesurer le démarrage à
froid (14,6 Mo de wasm par isolate), envisager des vignettes **pré-calculées au dépôt** plutôt
qu'un redimensionnement à la demande. Tant que ce n'est pas fait, tout appelant doit passer
`max_width: 320` explicitement — **le défaut serveur, 1200, est la valeur qui casse**.

### 7.6 Q5 — recherche web 🟡

La grille du §5 n'est pas confrontée à la documentation à jour. Sources à privilégier :
`docs.claude.com`, notes de version du CLI, documentation « Artifacts call your MCP connectors ».
Cas concrets à trancher : `morning-briefing` (skill qui rend un artefact — bon découpage ?),
Command Center (UI, mais qui la republie et à quelle cadence ?), Edifice front (UI ou skill qui
génère un rapport ?), `/crm` et `/pm` (une UI apporterait-elle quelque chose ?).

---

## 8. Règles de méthode, tirées de nos propres erreurs

1. **Une description d'artefact décrit une intention au moment de la publication, pas un fait.**
   Une session entière a conclu que la photo marchait en lisant des descriptions. Elle n'a
   jamais marché.
2. **Un commentaire de code n'est pas une mesure non plus.** Le commentaire en tête de
   `cowork-mcp.ts` affirmait que la plateforme dérive `mcpTools` en scannant les littéraux du
   bundle ; la mesure du 30/07 montre que c'est le paramètre `mcp_tools` qui fait foi. Le
   commentaire était une théorie, écrite comme un constat.
3. **Ne jamais citer un extrait de code sans ouvrir le fichier.** Le 31/07, j'ai conclu que le
   front ne testait pas `isError` en me fiant à un extrait cité dans le protocole. Le test
   existe, lignes 174-177. La déduction entière était fausse.
4. **Un test dont le résultat serait le même sous deux hypothèses différentes ne tranche rien.**
   `t-bridge` construisait son id d'outil par concaténation : son refus d'allowlist était
   compatible avec « allowlist vide en cloud » **et** avec « id introuvable ». Il a fallu
   `t-photo`, avec des littéraux entiers et la lecture directe du reçu, pour trancher.
5. **Lire `docs/` avant de tester.** Une session de test a été ouverte pour des questions déjà
   documentées à trois mètres, dans le même dépôt.
6. **Chercher l'instrument qui mesure sans intermédiaire.** Les six premières heures ont été
   passées à *déduire* l'état de l'allowlist depuis des refus d'appel. L'artefact peut lire
   son propre bloc `cowork-artifact-meta` : une ligne de JavaScript, zéro clic, réponse
   directe. La bonne question n'est pas « quel test faire », c'est « qu'est-ce qui est
   lisible directement ».

---

## 9. Clôture — verdicts et recommandations

*Arrêté le 2026-07-31 à 17h30. Chaque ligne : ce qui marche, ce qui ne marche pas, la preuve,
et la décision qui en découle.*

### 9.1 La contrainte qui domine tout

**❌ Publier un artefact vivant depuis une session cloud NE MARCHE PAS.**

**Preuve** — `t-photo`, 31/07 : 12 ids en littéraux entiers, deux formes, 6 outils ;
`mcpTools: []` lu dans le reçu de l'artefact lui-même ; 12 appels refusés.
Aucune interprétation, aucune ambiguïté.

**Décision** : toute publication ou republication d'un artefact qui appelle des outils passe
par une **session Cowork locale**, avec `mcp__cowork__{create,update}_artifact` et le
paramètre `mcp_tools` — **liste complète repassée à chaque fois, les deux formes d'adressage**.
Le chemin `mcp__remote-devices__*` est réservé aux artefacts statiques (rapports, schémas).
L'utiliser sur un artefact vivant **le casse silencieusement**.

Cette contrainte est la cause unique de trois des cinq questions restées ouvertes. Ce n'est
pas cinq problèmes : c'est un seul, identifié, avec une procédure de levée connue.

### 9.2 Les cinq questions

| Q | Verdict | Preuve | Recommandation |
|---|---|---|---|
| **Q1 — photo** | 🔶 **Indéterminé**, mais l'hypothèse a changé | Panne A = interprétation d'une chaîne d'erreur générique. Panne B mesurée : 1200 ❌ 180 s, 320 ✅. `PHOTO_MAX_WIDTH` valait 600, jamais mesuré, avec `Promise.all` fail-fast | **Ne pas toucher hal avant d'avoir cliqué `t-photo` en local.** Le correctif du 31/07 (allSettled + 320 + isolation) peut suffire à lui seul |
| **Q2 — rafraîchissement** | ❌ **Pas d'abonnement** · ✅ **Reload suffit** | Inventaire `t-bridge` : zéro `on*`/`subscribe`/`watch`/`observe` | Bouton Reload de l'hôte. Ne pas construire de polling : gain nul, risque de dialogue par tick |
| **Q3 — agent** | 🔶 **`askClaude` existe, intestable** | Présent dans `window.cowork`. Publication refusée **2 fois** par le classifieur, sur 2 formulations | **Passer par un outil MCP hal `ask(prompt, context)`.** Meilleur de toute façon : clé API hors de la page, raisonnement journalisable, même outil pour Cowork, CLI et openclaw |
| **Q4 — écriture** | 🔶 **Non testé** — bloqué par 9.1 | 12 refus d'allowlist | `t-photo` teste déjà la chaîne complète (E→F→G→H). Un clic en local |
| **Q5 — skill ou UI** | ✅ **Tranché** | Contrainte dure : artefact = **desktop uniquement** + republication manuelle en local | Voir 9.3 |

### 9.3 Q5 — arbitrage, cas par cas

La contrainte de 9.1 change la grille : une UI d'artefact n'est pas seulement desktop-only,
elle exige **une session locale à chaque mise à jour**. Son coût de maintenance est réel.

| Cas | Décision | Pourquoi |
|---|---|---|
| `morning-briefing` | **Skill.** L'artefact rendu reste un bonus desktop | Doit être lisible depuis un téléphone. Un artefact ne l'est pas |
| Command Center | **UI**, et c'est le bon cas | État consulté et reconsulté, quotidien, desktop. Change rarement → le coût de republication est amorti |
| Edifice front | **Suspendu à Q1.** En attendant : **skill qui génère un rapport** | Un rapport se lit partout, se classe, s'envoie. Une UI qui n'affiche pas les photos n'apporte rien de plus qu'un rapport |
| `/crm`, `/pm` | **Skills, ne rien changer** | Usage conversationnel, sorties = livrables. Une UI n'ajouterait que de la maintenance |

**Règle générale** : UI d'artefact seulement si les trois conditions sont réunies — usage
**quotidien**, **desktop**, et contenu qui **change rarement**. Sinon, skill.

### 9.4 La suite, dans l'ordre, en session locale

1. `npm run build` dans `ui/edifice-front/` — vérifier que le correctif du 31/07 compile.
   *(Impossible depuis Cowork : `node_modules/typescript` est un symlink hors du dossier
   monté, cassé à travers le pont. Toute compilation de ce repo exige le poste.)*
2. Publier `t-photo` avec `mcp_tools` = les 12 ids. Cliquer A→B→C→D, puis E→F→G→H.
   **Noter si un dialogue de permission apparaît, et à quel moment.**
3. **Selon C** : image rendue → hal#89 inutile, republier `edifice-front` et c'est fini.
   Rejet `failed to pass validation` → implémenter `get_mission_photo_b64` (~10 lignes),
   l'ajouter à l'allowlist, republier.
4. Reporter les verdicts de Q1 et Q4 ici même, en remplaçant les 🔶.

**Ne pas** : republier quoi que ce soit depuis le cloud · relancer une sonde `askClaude` ·
construire un sixième artefact de test avant d'avoir cliqué `t-photo`.
