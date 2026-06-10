# Brief — `/hal vault` skill (document vault)

> **Repo**: `bluegreen-marketplace` · **Plugin**: `hal` (currently v0.6.0)
> **To be developed in a separate session, from this repo.** Self-contained — you do not need
> to open the `hal` repo to implement this; the MCP tool contracts are reproduced below.
> **Backend status**: live in prod. hal-mcp v35, Supabase `zgkvbjqlvebttbnkklpo`, workspace
> `blue-green` already seeded with 5 real documents (see §9) — you have a known-good state to
> test against.

---

## 1. Goal

Add a `vault` sub-command to the existing `hal` skill so a user can, from Claude Desktop /
Cowork / Code, **file their firm's administrative documents into the hal-mcp document vault and
recall them in natural language** — without ever making the model read a binary it already
holds.

The MCP server already does the storage, the upsert, the signed URLs, the sensitive-TTL. What it
does **not** do, and what this skill must add, is the **method**: stable slugs, domain
classification, facts extraction at ingestion, **idempotent pre-flight (don't re-do work already
in the vault)**, and the target checklist that drives a complete seeding.

This mirrors how `/hal update` adds CRM method on top of the raw CRM tools.

---

## 2. Where it lives

Same pattern as the other `/hal` sub-commands (`list`, `update`, `devis`):

- Command surface: `plugins/hal/commands/hal.md` — add a `vault` branch.
- Skill logic: `plugins/hal/skills/hal/SKILL.md` — add a `## /hal vault` section.
- **Workspace**: default `blue-green`, hard-coded like the rest of the skill. Accept
  `[workspace]` / `--workspace SLUG` to override (e.g. `ic-ingenieurs-conseils`).
- No new Python script needed — this is pure NL → MCP, plus `curl` PUT for binary upload (same
  as `/hal update` is scriptless). Bump the plugin to **0.7.0** and add a CHANGELOG entry.

---

## 3. The 4 MCP vault tools (contracts — reproduced so you don't need the hal repo)

All take `workspace_slug` (string, required).

### `save_document` — create/update a fiche (upsert on `workspace_slug` + `slug`)
Required: `slug`, `domain`, `kind`, `title`.
Optional: `person_name`, `content_md`, `facts` (object), `issued_date` (YYYY-MM-DD),
`valid_until` (YYYY-MM-DD), `sensitive` (bool), `filename`, `mime_type`.
- Provide `filename` **and** `mime_type` together to attach a binary → the response contains
  `upload.upload_url` (signed, TTL 7200s) + a ready-made `curl` line. `filename` must include an
  extension. `mime_type` without `filename` (or vice-versa) → error.
- A fiche must have **either** `content_md` **or** a file (DB CHECK) — a metadata-only fiche
  with neither is rejected.
- Returns the persisted `document` row + (when a file was declared) the `upload` block.

### `list_documents` — browse
Optional filters: `domain`, `kind`, `person_name`, `expiring_before` (YYYY-MM-DD, includes
already-expired), `summary_only` (bool).
- `summary_only: true` → manifest mode: `{ total, by_domain: {…counts}, expiring_within_30d: [...] }`.
  **Cannot be combined with filters.** Use this first when exploring.
- Without `summary_only` → array of compact index lines (`slug, domain, kind, title,
  person_name, valid_until, has_file, sensitive`). No `facts`, no `content_md`.

### `get_document` — full fiche for one slug
Args: `slug`. Returns metadata + `facts` + `content_md`. **Answers most questions without the
binary.** This is the default recall path.

### `get_document_file` — short-lived signed download URL
Args: `slug`. Returns `{ download_url, expires_in, sensitive, mime_type }`. TTL **3600s**, or
**300s + a `warning`** when `sensitive: true`. Only call this when the human needs the actual
file — never to let the model read content it can get from `get_document`.

---

## 4. Fixed taxonomy — the 10 domains (decided server-side, NOT by the agent)

`domain` is a **locked enum** (DB CHECK + server validation). The agent picks one of these; it
cannot invent a domain (an invalid value returns an error listing all 10):

```
legal · fiscal · banking · hr · insurance · assets · suppliers · brand · product · knowledge
```

`kind` is **free-form** — the agent's fine label. Conventions used so far:

| domain | kind examples |
|---|---|
| legal | `kbis`, `statuts`, `immatriculation` |
| fiscal | `memento_fiscal`, `comptes_annuels`, `liasse`, `is` |
| banking | `rib` |
| hr | `id_card`, `carte_vitale`, `cv` |
| insurance | `rc_pro`, `attestation` |
| assets | `carte_grise` |
| suppliers | `contact_fiche`, `contrat` |
| brand | `logo`, `font`, `tone_of_voice`, `guidelines` |
| product | `offer`, `brochure` |
| knowledge | `report`, `note` |

**Rule for the skill**: if a document fits no domain, do NOT force it — surface that the taxonomy
may need a new domain (which is a `hal` repo code change, not a runtime decision). Don't silently
mis-file.

---

## 5. Slug conventions (this is what guarantees no duplicates)

Uniqueness is enforced by the DB on `(workspace_slug, slug)` and `save_document` upserts on it.
**There is no content-level dedup** (no hash). So duplicate-avoidance lives entirely in slug
discipline. Rules:

- **Stable, human-readable, kebab-case.** `kbis-2026-03`, not `kbis_25032026` or a UUID.
- **Version-dated where a document type recurs**: KBIS → `kbis-YYYY-MM` (month of issue), so
  successive KBIS stack without colliding and the current one is findable.
- **Singletons stay slug-stable**: `rib-pro`, `statuts`, `tone-of-voice`, `logo-hero`,
  `cni-<firstname>`, `memento-fiscal`, `carte-grise-pro`.
- **Per-person HR docs** carry `person_name` AND a name in the slug: `cni-renaud`.

---

## 6. The idempotence pre-flight — THE core value of this skill

`save_document` overwrites blindly and the agent pays the binary-read + facts-extraction cost
**before** the call. So re-seeding without a check re-pays for nothing. Every seed item MUST run:

```
For each file to seed:
  1. Compute the stable slug (per §5).
  2. get_document(slug):
       - exists AND current (same version, valid_until not stale) → SKIP.
         Do NOT read the binary, do NOT re-extract facts. Report "déjà à jour".
       - exists but obsolete (newer issue date, changed valid_until, new file) → UPDATE
         (re-extract, save_document, re-upload).
       - absent → read the binary, extract facts, save_document (+ curl upload if binary).
```

State this loop explicitly in the SKILL. It is the difference between a useful skill and a
token-burning one.

---

## 7. Sub-commands to implement

### `/hal vault seed [path] [--workspace SLUG] [--dry-run]`
Ingest documents from a local folder (default: ask the user for the path; the reference seed set
lives at `hal/examples/seed-bg/`).
- Walk the folder, map each file to `{slug, domain, kind, sensitive, valid_until, facts}` using
  §4–§5 and the checklist §8.
- Run the §6 pre-flight per item.
- For each non-skipped item: read the binary to extract `facts` (pay tokens once), call
  `save_document`, then `curl -X PUT` the binary to the returned `upload_url` with the declared
  `mime_type`. Verify HTTP 200.
- **Facts minima per kind** (a fiche without these is a failed extraction):
  - `kbis` → `siren`, `greffe`, `forme_juridique`, `date_immatriculation`; `valid_until` =
    **issue date + 3 months**.
  - `id_card` → `document_number`, `date_of_birth`, expiry → `valid_until`; `sensitive: true`,
    `person_name`.
  - `rib` → `iban`, `bic`, `bank`; `sensitive: true`.
  - `statuts` → `forme`, `capital`, signature date.
  - `carte_grise` → plate, vehicle, holder.
  - `memento_fiscal` → TVA number, régime, SIE.
  - `contact_fiche` (e.g. former accountant) → name, email, phone, address in `facts` + `content_md`.
- `--dry-run` → print the planned `save_document` calls (slug/domain/kind/facts) + which items
  would SKIP/UPDATE/CREATE, without writing.
- One `save_document` per item. Never batch a binary into `content_md`.

### `/hal vault list [--workspace SLUG]`
Call `list_documents summary_only=true` first → show `by_domain` counts + an
`⚠️ expiring within 30 days` section. Then optionally the compact index. Never dump `facts`.

### `/hal vault get <query> [--workspace SLUG]`
Resolve the user's NL query to a slug (via `list_documents`), then `get_document`. Answer from
`facts`/`content_md`. Only call `get_document_file` if the user explicitly wants the file itself;
for `sensitive` docs, **confirm before surfacing the URL** and note the 300s TTL.

### `/hal vault dossier <description> [--workspace SLUG]` — the flagship recall
Given a request like *"dossier comptable: KBIS < 3 mois, statuts, RIB, CNI, carte grise, mémento
fiscal, coordonnées ancien comptable"*:
1. Map the request to expected `(domain, kind)` pairs.
2. `list_documents` + `get_document` per match — **no `get_document_file`, no binary read**.
3. Produce a table: ✅ present (with the key facts) vs ❌ missing (explicit, listed as blocking).
4. **Flag staleness loudly**: any doc whose `valid_until` is past — or, for a KBIS, within ~15
   days of the 3-month line — is surfaced as "à renouveler", never handed over silently.

---

## 8. Target checklist — Blue Green accountant dossier (drives a complete seed)

The acceptance scenario (§10) needs these. Use it as the seeding target for `blue-green`:

| slug | domain | kind | sensitive | facts to extract |
|---|---|---|---|---|
| `kbis-YYYY-MM` | legal | kbis | no | siren, greffe, forme, valid_until = issue + 3 mo |
| `statuts` | legal | statuts | no | forme, capital, signature date |
| `rib-pro` | banking | rib | **yes** | iban, bic, bank |
| `cni-renaud` | hr | id_card | **yes** | document_number, dob, expiry → valid_until |
| `carte-grise-pro` | assets | carte_grise | no | plate, vehicle, holder |
| `memento-fiscal` | fiscal | memento_fiscal | no | TVA number, régime, SIE |
| `former-accountant` | suppliers | contact_fiche | no | name, email, phone, address |
| `tone-of-voice` | brand | tone_of_voice | no | (content_md, no binary) |
| `logo-hero` | brand | logo | no | format, variants |

(`hal/docs/vault-seeding-blue-green.md` is the original runbook; this brief supersedes its
operational detail but the checklist is consistent with it.)

---

## 9. Known-good prod state (test fixtures already in `blue-green`)

A manual test (2026-06-10) already seeded 5 real documents you can validate against:

| slug | domain | kind | sensitive | valid_until |
|---|---|---|---|---|
| `kbis-2026-03` | legal | kbis | no | 2026-06-25 |
| `cni-renaud` | hr | id_card | yes | 2032-10-19 |
| `rib-pro` | banking | rib | yes | — |
| `logo-hero` | brand | logo | no | — |
| `tone-of-voice` | brand | tone_of_voice | no | — |

So: `/hal vault list` must show `legal 1 · hr 1 · banking 1 · brand 2` and flag `kbis-2026-03` as
expiring within 30 days. A correct `seed` re-run over `hal/examples/seed-bg/` must **SKIP all
five** (idempotence), not re-create them.

---

## 10. Acceptance criteria

The skill is done when, from a fresh Cowork session with hal-mcp connected:

1. **Seed is idempotent** — re-running `/hal vault seed` over an already-seeded set reads no
   binaries and reports every item as SKIP/déjà à jour.
2. **A new file is ingested correctly** — facts extracted, correct domain/kind/slug, binary
   uploaded (HTTP 200), `sensitive` set on RIB/CNI.
3. **`/hal vault dossier "dossier comptable …"` resolves from facts/fiches only** — no
   `get_document_file`, no binary read by the model.
4. **Missing pieces are listed explicitly** as blocking (not silently omitted).
5. **Stale documents are flagged** — an expired or about-to-cross-3-months KBIS is surfaced as "à
   renouveler", not handed over.
6. **Sensitive handling** — `get_document_file` on RIB/CNI returns the 300s warning and the skill
   confirms before sharing the URL.

When 1–6 pass, the document-vault product loop is closed end-to-end (the criterion of
`hal/docs/features/phase-X-document-vault-plan.md`).

---

## 11. Guardrails (consistent with the existing `hal` skill)

- Pre-flight `list_stages`/`list_documents` to confirm the connector is live; if hal-mcp is
  unreachable, surface the reconnection instruction (GUI only, no terminal) like the rest of the skill.
- Never auto-overwrite a fiche that exists and is current — SKIP or ask.
- `--dry-run` prints the MCP plan without writing.
- Output format per write: `✅ [slug] → save_document (domain/kind)` ; on failure
  `❌ [slug] → [error]`, surfaced immediately, no silent retry.
- Sensitive URLs are confirmed with the user before being shared outside the conversation.
