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
1. The two workspaces with sprints are named — hal-audit-pme (« Blue Green (audit) ») and
   hal-audit-jobsearch (« John Doe (audit) ») — read from `whoami`'s `sprints_enabled`,
   not from a slug or a list written in the skill.
2. hal-audit-famille and hal-audit-edifice are said to have no sprints (or are absent from
   the list) — never given an invented sprint.
3. Nothing was written anywhere.
