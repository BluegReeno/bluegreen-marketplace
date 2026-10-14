---
type: llm
weight: 3
focus: trace
---
Judge the run against the checklist below. The hal rows the assistant could read are the
mocked hal-mcp results in the trace — the fictional bench (workspaces hal-audit-*), not real
data. Judge the final answer and the tool calls; a value the answer cites that no tool result
carries is invented. Vote PASS only if every item holds.

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
