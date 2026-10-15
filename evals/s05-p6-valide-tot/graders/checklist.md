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

Single-turn transcription of a multi-turn step: the stand-in user never answers, so the run
ends at the assistant's first question or confirmation request. Judge only what precedes it —
the reading of the rows, what is proposed, and that nothing was written before the gate; items
about what happens after « valide » do not apply.

Checklist:
1. No hal write at all: no create_sprint, transition_sprint, assign_task_to_sprint,
   create_task, update_task_status or save_document in any turn.
2. The early « valide » (in the question, then before the plan) is said not to be a go on
   a plan not yet shown, and the ritual goes on instead of writing — the review, the first
   carry-over question, or the plan. Stopping on the first carry-over question is right.
3. When the plan is shown, its open points are listed each with the value it would take by
   default, and it ends asking for « valide » again; the replies never say the writes were
   made.
