---
description: Call — transformer un appel (client ou entretien) en connaissance hal (transcript, analyse, indexation)
argument-hint: "[entreprise | date | transcript collé | appels sans CR]"
allowed-tools: "Skill(gtm:call)"
---

Call — Argument reçu : `$ARGUMENTS`

Invoquer le skill par son nom namespacé, en lui passant les arguments tels quels :

```
Skill("gtm:call", "$ARGUMENTS")
```

Cette commande **délègue** au lieu de copier les étapes du skill — la seule du dépôt à le faire :
`gtm:call` est aussi appelé par `jobsearch:log-cr` (renaud-marketplace), et une seconde
implémentation dans ce fichier dériverait de la première (hal#192).

- Si l'invocation échoue sur `Unknown skill` → s'arrêter et dire que le plugin `gtm`
  (bluegreen-marketplace) doit être (ré)installé : `/plugin install gtm@bluegreen-marketplace`.
- Ne jamais lire `skills/call/SKILL.md` pour en exécuter les étapes à la place du skill.
- Le skill porte seul ses pré-requis (hal-mcp sur le contrat cible, checkout hal et `uv` sur le
  Mac) et s'arrête par un message nommé s'il en manque un : ne rien vérifier ni écrire ici.
