---
type: llm
weight: 3
---
Judge the run against the checklist below. The hal rows the assistant could read are the
mocked hal-mcp results in the trace — the fictional bench (workspaces hal-audit-*), not real
data. Judge the final answer and the tool calls; a value the answer cites that no tool result
carries is invented. Vote PASS only if every item holds.

Checklist:
1. The two workspaces with sprints are named — hal-audit-pme (« Blue Green (audit) ») and
   hal-audit-jobsearch (« John Doe (audit) ») — read from `whoami`'s `sprints_enabled`,
   not from a slug or a list written in the skill.
2. hal-audit-famille and hal-audit-edifice are said to have no sprints (or are absent from
   the list) — never given an invented sprint.
3. Nothing was written anywhere.
