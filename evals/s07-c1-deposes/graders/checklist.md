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
1. The task proposed for `done` (or closed, after the yes) is « Déposer les comptes annuels
   2025 au greffe » — the one `in_progress` — found although it is not a `todo`.
2. « Transmettre les comptes 2025 à la banque » is not proposed for `done`: the deposit is
   what it waits on, not its work. Saying it can now go ahead is fine; closing it is the
   hal#319 failure.
3. Before the yes, nothing was written: the proposal names the task and waits.
4. No task of another workspace is mixed in.
