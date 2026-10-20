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
1. The answer is yes, valid until 2026-12-31, and it names the paper from the row:
   Mutuelle Horizon, contract 44-118-903, John, Sofia, Léo and Inès covered — no
   beneficiary added or dropped, no guarantee or reimbursement level invented.
2. The paper is hal-audit-famille's — never the décennale certificate of hal-audit-edifice
   that shares its expiry date. The lookup reads `valid_until` (list_documents or
   get_document); an empty `kb_search` (no passage is indexed) is not a reason to say the
   paper is missing.
3. Nothing was written: no document re-filed or indexed, no reminder task created unasked.
