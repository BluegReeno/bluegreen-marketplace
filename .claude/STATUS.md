# STATUS — bluegreen-marketplace

Last updated: 2026-05-28

## Current Focus

Plugin `hal` v0.1.0 mergé. Étape 2 : supprimer `hal/agents/skills/hal-crm/` dans le repo `hal`.

## In Progress

_(rien)_

## Next Steps

### Étape 2 — PR `hal` (repo hal)

**Plan** : `hal/.agents/plans/remove-hal-crm-skill.md`
**Branch** : `chore/remove-hal-crm-skill`

Ce que ça fait :
- Supprime `hal/agents/skills/hal-crm/` (obsolète — tout passe par Cowork via bluegreen-marketplace)
- Met à jour `hal/CLAUDE.md` : pointer vers `bluegreen-marketplace/plugins/hal/scripts/obsidian/`
- `uv run pytest` doit passer

## Done (current sprint)

- [x] Embed hal-mcp in plugin via `.mcp.json` — removes custom connector friction at onboarding — 2026-05-27 ✅ tested & validated (Steeve onboarding)
- [x] Bump plugin to v0.6.3 (plugin.json + SKILL.md + marketplace.json) — 2026-05-27
- [x] Fix CLAUDE.md — source repo updated, release process corrected — 2026-05-27
- [x] Architecture hal plugin : décisions prises + 2 plans rédigés — 2026-05-28
  - Un plugin `hal`, deux skills (`/edifice` + `/hal`), un MCP `hal-mcp`
  - Versioning par composant (3 chiffres, PATCH par release, MINOR pour interface)
  - `plugins/hal/scripts/obsidian/` = source de vérité unique pour scripts vault I/O
  - `/hal` v0.1.0 → Obsidian ; v0.2.0 → Supabase (après migration)
- [x] hal plugin v0.1.0 — PR #3 mergée — 2026-05-28
  - `plugins/edifice-mission-report/` → `plugins/hal/`
  - Skill `/hal update` v0.1.0 (Obsidian vault) + `hal_update.py`
  - 8 scripts obsidian-crm bundlés dans `scripts/obsidian/`
  - README, CLAUDE.md, marketplace.json, versioning policy mis à jour

## Backlog

- [ ] hal-crm v0.2.0 — migration data layer `/hal` : Obsidian → Supabase via hal-mcp CRM tools (après migration Postgres hal)
