---
name: file
description: >
  Ranger un papier : lire le document, extraire ses faits, choisir workspace, domaine, kind et slug,
  décider « fiche seule ou fiche et base de connaissance », référencer le fichier dans le stockage du
  workspace et écrire la fiche. Déclencher sur : "range ce devis", "garde le nouveau KBIS", "stocke ça",
  "enregistre cette procédure", "fais une fiche pour ce papier". NE PAS déclencher pour : retrouver ou
  lire un document (→ list_documents, get_document, get_document_link nommés dans la phrase), indexer
  (→ knowledge:ingest).
allowed-tools: "Read mcp__plugin_hal_hal-mcp__whoami mcp__plugin_hal_hal-mcp__list_documents mcp__plugin_hal_hal-mcp__get_document mcp__plugin_hal_hal-mcp__list_projects mcp__plugin_hal_hal-mcp__save_document"
---

# File — ranger un papier

hal garde la **fiche** (faits, validité, lien) ; le **fichier** reste dans le stockage du workspace.
hal ne copie, n'envoie et n'écrase aucun fichier : il le référence par `storage {provider, uri}`.
Les faits d'abord, le fichier ensuite. Sorties en français.

## 1. Lire et extraire

Lire le papier donné (PDF, photo, texte collé) et en extraire les faits : numéros, montants, dates,
personnes (SIREN, IBAN, échéance…). **Les montrer avant d'écrire.** Un fait illisible est signalé, jamais
reconstitué.

## 2. Situer la fiche

1. `whoami`, une fois. Échec → « ❌ hal-mcp non connecté. Reconnexion : `/mcp` → `plugin:hal:hal-mcp` →
   `authenticate`. » Le workspace est celui dont les membres doivent voir le papier (l'appartenance décide de ce que
   chacun voit) ; ambigu → demander. **`archived` → s'arrêter** : aucune écriture n'y est acceptée.
2. `domain` : une valeur de `allowed_tags` du workspace, jamais inventée (hal refuse en énumérant les
   valeurs permises).
3. `kind` : `list_documents(summary_only=true)` donne les kinds déjà employés par domaine (`by_kind`) ;
   en réemployer un qui convient, ne coiner qu'à défaut (`linkedin_draft` / `linkedin-draft`, c'est la
   dérive à éviter).
4. `slug` : minuscules, chiffres, tirets, stable et daté (`kbis-2026-06`). Deux papiers successifs
   sont deux fiches, pas une écrasée. `list_documents(search=<slug>)` avant d'écrire : un slug existant
   = mise à jour de cette fiche, à confirmer.
5. Métadonnées : `valid_until` si le papier expire, `issued_date` s'il est daté, `person_name` s'il
   concerne une personne, `project_id` s'il appartient à un projet (le retrouver par `list_projects`),
   `sensitive` pour une pièce d'identité, un RIB, un avis fiscal ou social.

## 3. Fiche seule, ou fiche et base de connaissance

Une seule question : **« voudrai-je un jour retrouver une phrase de ce document sans savoir dans quel
document elle est ? »**

- Non — une pièce (RIB, KBIS, devis, facture, attestation), une photo, un fichier de travail (budget,
  suivi), un journal : fiche seule, `knowledge` reste faux. Le trouver, c'est `list_documents`.
- Oui — une méthode, une procédure, un cours, une leçon, un retour d'expérience, une note de
  décision : `knowledge=true`. **Le dire à Renaud.** `knowledge` et `sensitive` ne vont jamais
  ensemble (hal refuse).

`content_md` porte ce qui doit être trouvable par le sens ; une fiche cochée sans `content_md` n'a rien
à indexer. Une leçon d'un message (« stocke ça ») est un `content_md` sans fichier.

## 4. Le fichier

`whoami` donne par workspace `storage` (`{provider, root}`, ou `{}` s'il n'est pas déclaré) et `folders`
(`[{name, domain, rule?}]`) : le dossier de premier niveau d'un fichier est celui dont le `domain` est le
domaine de la fiche, et sa `rule` dit le sous-dossier (par personne, par année, par projet).

- Le fichier **est déjà** dans le stockage → demander son lien ; ce sera `storage.uri`, avec
  `provider` = celui du workspace.
- Il n'y est pas → dire où le mettre (`folders[].name` + sous-dossier selon `rule`), sans le pousser soi-même
  ; Renaud le range puis donne le lien. Pas de `folders` pour ce domaine, ou `storage` vide → **ne pas
  inventer d'emplacement** : dire que le workspace n'en déclare pas, et écrire la fiche sans fichier
  seulement si `content_md` suffit.
- Papier sans fichier utile (texte collé) → fiche avec `content_md`, sans `storage`.

## 5. Écrire — après une confirmation

Montrer le plan en un message (workspace, domain, kind, slug, titre, faits, dates, `sensitive`,
`knowledge`, `project_id`, `storage`) et attendre le oui, puis :

`save_document(workspace_slug, slug, domain, kind, title, facts, content_md?, storage?, issued_date?,
valid_until?, person_name?, sensitive?, knowledge?, project_id?)`.

Lire la réponse : un `unindexed` non nul veut dire que des passages sont sortis de la base (fiche
repassée à `knowledge` faux ou `sensitive`). Fiche cochée `knowledge` → « en attente : elle sera trouvable
par `kb_search` après le prochain `knowledge:ingest pending` sur le Mac ». Rattacher à un projet une
fiche déjà rangée : `save_document` avec son `slug` et `project_id`, rien d'autre.

## Garde-fous

- Rien n'est écrit avant que les faits aient été montrés et le plan confirmé.
- Jamais de fichier envoyé, déplacé ou écrasé par hal ; jamais d'emplacement hors des `folders` déclarés.
- Une valeur refusée par hal (domaine, slug, kind…) se corrige d'après le message, sans contournement.
- Une pièce `sensitive` n'est jamais cochée `knowledge` et son lien ne sort de la conversation qu'avec l'accord de Renaud.
