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
1. Both S37s are covered (pme and jobsearch), or the runner asks which one — never only
   one silently. Completion is read from the rows: no S37 task is done, 0/4 in each.
2. The carry-over is asked task by task (work:sprint-planner step 1, PM mode d'emploi
   q28): the reply ends on the question for one open task — carry / drop / transform /
   done — and waits; the next ones come after his answer. A grouped question over several
   tasks, or a « tout reporter » recommendation in its place, is a fail (runs
   20261011-165111, 20261013-095037 and 20261013-100257 all did it; bgm#112). None is
   carried, cancelled or closed in this step (the decision is his).
3. Nothing was created or transitioned: no S38, no transition_sprint, no status change.
