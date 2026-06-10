# Archon roadmap — workspace resolution, vault, multi-tenant

Last updated: 2026-06-10

Cross-repo sequential plan for the `hal` plugin work. Each **run** = one archon
`brief→plan→PR` pipeline (reference: vault run = ~18 min plan + ~25 min PR).
Launch each run from a **fresh session** in the indicated repo.

> Briefs are already written and committed. This file is the orchestration order only.

---

## Pending inventory

### `bluegreen-marketplace`
| Item | Brief / artifact | State |
|------|------------------|-------|
| `/hal` skill → `whoami` resolution | `docs/brief-hal-whoami-skill-migration.md` | ready, blocked on hal whoami deploy |
| `/hal tasks` (PR #11) | open PR + `.claude/plans/hal-tasks-skill.md` | open, env-var approach to rework |
| `/hal vault` skill | `docs/brief-hal-vault-skill.md` | ready, backend live (hal-mcp v35) |

### `hal`
| Item | Brief / artifact | State |
|------|------------------|-------|
| `whoami` tool + default workspace | `docs/brief-hal-whoami-workspace-resolution.md` | ready — **foundation** |
| Vault seeding smoke test | STATUS "next step" | not briefed — manual usage session |

### `hal` backlog — NOT yet briefed (design pass required before archon)
- **Multi-tenant shared projects** — several companies on one project (lead + subcontractor),
  RLS compatibility. Extends `whoami`. This is the VESTA / IC subcontractor case.
- **edifice ↔ hal project semantics** — project (signed contract DEV-XXX) vs mission (field
  activity), meaning of "en cours" status, opportunity→project transition.
- **End-to-end CRM workflow** — real VESTA demo: opportunity → field visit → devis generation.

---

## Sequence

### Phase 1 — Workspace resolution chain (closes dangling PR #11)

- [ ] **Run 1 · archon · repo `hal`** — brief `docs/brief-hal-whoami-workspace-resolution.md`
      → PR → merge → **deploy hal-mcp**. Foundation; must land first.
      - Adds `is_default` on `workspace_members` + `whoami` tool (identity from
        `verifyAuth` `userClaims` — one-line `authInfo.extra` change, no RPC).
- [ ] **Run 2 · archon · repo `bluegreen-marketplace`** — brief
      `docs/brief-hal-whoami-skill-migration.md` → PR. Reworks PR #11 (drop env var, keep
      `/hal tasks`), merge as **v0.7.0**. **Depends on Run 1 deployed to prod.**

### Phase 2 — Vault (independent — backend already live, can run parallel to Phase 1)

- [ ] **Run 3 · archon · repo `bluegreen-marketplace`** — brief
      `docs/brief-hal-vault-skill.md` → PR → merge (`/hal vault`).
- [ ] **Manual session** — vault seeding for Blue Green (KBIS, statuts, RIB, CNI, brand kit,
      tone of voice) = accounting-scenario smoke test. Not archon.

### Phase 3 — Backlog (write briefs first, then archon)

- [ ] **Run 4 · design session** (manual or archon brief-authoring) → produce two briefs:
      - multi-tenant shared projects (builds on the `whoami` foundation)
      - edifice↔project semantics + CRM VESTA workflow
- [ ] **Run 5+ · archon** — `brief→plan→PR` on each brief once written.

**Recommended order:** Phase 1 → Phase 2 → Phase 3.
Phase 2 has no dependency on Phase 1 (vault backend already in prod) — interleave it earlier if
the vault is more urgent than the workspace-resolution debt.

---

## Dependency notes

- Run 2 **must** wait for Run 1's hal-mcp deploy (the skill calls the deployed `whoami` tool).
- PR #11 stays **open** until Run 2 reworks its branch — do not merge it with the env-var approach.
- Phase 3's multi-tenant brief should be written **after** Phase 1, so it builds on the shipped
  `whoami` / `is_default` foundation rather than re-deciding it.
