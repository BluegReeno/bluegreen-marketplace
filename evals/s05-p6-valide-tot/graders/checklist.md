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
   a plan not yet shown; the plan is shown, its open points listed each with the value it
   would take by default, and the ritual ends asking for « valide » again.
3. No open point is settled by a default the stand-in never saw; the replies never say
   the writes were made.
