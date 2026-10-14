# Eval suite — generated, do not edit

Every file here but `results/` is written by `scripts/audit/stories_to_evals.py` in the hal repo,
from the story specs `scripts/audit/stories/*.yaml` and the sidecar `eval-cases.yaml`: one case
per transcribed story step (`<story>-<step>/case.yaml` + `graders/checklist.md`), the hal-mcp
server as an agent mock over the whole demo-data seed (`mocks/hal-mcp/_server.md`), `whoami`
fixed, the real `tools/list` (`_tools.json`). A state-B case or one with a default workspace
carries its own `mocks/`. Edit the spec or the sidecar in hal and regenerate.

Run, from this directory's parent (the marketplace root):

    claude plugin eval . --eval-dir evals --model opus --judge-model sonnet --no-publish \
        --trust-plugin --ablation none --json evals/results/last.json

Renaud's verdicts of 2026-10-14 (hal `docs/audit/migration-step3-block-2-gaps.md`, § Renaud's
verdicts): `--model opus` plays the assistant for any run a conclusion is drawn from — it is the
model Renaud's client uses, and on `sonnet` a skill named by its trigger phrase is loaded one time
in six (A6); `--judge-model sonnet` is the harness's judge, where the tool's default `haiku` fails
right answers three votes out of three (A5); the default three runs per case for a verdict,
`--runs 1 --model sonnet` to probe one case while writing it. The child has no Bash and no vault:
what a case proves is the skill's reading of the rows, its gates and its wording (L3 of the
roadmap); the hal story harness keeps L4 and L5 (A8). Mock noise is fixed by adopting a verified
run's recordings into `mocks/.replay/` (the run's `ADOPT.txt` says how — A2), by hand.
