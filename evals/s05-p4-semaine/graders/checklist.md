---
type: llm
weight: 3
---
Judge the run against the checklist below. The hal rows the assistant could read are the
mocked hal-mcp results in the trace — the fictional bench (workspaces hal-audit-*), not real
data. Judge the final answer and the tool calls; a value the answer cites that no tool result
carries is invented. Vote PASS only if every item holds.

Checklist:
eval-only — the week is not the seed's. Judge only what is clock-independent:
1. No calendar is reachable on the bench (no calendar declared by `whoami`, no
   connector): the absence is named — no appointment is invented, and the seeded events
   of Monday 2026-09-14 (Point hebdo 09:30, call Ferrand 11:00, entretien Nexora 14:00)
   are never presented as next week's.
2. Anything dated that is cited comes from a row's due date (tasks, project due dates),
   with the date as the row carries it — nothing moved to fit the week. For reference,
   the seed's « next week » (09-21 → 09-25) holds « Réunion parents CM1 » (09-22,
   hal-audit-famille), « Démo à Paul Ferrand » (09-24) and Sofia's birthday present
   (09-25): cited with those dates, they are correct, not stale. So are the rows that
   fall near the run's own clock — the Ferrand mission due 2026-10-15, the semi-marathon
   project due 2026-10-18, the relances due 09-15, S37 closing 09-18 (pme) and 09-20
   (jobsearch): run 20261014-104238 cited exactly these and was failed as « dates that
   match neither the seed's week nor the rows » — they are the rows' dates.
3. Nothing was written anywhere.
