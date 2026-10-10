# Changelog — knowledge

All notable changes to this plugin are documented here.

## Versioning convention

`0.MINOR.PATCH` (pre-1.0):
- **PATCH** (`0.x.Y+1`) — bugfix, optional field, internal improvement with no interface impact
- **MINOR** (`0.X+1.0`) — interface change: new required field, renamed command, observable behaviour change

Requires the `hal` plugin, which carries the `hal-mcp` connector this plugin's skills call.

---

## [0.1.0] — 2026-10-09 — created: `ingest` and `file` (hal audit q29, q35, q41)

The plugin of the Documents and Knowledge pillars (q39). Two skills, the only gestures of the
pillar that chain several tools or carry a judgement; retrieving, reading, what expires and querying
stay named tools in the sentence (`list_documents`, `get_document`, `get_document_link`, `kb_search`).

- `ingest` — index what is worth recalling: the catch-up of knowledge-flagged documents and call
  transcripts (`--pending`), or one source from a file (course, video transcript, document). Runs
  the hal checkout's `scripts/kb/ingest.py` on the Mac and refuses by name anywhere else.
- `file` — file a paper: extract the facts, choose workspace, domain, kind and slug, answer the
  « fiche or knowledge base » question, reference the file in the workspace's storage
  (`storage {provider, uri}`), write the fiche with `save_document`.
