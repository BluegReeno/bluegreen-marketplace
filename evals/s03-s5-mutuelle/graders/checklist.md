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
1. The answer is yes, valid until 2026-12-31, and it names the paper from the row:
   Mutuelle Horizon, contract 44-118-903, John, Sofia, Léo and Inès covered — no
   beneficiary added or dropped, no guarantee or reimbursement level invented.
2. The paper is hal-audit-famille's — never the décennale certificate of hal-audit-edifice
   that shares its expiry date. The lookup reads `valid_until` (list_documents or
   get_document); an empty `kb_search` (no passage is indexed) is not a reason to say the
   paper is missing.
3. Nothing was written: no document re-filed or indexed, no reminder task created unasked.
