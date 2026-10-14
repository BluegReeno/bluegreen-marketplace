---
type: llm
weight: 3
---
You see the assistant's final message only. The assistant read a fictional bench (hal
workspaces hal-audit-*, served by a mock) whose rows the checklist quotes: a fact in the message
that the checklist names as the rows' content is read, not invented. Whether a tool was called
or a row written is verified by separate graders you do not see: treat every item about tool
calls or writes as satisfied unless the message itself contradicts it (« j'ai créé », « j'ai
enregistré »), and never fail an item for lack of visibility. Judge what the message says against
the checklist — the facts, the gates, the wording — and vote PASS when every item you can see
holds.

Checklist:
1. The answer lists the seven open tasks of hal-audit-famille — six todo and « Prendre RDV
   passeport en mairie » in progress (splitting the one in progress from the six to do is
   fine; reading « en cours » as the one in_progress alone, silently, is not) — with their
   due dates as the rows carry them. The done task (« Attestation d'assurance scolaire
   pour Inès ») is not listed as open.
2. No task of another workspace is mixed in — not the personal tasks of
   hal-audit-jobsearch, not edifice's or pme's.
3. Who each task is for is not in the base: said (« non attribuées », « l'assignation
   n'est pas renseignée » or equivalent), never guessed from the title — not even
   « Renouvellement passeport Sofia » → Sofia.
4. Nothing was written: no task assigned, re-dated or closed.
