---
name: ingest
description: >
  Rendre un texte trouvable par kb_search : le rattrapage (fiches cochées knowledge et transcripts
  d'appel en attente) ou une source isolée (un cours, une transcription de vidéo, une procédure en
  markdown ou HTML). Déclencher sur : "indexe", "mets ça dans la base de connaissance", "rattrape
  l'indexation", "ingère ce cours". NE PAS déclencher pour : indexer un appel (→ dernière étape de
  gtm:call), ranger un papier (→ knowledge:file), interroger la base (→ kb_search nommé dans la phrase).
allowed-tools: "Bash(uv *) Bash(test *) Bash(mkdir *) Read Write mcp__plugin_hal_hal-mcp__whoami mcp__plugin_hal_hal-mcp__kb_search"
---

# Ingest — indexer ce dont on voudra retrouver une phrase

La base de connaissance ne contient que ce qui a été **dit** (appels, vidéos), **appris** (cours,
leçons) ou **comment on fait** (procédures). Un papier, une photo, un fichier de travail, un journal
ont une fiche et rien d'autre (→ `knowledge:file`). Écrire une fiche ne rend rien trouvable : tant que
la source n'est pas indexée, `kb_search` ne la voit pas, sans message.

Le découpage en passages tourne **sur le Mac seulement** (Docling, dans le checkout hal) ; hal calcule
les vecteurs. Ce skill enchaîne : résoudre le workspace, préparer le markdown, lancer le script, lire
le rapport. Sorties en français.

Arguments : `pending [workspace]` (rattrapage) ou `<fichier | texte collé> [--kind course|video|document]
[--date AAAA-MM-JJ] [--workspace slug] [--title …]` (une source).

## 1. Pre-flight — aucune écriture avant

1. `whoami` (échec → « ❌ hal-mcp non connecté. Reconnexion : `/mcp` → `plugin:hal:hal-mcp` →
   `authenticate`. »).
2. **Le Mac.**
   ```bash
   HAL="${HAL_REPO:-$HOME/Projects/hal}"
   test -f "$HAL/scripts/kb/ingest.py" && test -f "$HAL/.env" && uv --version
   ```
   Un échec → **refuser en le nommant** : « knowledge:ingest a besoin du checkout hal, de son `.env` et de
   `uv` sur le Mac (introuvable : <quoi>). Rien n'est écrit. Pour qu'un document attende l'indexation,
   coche-le `knowledge` (`knowledge:file`) : le prochain rattrapage sur le Mac l'indexera. » Jamais
   une source écrite sans passages. Ne jamais lire ni afficher `.env`.
3. **Le workspace** : `knowledge_enabled` vrai et non `archived` (une écriture y est refusée). Argument
   absent ou ambigu → demander parmi ceux qui conviennent. `--workspace` est obligatoire pour le script.

## 2. Rattrapage — `pending`

Les lignes que le script considère : les fiches cochées `knowledge` qui ont un `content_md`, et les
interactions qui ont un `transcript`, dont le texte a changé depuis leur dernière indexation. Une
fiche `sensitive` ou non cochée est sautée et comptée.

1. D'abord à blanc :
   ```bash
   uv run --project "$HAL" --group kb python "$HAL/scripts/kb/ingest.py" --pending --workspace "$WS" --dry-run --env-file "$HAL/.env"
   ```
   Montrer le nombre de sources et de passages, les `skipped` (no text / confid. / not knowledge) et le
   bloc `CONFIDENTIAL` s'il existe. Si la détection de langue n'est pas sûre, le script s'arrête en
   nommant la source : demander `french`, `english` ou `simple`, puis **restreindre le run avec
   `--only <cette source>` avant `--lang`** (sans quoi `--lang` s'applique à toutes les sources du run).
2. Sur le oui, la même commande sans `--dry-run`.
3. Un workspace par commande : « tous mes workspaces » = une commande par workspace éligible, une
   confirmation chacune.

## 3. Une source — `<fichier ou texte>`

1. Matière : un fichier `.md` ou `.html` sur disque, ou un texte collé écrit dans un fichier `.md` du
   scratch de session. Autre format (PDF, vidéo) → le dire : seul le markdown et l'HTML sont acceptés ; une
   vidéo n'entre que comme transcription déjà obtenue.
2. `kind` : `course`, `video` ou `document`. Un transcript d'appel ou une analyse d'appel relèvent de
   `gtm:call`, pas d'ici. **`--date`** (le jour où le contenu a eu lieu) est obligatoire pour `course` et
   `video` : demander si absente, jamais l'inventer.
3. `--title` si le fichier n'en dit pas. `--sensitive` seulement pour une parole de tiers rapportée
   textuellement, sur un oui explicite. Ne pas indexer une pièce confidentielle (RIB, pièce d'identité).
4. À blanc, puis sur le oui :
   ```bash
   uv run --project "$HAL" --group kb python "$HAL/scripts/kb/ingest.py" <fichier> --workspace "$WS" \
     --kind <kind> --date <date> [--from html] [--title "…"] [--sensitive] [--dry-run] --env-file "$HAL/.env"
   ```
5. **Vérifier que c'est trouvable** : `kb_search(workspace_slug=WS, query=<une phrase distinctive de la
   source>)` ; la source doit revenir. Sinon le dire, ne pas conclure « indexé ».

## 4. Lire le rapport

`indexed`, `unchanged` (hash inchangé : rien n'est réécrit), nombre de passages. Pour une analyse
d'appel, le taux d'ancrage et le bloc `UNANCHORED` (indexé et signalé, pas jeté). Exit non nul →
« ❌ Indexation échouée : <message du script> », la commande à relancer, rien d'autre ; jamais de
saut silencieux ni de contournement.

## Garde-fous

- Confirmer avant tout run qui écrit ; `--dry-run` d'abord, toujours.
- Une source sans texte n'est pas indexée : le script la nomme, la reporter telle quelle.
- Un document décoché `knowledge` ou `sensitive` sort de la base à l'écriture de sa fiche
  (`save_document`) : cela ne passe pas par ce skill.
- Ne jamais contourner le Mac : pas de découpage à la main, pas d'appel direct à `kb_index`.
