#!/usr/bin/env python3
"""
/edifice pair — OAuth 2.0 Device Flow pairing (RFC 8628).

No external dependencies — Python stdlib only.
Run once per laptop (Mac or Windows).

Usage: python3 pair.py
"""

import json
import os
import pathlib
import socket
import stat
import sys
import time
import urllib.error
import urllib.request

GATEWAY_URL = "https://api.edifice.bluegreen.ai"
HAL_MCP_URL = "https://zgkvbjqlvebttbnkklpo.supabase.co/functions/v1/hal-mcp"
SUPABASE_URL = "https://zgkvbjqlvebttbnkklpo.supabase.co"
POLL_INTERVAL = 5  # seconds between polls


# ---------------------------------------------------------------------------
# Cross-platform paths
# ---------------------------------------------------------------------------

def get_edifice_config_dir() -> pathlib.Path:
    return pathlib.Path.home() / ".edifice-mission-report"


def get_claude_json_path() -> pathlib.Path:
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "")
        base = pathlib.Path(appdata) if appdata else pathlib.Path.home() / "AppData" / "Roaming"
        return base / "Claude" / "claude.json"
    return pathlib.Path.home() / ".claude.json"  # Mac + Linux


def detect_platform() -> str:
    if sys.platform == "darwin":
        return "mac"
    if sys.platform == "win32":
        return "windows"
    return "linux"


def detect_device_name() -> str:
    try:
        return socket.gethostname() or "laptop"
    except Exception:
        return "laptop"


# ---------------------------------------------------------------------------
# HTTP helpers (stdlib only)
# ---------------------------------------------------------------------------

def _post(url: str, body: dict) -> dict:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def save_config(tokens: dict) -> pathlib.Path:
    config_dir = get_edifice_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)

    payload = json.dumps(tokens, indent=2)

    # Always write config.json (backward compat — = last paired user)
    default_file = config_dir / "config.json"
    default_file.write_text(payload, encoding="utf-8")
    try:
        default_file.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass  # Windows — home dir is user-private by default

    # Also write named file config-<email>.json if email is known
    user_email = tokens.get("user_email") or ""
    if user_email:
        named_file = config_dir / f"config-{user_email}.json"
        named_file.write_text(payload, encoding="utf-8")
        try:
            named_file.chmod(stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass
        return named_file  # return named path for display

    return default_file


def register_hal_mcp(access_token: str) -> pathlib.Path:
    """Add/update hal-mcp in ~/.claude.json mcpServers. Preserves existing entries."""
    claude_path = get_claude_json_path()
    config: dict = {}
    if claude_path.exists():
        try:
            config = json.loads(claude_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            config = {}

    config.setdefault("mcpServers", {})
    config["mcpServers"]["hal-mcp"] = {
        "type": "http",
        "url": HAL_MCP_URL,
        "headers": {"Authorization": f"Bearer {access_token}"},
    }

    claude_path.parent.mkdir(parents=True, exist_ok=True)
    claude_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return claude_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    device_name = detect_device_name()
    plat = detect_platform()
    plugin_dir = str(pathlib.Path(__file__).resolve().parent)

    print(f"Pairing device : {device_name} ({plat})")

    # 1. Init
    try:
        resp = _post(f"{GATEWAY_URL}/v1/auth/device/init", {})
    except Exception as exc:
        print(f"ERROR: Cannot reach hal-gateway: {exc}", file=sys.stderr)
        sys.exit(1)

    device_code: str = resp["device_code"]
    user_code: str = resp["user_code"]
    expires_in: int = resp.get("expires_in", 600)

    print()
    print("─" * 52)
    print("  Ouvre l'Edifice PWA → ⚙️  Paramètres")
    print("  → Connecter un laptop → entre le code :")
    print(f"  {user_code}")
    print(f"  (expire dans {expires_in // 60} min)")
    print("─" * 52)
    print("En attente", end="", flush=True)

    # 2. Poll until confirmed or expired
    deadline = time.time() + expires_in
    poll: dict = {}
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL)
        try:
            poll = _post(f"{GATEWAY_URL}/v1/auth/device/poll", {
                "device_code": device_code,
                "device_name": device_name,
                "platform": plat,
            })
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                print("\n\nCode expiré. Relance /edifice pair.", file=sys.stderr)
                sys.exit(1)
            print(".", end="", flush=True)
            continue
        except Exception:
            print(".", end="", flush=True)
            continue

        if poll.get("status") == "complete":
            break
        print(".", end="", flush=True)
    else:
        print("\n\nTimeout. Relance /edifice pair.", file=sys.stderr)
        sys.exit(1)

    # 3. Save credentials (retro-compatible + new fields)
    print("\n")
    user_email: str = poll.get("user_email") or ""

    tokens = {
        "access_token": poll["access_token"],
        "refresh_token": poll["refresh_token"],
        "supabase_url": SUPABASE_URL,
        "user_email": user_email,
        "device_name": device_name,
        "platform": plat,
        "plugin_dir": plugin_dir,
        "paired_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    config_file = save_config(tokens)
    print(f"✅  Credentials : {config_file}")

    # 4. Register hal-mcp in ~/.claude.json
    claude_path = register_hal_mcp(poll["access_token"])
    print(f"✅  hal-mcp      : {claude_path}")

    print()
    print(f"   Connecté comme : {user_email or device_name}")
    print()
    print("⚠️   Redémarre Claude Code pour activer hal-mcp.")
    print("    Ensuite, /edifice pull fonctionnera avec tes credentials.")


if __name__ == "__main__":
    main()
