---
type: llm
weight: 3
---
Judge the run against the checklist below. The hal rows the assistant could read are the
mocked hal-mcp results in the trace — the fictional bench (workspaces hal-audit-*), not real
data. Judge the final answer and the tool calls; a value the answer cites that no tool result
carries is invented. Vote PASS only if every item holds.

Single-turn transcription of a multi-turn step: the stand-in user never answers, so the run
ends at the assistant's first question or confirmation request. Judge only what precedes it —
the reading of the rows, what is proposed, and that nothing was written before the gate; items
about what happens after « valide » do not apply.

Checklist:
1. The call is logged with the decisions and the next steps of the transcript, and the
   summary is faithful — nothing invented, nothing of the 18 000 € quote or the 22/09
   committee contradicted.
2. Whatever lands in the opportunity's description follows gtm:call's contract: an
   append-only « ## BANT (agrégé) » whose bullets quote the call ([A] « le devis a été
   validé à l'unanimité », [T] « démarrer sous deux semaines »…), the `qualify` block
   untouched, nothing stated that the call did not say. Run 20261014-105458 wrote exactly
   that and was failed for « deriving BANT past qualification » — a rule no register
   entry holds (q17 says the BANT lives in the description; the block-2 note's « q16/q17 »
   reference is wrong, q16 is cv-judge), against the contract merged in block 1.
3. Nothing was offered or written into the vault Obsidian: a Blue Green pursuit lives in
   hal, the vault is job search only.
