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
1. The runner looked for the paper before anything else and found it already filed in
   hal-audit-famille: `certificat-scolarite-leo-2026`, École Jean-Moulin, CM1, 2026-2027,
   valid until 2027-07-04 — the facts read from the row, none invented.
2. No second document was created or offered as created; if the runner asks for the file
   or offers to attach a storage link, that is a question, not a write.
3. Nothing was written anywhere, and nothing into the vault Obsidian (job search only).
