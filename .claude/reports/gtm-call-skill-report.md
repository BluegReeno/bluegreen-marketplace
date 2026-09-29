# Implementation Report — hal#192 phase B: `gtm:call`, `/crm log` retired

**Plan**: `bluegreen-marketplace/.claude/worktrees/piv-plan-implementation-34dddd/.claude/plans/gtm-call-skill.md` (phase B only; H1 shipped in hal PR #228, merged 2026-09-29)
**Branch**: `feat/hal-192-gtm-call`   **Status**: COMPLETE (code) — Level-4 manual runs pending (Renaud)

## Summary
The `gtm` plugin gains `gtm:call`, the one skill that turns a call — client or job interview —
into hal knowledge: opportunity or project resolved with evidence, Granola or pasted transcript,
corrections from hal's own spellings, three-profile signal extraction by the host model, Renaud's
read (feeling, reflection, keep/reject of each `could_do_better`), interaction + `call_analysis`
document written through hal's `scripts/kb/call_analysis.py render`, then `ingest.py --pending`.
It is hal-only and knows nothing of the vault; `jobsearch:log-cr` will call it once with a JSON
argument (phase R). `/crm log` is retired; `/crm log update` stays and now finds interaction ids
through `list_interactions`.

## Tasks completed
- B.1 → `plugins/gtm/skills/call/SKILL.md` (CREATE) — 10 sections + constraints, French prose.
- B.2 → `plugins/gtm/commands/call.md` (CREATE) — thin: `Skill("gtm:call")`, stop on `Unknown skill`.
- B.3 → `plugins/gtm/skills/crm/SKILL.md`, `plugins/gtm/commands/crm.md` (UPDATE) — `/crm log`
  section removed, description and `argument-hint` trimmed, `log update` resolves ids via
  `list_interactions`, `allowed-tools`: `log_interaction` → `list_interactions`, scope + out-of-scope
  point at `/call`.
- B.4 → `tests/test_gtm_call_skill.py` (CREATE) — 13 tests (unittest, as CI runs it).
- B.5 → `CLAUDE.md`, `README.md`, `docs/INSTALL.md`, `docs/skills-mcp-guide.md`, `.claude/STATUS.md` (UPDATE).
- B.6 → `scripts/release.sh gtm 0.3.0` (MINOR: command added, one removed).

## Tests added
`tests/test_gtm_call_skill.py`: `name: call`; no `disable-model-invocation`; `allowed-tools` cover
`whoami`, `list_projects`, `list_interactions`, `log_interaction`, `update_interaction`,
`save_document`, `Bash(uv *)`, `Bash(test *)`, and contain no `Skill(`; description names `log-cr`;
no email literal; the renderer is the hal CLI (`prompts`, `render`, `ingest.py`); every
`CALL_SOURCE_KEYS` key documented; `reflection` is a string under `## Réflexion`; `commands/call.md`
delegates to `gtm:call` and stops on `Unknown skill`; `/crm log` absent from `plugins/gtm` except
`log update` and the retirement note; `crm` no longer holds `log_interaction`.
Result: 13 passed; full suite `python3 -m unittest discover -s tests` → 101 tests OK (6 skipped, as before).

## Validation results
- `bash scripts/check_version_sync.sh` — OK (4 plugins).
- `python3 -m unittest discover -s tests` — 101 OK.
- B.2 grep (`Skill("gtm:call"` in `commands/call.md`) — 1 match.
- B.3 grep (no `/crm log` outside `log update` in `crm` files) — clean.
- Contract smoke against hal `main` (`10846dd`): the `call.json` shape written in SKILL.md § 8
  rendered with exit 0 — `slug call-analysis-<id>`, `title` = H1, `issued_date` in Paris,
  off-vocabulary `lever` coerced to `other` and counted, `## Réflexion` present, anchoring 1.0.
  `prompts` returns `call`, `questions_asked`, `could_do_better`, `vocabularies` (incl. `call.polarity`/`bant`).

## Deviations from the plan
1. **`reflection` is a string rendered under `## Réflexion`**, not `reflection.fit` under
   `## Lecture Renaud` — follows H1's deviation 1 (`ingest.py` reads a string). The skill asks
   Renaud's free read for a client call and passes it as one string; omitted for an interview.
2. **`source` is sent complete, null when unknown**, and `occurred_at` always carries a time and an
   offset (noon Europe/Paris when no start time is known) — H1 deviations 4; the plan's
   "date only when neither" is refused by `render`.
3. **All writes happen in § 8 after one confirmation.** The plan had § 6 write the BANT/Appels
   bullets before Renaud's read (§ 7) and the write plan (§ 8). § 6 now *prepares* and shows the
   bullets and the stage/task proposals; `update_project`, `update_project_stage`, `create_task`
   run in § 8 with the interaction and the document. One confirmation gates every write — the crm
   guardrail « confirmer avant toute écriture ambiguë », and no half-state if Renaud stops at § 7.
4. **Empty `signals` after rejection → no analysis, ingestion still runs**: `render` refuses empty
   signals; the interaction (with transcript) is written and is itself a pending source.
5. **Test file is `unittest`, not pytest-only** — CI runs `python3 -m unittest discover -s tests`;
   pytest collects it as well. The `allowed-tools` tokenizer handles `Bash(uv *)` (holds a space).
6. **H1.5 not performed** — hal's rendering stayed byte-identical (H1 report), nothing to re-index.
7. `docs/skills-mcp-guide.md` gained a third option (delegate with `Skill(...)`) so the rule
   "commands are self-contained" names its one exception instead of contradicting `call.md`.

## Issues encountered
- The plan's grep `/crm log\`` also matches a sentence recording the retirement; reworded to
  « la sous-commande `crm log` … retirée ». The test allows a `/crm log` mention only on a line
  containing « retiré ».
- Granola and Google Calendar tool names (`mcp__Granola__*`, `mcp__claude_ai_Google_Calendar__*`)
  are taken from `log-cr` and `book-appointment`; nothing in CI checks that they resolve (known
  trap, STATUS.md). Level 4 will.

## Level 4 — Renaud's manual runs (prepared, not simulated)
1. Client call, past — `/call l'appel d'aujourd'hui avec Elise` on the Mister IA call of
   2026-09-28 16:15 (Granola `6d3f2d94-4e18-4516-a284-8648d673355e`): expect domain → « Mister IA »,
   « no active project » → « entreprise seulement » / « nouvelle opportunité », calendar read with
   no question, nothing in the vault, chunks + anchoring reported. (AC2, AC3, AC4, D8, D9)
2. Same flow with the transcript pasted. (AC3)
3. « Alstom — Deon & François » → proposal = Cognyx with evidence. (AC2)
4. Re-run 1 → same interaction updated, same slug, no duplicate. (AC7)
5. Cowork: `/call` stops at pre-flight (b) with the Mac-only message, writes nothing. (AC1)
6. `kb_search` on a phrase of the new call returns its passages.
7. OSS Ventures via `/log-cr` and the `gtm`-absent `Unknown skill` stop wait for phase R.
