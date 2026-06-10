# Brief — `hal` skill: workspace resolution via `whoami` (remove env var)

> **Repo**: `bluegreen-marketplace` · **Plugin**: `hal` · **Skill**: `hal`
> **Depends on**: the `whoami` tool shipped in the `hal` repo
> (`hal/docs/brief-hal-whoami-workspace-resolution.md`). **Do not start until `whoami` is live in
> prod** — this skill change consumes its output. Sequential.

---

## 1. Goal

Make every `/hal` command resolve its target workspace from the **authenticated user** (via the
new `whoami` MCP tool), not from client-side config. Remove the `HAL_DEFAULT_WORKSPACE` env var
entirely. Keep the per-command explicit-override (`/hal tasks ic`) exactly as is.

This replaces the env-var resolution introduced by **PR #11** (`/hal tasks` + NL task intents).
PR #11's task features are good and stay — only its *workspace-resolution mechanism* is wrong and
must be swapped. See §6.

## 2. Why

The env-var approach has two defects (full analysis in the `hal` brief §1):

1. **Hardcoded `blue-green` pre-flight breaks non-`blue-green` users.** RLS scopes
   `halcrm_workspaces` to the caller's memberships, so an IC-only user's `list_stages(blue-green)`
   probe returns "not found" and the skill reports the connector as down. Defeats the multi-tenant
   purpose of the very change that introduced it.
2. **`HAL_DEFAULT_WORKSPACE` is unreliable on the target.** macOS GUI apps (Claude Desktop) don't
   inherit `~/.zshrc` exports; Cowork env vars are ephemeral. Never verified live.

The `whoami` tool fixes both: it serves the default from Supabase and doubles as the connectivity
probe.

## 3. New resolution model

`whoami` (no input) returns:

```
{ user_email, workspaces: [{workspace_slug, role, is_default}], default_workspace_slug }
```

### 3.1 Pre-flight (replaces the hardcoded `list_stages` probe)

- Call `whoami`.
  - **Success** → the connector is up; cache `default_workspace_slug` + `user_email` for the
    rest of the command.
  - **Failure** (tool unavailable / refused / timeout) → keep the existing "MCP unavailable"
    message and stop.
- Remove the `list_stages(workspace_slug: "blue-green")` pre-flight and its "intentional
  hardcode" note.

### 3.2 Workspace resolution (applies to `list`, `tasks`, `update`)

1. **Explicit arg** (`/hal tasks ic`, `/hal list blue-green`) → use that slug. Shorthand
   `ic` → `ic-ingenieurs-conseils`. RLS validates membership; if the user is not a member the MCP
   tool returns a natural error — surface it verbatim.
2. **No arg** → use `default_workspace_slug` from `whoami`.
   - If `default_workspace_slug` is `null` (user in 0 workspaces, or several with no flag) →
     show the `workspaces` list and ask which to use (or tell them to contact their admin if the
     list is empty). **Do not** fall back to any hardcoded slug.

### 3.3 `--mine`

Use `user_email` from `whoami` directly — drop the "ask the user for their email" step.

## 4. Concrete edits

- `plugins/hal/skills/hal/SKILL.md`
  - Bump `version:` (PATCH or MINOR — interface of resolution changes; recommend **MINOR**).
  - Replace the `## Workspace resolution` block with the `whoami`-based model (§3.2).
  - Replace the `## Pre-flight` section with the `whoami` probe (§3.1).
  - `/hal tasks` `--mine`: source email from `whoami` (§3.3).
  - Remove every reference to `HAL_DEFAULT_WORKSPACE` and the hardcoded `blue-green`.
- `plugins/hal/commands/hal.md`
  - Replace the env-var resolution rule with the `whoami` rule (self-contained command file —
    keep parity with SKILL.md).
- `plugins/hal/README.md`
  - **Remove** the "Set your default workspace (required)" env-var section. New onboarding:
    your admin adds you to your workspace(s) in Supabase (and flags your default if you belong to
    several). Zero client-side config. Mention the per-command override (`/hal tasks ic`).
- Version bumps: `plugin.json` + `marketplace.json` (kept in sync), `CHANGELOG.md` entry. Confirm
  the exact numbers against whatever PR #11 lands as (see §6).

## 5. Acceptance criteria

- [ ] No occurrence of `HAL_DEFAULT_WORKSPACE` anywhere under `plugins/hal/`.
- [ ] No hardcoded `blue-green` in pre-flight or resolution (search `grep -rn "blue-green"`; only
      legitimate doc/example mentions remain).
- [ ] Pre-flight is a `whoami` call; failure path unchanged.
- [ ] No-arg `/hal list` / `/hal tasks` / `/hal update` use `default_workspace_slug`.
- [ ] Explicit arg overrides; non-member arg surfaces the MCP error verbatim.
- [ ] `default_workspace_slug == null` → skill asks, never falls back to a hardcoded slug.
- [ ] `--mine` uses `whoami.user_email`.
- [ ] README env-var section removed; onboarding reflects Supabase-served default.
- [ ] plugin.json === marketplace.json version; CHANGELOG entry added.
- [ ] Smoke-tested live from Claude Desktop: `/hal tasks` with no arg resolves to the default and
      lists tasks (this is the scenario the env var could not guarantee).

## 6. Relationship to PR #11

PR #11 (`feat(hal): v0.7.0 — /hal tasks + NL task intents`) is **open, not merged**. It bundles:

- (a) `/hal tasks` kanban + NL task/sprint intents — **good, keep**;
- (b) workspace resolution via `HAL_DEFAULT_WORKSPACE` — **wrong, replace per this brief**.

Recommendation: **hold PR #11**. Once `whoami` is live, rework the same branch — swap (b) for the
`whoami` model — then merge as a single `v0.7.0`. Avoids shipping the env var and immediately
ripping it out. If #11 has already merged by the time this runs, this becomes a follow-up patch
release.
