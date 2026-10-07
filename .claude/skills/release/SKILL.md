---
name: release
description: Release one plugin of bluegreen-marketplace with scripts/release.sh (version bump, marketplace entry, top-level counter, CHANGELOG, commit). Use when asked to release, bump, or publish a plugin version.
---

# Release a plugin

Releases are intentional and infrequent (~1-2/month), and stay a deliberate human act — CI only
enforces the invariant (`.github/workflows/ci.yml` runs `scripts/check_version_sync.sh` + tests on
every PR/push, so a broken version sync or a missing CHANGELOG entry fails the build).

`scripts/release.sh` performs the whole bump in one validated pass so a missed field can no longer
strand Claude Desktop clients on the old version (the top-level marketplace counter is what surfaces
the "Mettre à jour" button — see §Project Overview). It validates everything **before** writing, then:

1. bumps `plugin.json.version`,
2. bumps the matching marketplace plugin entry (kept identical),
3. bumps the marketplace **top-level** `version` (monotonic PATCH +1),
4. prepends a dated `## [<version>]` CHANGELOG entry,
5. runs `scripts/check_version_sync.sh` and aborts if it fails,
6. commits `chore(<plugin>): release v<version>` — **no push, no merge, no tag**.

```bash
# <plugin> <new-version> "<changelog line>"  (--mcp-version <v> also bumps .mcp.json)
bash scripts/release.sh pm 0.2.2 "fix sprint-planner date range"
git push        # the human pushes after reviewing the commit
```

It refuses (exit 1, clear message) on: missing args, unknown plugin, a version not strictly
greater than the current one, a dirty working tree, or a CHANGELOG that already lists the version.
A failed validation writes nothing. `.mcp.json` is left untouched unless `--mcp-version` is passed.

---
