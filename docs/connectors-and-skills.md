# Installing connectors & skills — Claude, Gemini, OpenAI

How to connect the `hal` plugin's MCP server (**connector**) and its `SKILL.md`
files (**skills**) across the three major AI providers.

Read this first: **a connector and a skill are two different things with different reach.**

| | What it is | Where it installs |
|---|---|---|
| **Connector** | A remote **MCP server** (our Supabase Edge Function `hal-mcp`) exposing tools | **Every** surface: Claude (Code / Desktop / claude.ai), Gemini (Enterprise / CLI), ChatGPT |
| **Skill** | A `SKILL.md` capability file (`/edifice`, `/hal …`) | **Only the agent/CLI surfaces**: Claude Code, Gemini **CLI**, OpenAI **Codex** — via the [agentskills.io](https://agentskills.io) standard. **Not** the chat apps. |

The chat apps (claude.ai chat, ChatGPT app, Gemini Enterprise) **cannot install a skill** —
they only call the connector's tools. The full `/edifice` / `/hal` skill experience lives in
**Claude Code**. That is our primary, fully-supported target.

---

## Our server — the facts that drive everything below

| | Value |
|---|---|
| MCP server | `hal-mcp` — Supabase Edge Function |
| Project ref | `zgkvbjqlvebttbnkklpo` |
| URL | `https://zgkvbjqlvebttbnkklpo.supabase.co/functions/v1/hal-mcp` |
| Transport | **Streamable HTTP** (required by all three; Gemini Enterprise refuses SSE) |
| Auth — chat/web/mobile | **OAuth 2.1** via Supabase Auth (`/auth/v1`), with discovery + dynamic client registration |
| Auth — Claude Code CLI / Desktop | **`apikey` header** (`secret:hal_api_key` mode) — no OAuth dance |
| OAuth discovery | `…/hal-mcp/.well-known/oauth-protected-resource` → authorization server `…/auth/v1` |

Because `hal-mcp` runs a full Supabase OAuth 2.1 server, **Claude, ChatGPT, and Gemini CLI
need only the URL** — they discover the auth server and self-register (no client ID to paste).
**Gemini Enterprise is the exception** (see §2): it uses classic OAuth and needs endpoints
pasted manually.

---

## 1. Claude — primary, fully supported

### 1a. Claude Code (CLI) — the full skill + connector experience

```
/plugin marketplace add BluegReeno/bluegreen-marketplace
/plugin install hal@bluegreen-marketplace
```

Installing the plugin registers **both** the skills (`/edifice`, `/hal …`) **and** the
`hal-mcp` connector automatically (the bundled `.mcp.json` auto-starts when the plugin is
enabled). Run `/reload-plugins` if it doesn't appear immediately.

The connector authenticates via the `apikey` header. If it isn't already wired, add it once:

```
claude mcp add --transport http hal-mcp \
  https://zgkvbjqlvebttbnkklpo.supabase.co/functions/v1/hal-mcp \
  --header "apikey: <HAL_API_KEY>"
```

### 1b. Claude Desktop / claude.ai (connector only — no skills)

`Settings → Connectors` (Desktop: `Customize → Connectors`) → **Add custom connector** →
paste the URL → **Add**.

- No Client ID / Secret needed — OAuth discovery + dynamic client registration are automatic.
- A browser opens for the Supabase consent screen on first use. Approve, and it syncs to mobile.
- ⚠️ The browser's claude.ai session must be the **same account** as the app, or you get
  "Account mismatch / Incompatibilité de compte".

> Claude Desktop / claude.ai run the **tools**, not the `/edifice` / `/hal` skills. For the full
> command experience, use Claude Code (§1a).

---

## 2. Gemini

### 2a. Gemini Enterprise — connector via "Custom MCP Server" data store

This is the surface in the OAuth tutorial. It is **classic OAuth**: you paste the endpoints
manually (no discovery, no dynamic registration). Status: **Preview** — UI labels drift.

**Google Cloud console → Gemini Enterprise:**
1. Nav menu → **Data stores** → **Create data store**.
2. On **Select a data source**, type **Custom MCP Server** in the search field → select it.
3. **MCP Server URL**: `https://zgkvbjqlvebttbnkklpo.supabase.co/functions/v1/hal-mcp`
4. **Transport: Streamable HTTP** (the only option Gemini Enterprise supports).
5. **Authentication settings** (all manual):
   - **Authorization URI**: `https://zgkvbjqlvebttbnkklpo.supabase.co/auth/v1/authorize`
   - **Token URI**: `https://zgkvbjqlvebttbnkklpo.supabase.co/auth/v1/token`
   - **Client ID** / **Client Secret**: from a Supabase OAuth client (see box below)
   - **Scopes**: as required by the client registration
6. Google fixes the **redirect URI** to `https://vertexaisearch.cloud.google.com/oauth-redirect`
   — register it on the Supabase side as an allowed redirect.
7. Click **Login** to verify the connection, then **Continue**.
8. **Enable the tools** — by default *all tools are disabled* on a new MCP data store.

> **Supabase OAuth client (the part the tutorial gets wrong)**
> There is **no** ready-made "Client ID / Secret" in *Supabase → Project Settings → Authentication*.
> Because Gemini Enterprise cannot do dynamic client registration, you must **pre-register a
> static OAuth client** against the Supabase OAuth 2.1 server (`/auth/v1/oauth/*`) and use its
> `client_id` / `client_secret`. Alternative: front the function with a dedicated IdP
> (Google / Okta / Azure AD) and paste *its* endpoints instead. This step is hands-on in the
> console — see the tracking issue.

**Google Workspace Admin (org enablement):**
`admin.google.com` → Menu → **Generative AI** → **Gemini app** → **Apps** → enable access
(requires the *Gemini Settings administrator* privilege; can take up to 24 h to propagate).
The older `Apps > Google Workspace > Gemini > Extensions` path is being redirected to this
new **Generative AI** section.

**First run:** in the Gemini app, invoke the connector ("Utilise hal-mcp pour …"). Gemini runs
the Authorization-Code flow → Supabase consent screen → approve → token stored. Subsequent
calls are transparent.

### 2b. Gemini CLI — connector + skills (OAuth discovery, no manual endpoints)

Unlike Enterprise, Gemini CLI honors OAuth **discovery + dynamic registration** — paste only
the URL. Edit `~/.gemini/settings.json`:

```json
"mcpServers": {
  "hal-mcp": {
    "httpUrl": "https://zgkvbjqlvebttbnkklpo.supabase.co/functions/v1/hal-mcp",
    "oauth": { "enabled": true }
  }
}
```

Then authorize once with `/mcp auth hal-mcp` (opens the browser flow).

> ⚠️ **Key rename in progress.** A PR is consolidating `httpUrl` → `url`. If your CLI version
> is recent and `httpUrl` has no effect, replace it with `url` in `settings.json`.

Gemini CLI also reads the `SKILL.md` standard — skills live in `~/.gemini/skills/`
(alias `~/.agents/skills/`), so the §4 symlinks expose `/edifice` and `/hal` here too.

---

## 3. OpenAI / ChatGPT — connector only (no skills in the chat app)

ChatGPT needs **Developer Mode** for a connector that exposes write tools (not just search/fetch).

1. `Settings → Apps & Connectors → Advanced settings → Developer mode` → toggle **ON**
   (confirm the warning). On Business/Enterprise/Edu a workspace admin must enable it first.
2. `Settings → Apps & Connectors → Add new connector` (a.k.a. **Create**).
3. **MCP Server URL**: `https://zgkvbjqlvebttbnkklpo.supabase.co/functions/v1/hal-mcp`
4. **Authentication = OAuth** → **Create**. ChatGPT discovers the auth server, registers itself
   dynamically (PKCE), and opens the Supabase consent flow. No endpoints to paste.

Available on Plus / Pro / Business / Enterprise / Edu — **web only**, beta (Free can't add
custom connectors).

> ⚠️ ChatGPT's dynamic registration is unstable as of mid-2026 — some builds mis-detect the
> OAuth endpoints or force a manual **OAuth Client ID** despite discovery. Contingency:
> pre-register a static OAuth client on Supabase so you can paste a `client_id` if the
> automatic flow fails.

> ChatGPT has no Agent Skills in the chat app. The `/edifice` / `/hal` *skills* run in **Codex**
> (which adopted `SKILL.md`) via `.agents/skills/` — see §4. The chat app only calls tools.

### 3b. OpenAI Codex — connector + skills

Codex reads the [agentskills.io](https://agentskills.io/specification) standard and picks up
skills from `.agents/skills/` (same as Gemini CLI — see §4 for the symlink setup).

For the MCP connector, add it to your Codex MCP config (path varies by install):

```json
"hal-mcp": {
  "url": "https://zgkvbjqlvebttbnkklpo.supabase.co/functions/v1/hal-mcp",
  "auth": { "type": "oauth" }
}
```

Codex discovers the auth server automatically (no endpoints to paste) and opens the browser
consent flow on first use.

---

## 4. Skills cross-client (Claude Code / Gemini CLI / Codex)

Our `SKILL.md` files already comply with the [agentskills.io](https://agentskills.io/specification)
standard. To expose them to Gemini CLI and OpenAI Codex (which both read `.agents/skills/`),
symlink them at the repo root:

```bash
# run from the repo root
mkdir -p .agents/skills
ln -sf "$(pwd)/plugins/hal/skills/hal"     .agents/skills/hal
ln -sf "$(pwd)/plugins/hal/skills/edifice" .agents/skills/edifice
```

No frontmatter change needed. The chat apps (claude.ai, ChatGPT, Gemini Enterprise) ignore
`.agents/skills/` — skills are an agent/CLI feature only.

---

## 5. Provider matrix (cheat sheet)

| | Connector (MCP) | Auth model | Paste endpoints? | Skills? |
|---|---|---|---|---|
| **Claude Code** | ✅ auto via plugin | `apikey` header | No | ✅ native |
| **Claude Desktop / claude.ai** | ✅ Add custom connector | OAuth discovery + DCR | No | ❌ |
| **Gemini Enterprise** | ✅ Custom MCP data store | OAuth (classic) | **Yes — manual** | ❌ |
| **Gemini CLI** | ✅ `mcpServers` config | OAuth discovery | No | ✅ via `.agents/skills/` |
| **ChatGPT (Dev Mode)** | ✅ Add connector | OAuth discovery + DCR + PKCE | No | ❌ |
| **OpenAI Codex** | ✅ MCP config | discovery | No | ✅ via `.agents/skills/` |

---

## 6. Verify the server is connectable (run from a machine with network access)

```bash
# OAuth discovery — must return JSON with authorization_servers
curl https://zgkvbjqlvebttbnkklpo.supabase.co/functions/v1/hal-mcp/.well-known/oauth-protected-resource

# Supabase OAuth server enabled — must NOT return {"error_code":"feature_disabled"}
curl https://zgkvbjqlvebttbnkklpo.supabase.co/auth/v1/.well-known/oauth-authorization-server

# Tool list over the apikey header (Claude Code path)
# Never share <HAL_API_KEY> — treat it like a password
npx @modelcontextprotocol/inspector \
  --header "apikey: <HAL_API_KEY>" \
  https://zgkvbjqlvebttbnkklpo.supabase.co/functions/v1/hal-mcp
```

For the server-side OAuth and Edge Function implementation details, see the `renaud-marketplace`
repo (`docs/mcp-server-supabase-edge.md`).

---

## Sources

- Claude — connectors & MCP: <https://claude.com/docs/connectors/building>, <https://claude.com/docs/connectors/building/authentication>, <https://claude.com/docs/mcp>, <https://claude.com/docs/plugin-marketplaces>
- Claude — `mcp-server-dev` skill (Anthropic official): <https://github.com/anthropics/claude-plugins-official/tree/main/plugins/mcp-server-dev>
- Gemini Enterprise custom MCP: <https://docs.cloud.google.com/gemini/enterprise/docs/connectors/custom-mcp-server/set-up-custom-mcp-server>
- Gemini Workspace admin: <https://support.google.com/a/answer/15293691>
- OpenAI developer mode / connectors: <https://help.openai.com/en/articles/12584461-developer-mode-apps-and-full-mcp-connectors-in-chatgpt-beta>
- MCP authorization spec: <https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization>
- Agent Skills standard: <https://agentskills.io/specification>
</content>
</invoke>
