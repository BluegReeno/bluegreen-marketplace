# Edifice Mission Report — Claude Plugin

Pull an Edifice mission from Supabase and generate the DOCX report locally, directly from Claude Cowork or Claude Code.

## Prerequisites

### 1. Install `uv` (one-time)

The plugin uses [`uv`](https://docs.astral.sh/uv/) to manage Python dependencies automatically — no venv, no pip.

**Mac:**

```bash
brew install uv
```

**Windows:**

```powershell
winget install astral-sh.uv
```

### 2. Install the plugin (one-time)

In Claude Cowork:

```
/plugin marketplace add BluegReeno/bluegreen-marketplace
/plugin install edifice-mission-report@bluegreen-marketplace
```

### 3. Enable auto-update (recommended)

In Cowork: `/plugin` → Marketplaces tab → select `bluegreen-marketplace` → enable auto-update.

## Usage

### First time: pair your laptop

1. In Claude Cowork, type `/edifice pair`.
2. The skill calls the Edifice gateway and displays a code (e.g. `ABCD-EFGH`).
3. On your phone, open the Edifice PWA → tap ⚙️ (Settings) → "Connecter un laptop" → enter the code.
4. The laptop is now paired. Credentials are stored in `~/.edifice-mission-report/config.json`.

### Every mission

1. On the phone (Edifice PWA), open a mission and tap **"Exporter pour Cowork"**.
2. Share the generated `.edifice.md` file to your laptop (AirDrop, email, Drive, etc.).
3. Open Claude Cowork in the folder containing the `.edifice.md` file.
4. Ask: *"Pull this mission and generate the report."*

The skill activates automatically when it detects a `*.edifice.md` file. It authenticates using the stored refresh token (auto-renewed by the Supabase SDK), downloads mission data + photos, and renders the DOCX report.

The generated report appears in `mission/rapport.docx` next to the briefing file.

## Manual usage (without Claude)

```bash
uv run --with "supabase>=2.28,<3.0" --with docxtpl --with pyyaml \
  python pull_mission.py mission-example.edifice.md
```

Options:

| Flag | Default | Description |
|------|---------|-------------|
| `--output-dir` | `mission/` | Where to save downloaded data and the report |
| `--report-type` | `suivi_chantier` | Which DOCX template to use |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `uv: command not found` | Install uv (see Prerequisites above) |
| "This laptop is not paired" | Run `/edifice pair` in Claude Cowork |
| Auth token refresh fails | Delete `~/.edifice-mission-report/config.json` and re-pair |
| Template not found | Check `--report-type` matches a `.docx` file in `templates/` |
