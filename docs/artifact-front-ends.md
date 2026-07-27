# Artifact front-ends

How rich (React/Tailwind) front-ends are built here and shipped as part of the `hal` plugin.

This repo is both a **build environment** (`ui/`) and a **distribution channel**
(`plugins/hal/artifacts/`). Sources, configs and build tooling live in `ui/`; the plugin directory
contains only what is read at runtime. The two must not contaminate each other.

## Why static HTML, not a plugin component

The Claude Code plugin schema has **no artifact component type** — components are Skills, Commands,
Agents, Hooks, MCP servers, LSP servers, and Monitors, nothing else. Shipping "a static HTML file
committed under the plugin, read at runtime by a skill" is **not a workaround** — it is the only
supported mechanism for delivering a front-end with a plugin.

## Layout

```
ui/                                   ← SOURCE — never read at runtime
├── pnpm-workspace.yaml
├── package.json                      (workspace root; cheerio devDependency)
├── pnpm-lock.yaml                    (committed — makes rebuilds reproducible)
├── .npmrc                            (@bluegreeno/* → GitHub Packages mapping only)
├── scripts/build-artifact.mjs        (shared post-build step)
└── <name>/                           one directory per artifact (Vite app)
    ├── package.json                  ("build": "vite build && node ../scripts/build-artifact.mjs <name>")
    ├── vite.config.ts                (viteSingleFile())
    └── src/

plugins/hal/artifacts/
└── <name>.html                       ← DELIVERED — single-file, committed
```

`ui/` sits at the repo root, **not** under `plugins/hal/`: the plugin directory stays auditable, and
no skill can read a source file by accident. `ui/**/node_modules/` and `ui/**/dist/` are gitignored,
so `git clone` pulls no dependencies and no uncommitted build output — only source and the committed
`.html`.

## Building an artifact

```bash
cd ui
corepack enable          # activates pnpm from package.json's packageManager field
pnpm install
pnpm --filter <name> build
```

`pnpm --filter <name> build` runs `vite build` (producing `ui/<name>/dist/index.html`), then
`ui/scripts/build-artifact.mjs <name>`, which:

1. **Size guard** — hard-fails past 16 MiB (the Cowork/Claude Code rendered ceiling), warns past 2 MiB.
2. **Provenance stamp** — prepends an HTML comment carrying build date, source commit, and the
   `@bluegreeno/annotation-core` version (or `n/a`). This answers "which code produced this committed
   HTML?", otherwise unanswerable without regenerating it. The stamp line is intentionally
   non-reproducible (its date changes every run), so `scripts/check_artifact_sync.sh` strips it before
   diffing.
3. **Target shape** (`ARTIFACT_TARGET`, see below).
4. Writes `plugins/hal/artifacts/<name>.html`.

Commit both the source (`ui/<name>/`) and the resulting `plugins/hal/artifacts/<name>.html`.

## Two output shapes — pick per artifact

The two artifact runtimes want incompatible document shapes; they are **not** interchangeable.

| `ARTIFACT_TARGET` | Runtime | Output |
|-------------------|---------|--------|
| `cowork` (default) | Cowork live artifact | Full document — `<!doctype html>`, stamp, then `<html>/<head>/<body>`. |
| `fragment` | Claude Code / claude.ai | **Fragment only** — the `Artifact` tool wraps the file in its own `<!doctype html>…<body>` shell, so emitting wrapper tags is a bug. |

`vite-plugin-singlefile` inlines the `<script>`/`<style>` into `<head>`, so the fragment extraction
concatenates `head` **and** `body` (dropping only the wrapper tags) — a body-only extraction would
silently drop the entire bundle.

**v1 ships the `cowork` target only** (per `#50`). The `fragment` path is implemented and verified but
nothing consumes it yet.

## How a skill consumes a bundled artifact

A future skill (`#50`) reads the committed template, hydrates any per-session values, and writes the
result **to a working directory** — never back under the plugin root.

- Read the template through `${CLAUDE_PLUGIN_ROOT}/artifacts/<name>.html`. Treat `${CLAUDE_PLUGIN_ROOT}`
  as **read-only, ephemeral input**: it changes on every plugin update, and the previous directory is
  cleaned up roughly two weeks later. Never write into it, never use it as a state store.
- Inject per-session values (e.g. a Cowork connector UUID) into the read template in memory.
- Write the hydrated output to a **working directory**. If a skill ever needs to persist hydrated
  output across sessions, `${CLAUDE_PLUGIN_DATA}` (survives updates) is the mechanism — not the plugin
  root.

## CI

`scripts/check_artifact_sync.sh` rebuilds every `ui/<name>/` and fails if the committed HTML drifts
from a fresh rebuild (ignoring the build-stamp line). This is what makes "committed build output" safe
— the invariant is machine-checked, not maintained by discipline. CI runs it (with a Node/pnpm setup)
**only** when `ui/**` or `plugins/hal/artifacts/**` changed, so Python-only PRs stay fast.

## GitHub Packages auth (`@bluegreeno/*`)

`ui/.npmrc` declares only the scope→registry mapping
(`@bluegreeno:registry=https://npm.pkg.github.com`). It intentionally carries **no token** — pnpm
≥10.34.2/≥11.5.3 ignores `${VAR}`-style expansion in a committed project-level `.npmrc`
(GHSA-3qhv-2rgh-x77r), and a token must never be committed regardless.

The mapping has no effect until a future issue (`#50`) adds a real `@bluegreeno/*` dependency. When it
does:

- **Local dev**: `pnpm config set "//npm.pkg.github.com/:_authToken" "$TOKEN"` (writes user-level
  config, which still expands normally).
- **CI**: use `actions/setup-node`'s `registry-url` / `NODE_AUTH_TOKEN` inputs. Note the default
  Actions `GITHUB_TOKEN` cannot read packages published from a *different* repository, even in the same
  org — a classic PAT with `read:packages`, stored as a repo secret, will be required.
