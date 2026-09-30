# Changelog — docs

All notable changes to this plugin are documented here.

## Versioning convention

`0.MINOR.PATCH` (pre-1.0):
- **PATCH** (`0.x.Y+1`) — bugfix, optional field, internal improvement with no interface impact
- **MINOR** (`0.X+1.0`) — interface change: new required field, renamed command, observable behaviour change

`proposal` optionally reads hal through the `hal` plugin's connector; `brand` and `study-report` need nothing but pandoc.

---

## [0.1.0] — 2026-09-30 — First release: brand identity, Markdown → branded .docx, study report and proposal

- `brand` — `brand.yaml` is the single source of the Blue Green identity (colours, Poppins,
  legal notice from the 2026-06-22 Kbis, contact) and `assets/` carries logo, badge, cover and
  banner. `scripts/md2docx.py` renders Markdown to .docx: pandoc with a reference document built
  from `brand.yaml` on every run, then python-docx post-processing (cover page, TOC page break,
  full-width tables keeping their Markdown proportions, OOXML `pPr` ordering Word requires).
  Runs with `uv run --with python-docx --with pyyaml`; `--with pypandoc_binary` when pandoc is missing.
- `study-report` — structure and writing rules of a study report (`type: report`: cover + TOC).
- `proposal` — structure and pricing conventions of a commercial proposal (`type: proposal`:
  Blue Green presentation page), with optional hal context (opportunity, contact tone).
