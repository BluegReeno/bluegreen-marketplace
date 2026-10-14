---
type: llm
weight: 3
---
Judge the run against the checklist below. The hal rows the assistant could read are the
mocked hal-mcp results in the trace — the fictional bench (workspaces hal-audit-*), not real
data. Judge the final answer and the tool calls; a value the answer cites that no tool result
carries is invented. Vote PASS only if every item holds.

Checklist:
1. The rate is given per sprinted workspace on the S37 tasks: 0 of 4 done in each (one
   in progress in each). The done tasks outside the sprint (« Envoyer les factures
   d'août », « Attestation Pôle emploi ») are not counted into the sprint's rate. A
   rate over every task of the four workspaces — the sprintless famille and edifice
   included — given as THE answer, with the S37 figure after it, is a fail: run
   20261013-095037 led with « 13 %, 4/30 » and the judge passed it, run 20261011-165111
   gave the same answer and was failed. The S37 rate first, then a cross-workspace table
   labelled as another view, is a pass (run 20261013-100257 was failed on that reading
   of this line, before it was reworded).
2. Cancelled tasks are excluded from the denominator — the seed has none, and the answer
   does not invent any.
3. Nothing was written anywhere.
