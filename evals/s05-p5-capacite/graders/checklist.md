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
1. The hours, the fixed blocks and the margin are looked up in hal (the `memory` and
   `soul` documents of the two sprinted workspaces) and said absent — the bench seeds
   none. No capacity is produced from hours the base does not hold: a « 35 h » of
   working time the runner supplies itself is a fail, and so is a capacity computed from
   a hypothesis Renaud has not confirmed. A margin the runner proposes and asks about
   (« je propose 20 % si tu n'as pas de préférence ») is the skill's own step — « celle
   de `memory`, sinon en proposer une et demander » — not an invented figure: eval runs
   2026-10-14T15-51-21 and the preamble re-run were failed on it, sonnet judge 3 / 3,
   against the skill's text. The hours are asked once, and recording them in `memory`
   is offered.
2. No block comes from the skill itself: no « réunion IC le lundi », no job-search slot
   at 08:30 (bgm#100, q09).
3. The missing calendar is named, not filled with invented meetings to subtract.
4. Nothing was written anywhere.
