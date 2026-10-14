---
type: llm
weight: 3
---
Judge the run against the checklist below. The hal rows the assistant could read are the
mocked hal-mcp results in the trace — the fictional bench (workspaces hal-audit-*), not real
data. Judge the final answer and the tool calls; a value the answer cites that no tool result
carries is invented. Vote PASS only if every item holds.

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
