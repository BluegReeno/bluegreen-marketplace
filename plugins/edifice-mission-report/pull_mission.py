#!/usr/bin/env python3
"""
Pull an Edifice mission from Supabase and generate the DOCX report.

Usage:
    python pull_mission.py <path-to-edifice.md>

The script:
1. Parses the briefing file (YAML front-matter with edifice_mission_id).
2. Loads Supabase credentials from ~/.edifice-mission-report/config.json (stored during /edifice pair).
3. Authenticates via refresh_token exchange (stdlib HTTP — no SDK required).
4. Downloads the mission (project row, building, notes, photos) into a mission/ subdirectory.
5. Renders the DOCX into mission/rapport.docx using the template matching report_type.
"""

import argparse
import errno
import json
import os
import stat
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Credential resolution is deferred to resolve_config_file(briefing_path) in main().
# Order: EDIFICE_CONFIG_PATH env var → briefing dir → ~/.edifice-mission-report/config.json
CONFIG_FILE: Path | None = None

# Public anon key — not a secret (committed in .env.production)
SUPABASE_ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpna3ZianFsdmVidHRibmtrbHBvIiwi"
    "cm9sZSI6ImFub24iLCJpYXQiOjE3NTIwNjc4MTMsImV4cCI6MjA2NzY0MzgxM30."
    "5KL9SDxYR2nP5tQTMnliykVSPbhlw0BqbAa10T_9io8"
)


# ---------------------------------------------------------------------------
# Minimal Supabase client (stdlib-only — no SDK required)
# ---------------------------------------------------------------------------

class SupabaseClient:
    """Minimal Supabase client — auth + REST + storage signed URLs, stdlib urllib only."""

    def __init__(self, url: str, anon_key: str):
        self.url = url.rstrip("/")
        self.anon_key = anon_key
        self.access_token: str = ""

    def refresh_session(self, refresh_token: str) -> dict:
        """Exchange refresh_token for a new session. Returns {access_token, refresh_token}."""
        body = json.dumps({"refresh_token": refresh_token}).encode()
        req = urllib.request.Request(
            f"{self.url}/auth/v1/token?grant_type=refresh_token",
            data=body,
            headers={
                "Content-Type": "application/json",
                "apikey": self.anon_key,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        self.access_token = data["access_token"]
        return data

    def set_service_key(self, service_key: str) -> None:
        self.access_token = service_key

    def _headers(self) -> dict:
        return {
            "apikey": self.anon_key,
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def select(self, table: str, query: str = "*", filters: dict | None = None) -> list:
        """GET /rest/v1/{table}?select=...&col=eq.val — returns list directly."""
        params: dict = {"select": query}
        if filters:
            for k, v in filters.items():
                params[k] = f"eq.{v}"
        qs = urllib.parse.urlencode(params)
        req = urllib.request.Request(
            f"{self.url}/rest/v1/{table}?{qs}",
            headers={**self._headers(), "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())

    def update(self, table: str, data: dict, filters: dict) -> None:
        """PATCH /rest/v1/{table}?col=eq.val"""
        qs = urllib.parse.urlencode({k: f"eq.{v}" for k, v in filters.items()})
        body = json.dumps(data).encode()
        req = urllib.request.Request(
            f"{self.url}/rest/v1/{table}?{qs}",
            data=body,
            headers=self._headers(),
            method="PATCH",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()

    def create_signed_url(self, bucket: str, path: str, expires_in: int = 3600) -> str:
        """POST /storage/v1/object/sign/{bucket}/{path} — returns full signed URL."""
        body = json.dumps({"expiresIn": expires_in}).encode()
        req = urllib.request.Request(
            f"{self.url}/storage/v1/object/sign/{bucket}/{path}",
            data=body,
            headers=self._headers(),
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        return f"{self.url}/storage/v1{data['signedURL']}"

    def download_file(self, signed_url: str) -> bytes:
        req = urllib.request.Request(signed_url, headers={"apikey": self.anon_key})
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read()


# ---------------------------------------------------------------------------
# YAML frontmatter parser (stdlib regex — no pyyaml)
# ---------------------------------------------------------------------------

def parse_yaml_frontmatter(text: str) -> dict:
    """Parse simple key: value YAML frontmatter (scalar values only — sufficient for .edifice.md)."""
    result = {}
    for line in text.strip().splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            result[key.strip()] = val.strip()
    return result


# ---------------------------------------------------------------------------
# Credential resolution
# ---------------------------------------------------------------------------

def resolve_config_file(briefing_path: Path) -> Path:
    """Resolve credentials file location in priority order:
    1. EDIFICE_CONFIG_PATH env var
    1b. EDIFICE_USER env var → ~/.edifice-mission-report/config-<email>.json
    2. edifice-credentials.json next to the briefing file
    3. ~/.edifice-mission-report/config.json (standard Mac/Windows CLI)
    4. /Users/*/  scan (Cowork sandbox: home != /Users/...)
    5. C:/Users/*/ scan (Cowork sandbox on Windows)
    """
    override = os.environ.get("EDIFICE_CONFIG_PATH")
    if override:
        return Path(override)

    edifice_user = os.environ.get("EDIFICE_USER")
    if edifice_user:
        named = Path.home() / ".edifice-mission-report" / f"config-{edifice_user}.json"
        if named.exists():
            return named
        raise SystemExit(
            f"Credentials not found for user '{edifice_user}'.\n"
            f"Expected: {named}\n"
            "Run /edifice pair with that account first."
        )

    candidate = briefing_path.parent / "edifice-credentials.json"
    if candidate.exists():
        return candidate

    standard = Path.home() / ".edifice-mission-report" / "config.json"
    if standard.exists():
        return standard

    # Cowork sandbox: sandbox home != real user home → scan OS user dirs
    home_str = str(Path.home())
    for users_root in [Path("/Users"), Path("C:/Users")]:
        if users_root.exists() and not home_str.startswith(str(users_root)):
            try:
                for user_dir in sorted(users_root.iterdir()):
                    if user_dir.is_dir() and not user_dir.name.startswith("."):
                        alt = user_dir / ".edifice-mission-report" / "config.json"
                        if alt.exists():
                            return alt
            except PermissionError:
                pass

    return standard  # will fail with a clear error message below


# ---------------------------------------------------------------------------
# Briefing file parsing
# ---------------------------------------------------------------------------

def parse_briefing(path: Path) -> dict:
    """Parse a *.edifice.md briefing file. Returns frontmatter dict."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        if exc.errno == errno.EDEADLK:
            raise SystemExit(
                f"Cannot read briefing file (EDEADLK / resource deadlock): {path}\n"
                "The file is on a network mount (Google Drive, Synology, FUSE) that is\n"
                "inaccessible from the sandbox. Use the Read tool to copy it to a local\n"
                "path, then re-run with that local path as BRIEFING."
            )
        raise
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise SystemExit("Error: briefing file missing YAML front-matter (--- delimiters).")
    fm = parse_yaml_frontmatter(parts[1])
    if "edifice_mission_id" not in fm:
        raise SystemExit("Error: briefing file missing 'edifice_mission_id' in front-matter.")
    return fm


# ---------------------------------------------------------------------------
# Config management
# ---------------------------------------------------------------------------

def load_config(config_file: Path) -> dict | None:
    """Load credentials from config_file."""
    if not config_file.exists():
        return None
    return json.loads(config_file.read_text(encoding="utf-8"))


def save_config(config: dict) -> None:
    """Save device config, creating the directory if needed."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2), encoding="utf-8")
    try:
        CONFIG_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass  # Windows — home directory is user-private by default


# ---------------------------------------------------------------------------
# Supabase client
# ---------------------------------------------------------------------------

def get_supabase_client(config: dict, config_file: Path) -> SupabaseClient:
    """Create an authenticated Supabase client from stored config.

    If config contains a 'service_key', uses it directly (bypasses user auth).
    Otherwise authenticates via refresh_token exchange (stdlib HTTP — no SDK).
    """
    supabase_url = config["supabase_url"]
    client = SupabaseClient(supabase_url, SUPABASE_ANON_KEY)

    service_key = config.get("service_key") or os.environ.get("SUPABASE_SECRET_KEY")
    if service_key:
        client.set_service_key(service_key)
        return client

    try:
        new_session = client.refresh_session(config["refresh_token"])
        config["access_token"] = new_session["access_token"]
        config["refresh_token"] = new_session["refresh_token"]
        config_file.write_text(json.dumps(config, indent=2), encoding="utf-8")
    except Exception as exc:
        raise SystemExit(
            f"Authentication failed: {exc}\n"
            "Tip: set SUPABASE_SECRET_KEY env var (from .env) to bypass user auth.\n"
            "Or export a fresh edifice-credentials.json from the Edifice PWA and retry.\n"
            f"(Credentials file: {config_file})"
        )

    return client


# ---------------------------------------------------------------------------
# Mission pull
# ---------------------------------------------------------------------------

def pull_mission(supabase: SupabaseClient, mission_id: str, output_dir: Path) -> dict:
    """Download mission data from Supabase into output_dir.

    Returns the context dict suitable for render_cr_visite.
    """
    # 1. Fetch project
    print(f"Fetching mission {mission_id}...")
    projects = supabase.select("edifice_projects", "*", {"id": mission_id})
    if not projects:
        raise SystemExit(f"Mission {mission_id} not found in Supabase.")
    project = projects[0]

    # 2. Fetch building (if project has a building_id)
    building = {}
    building_id = project.get("building_id")
    if building_id:
        buildings = supabase.select("edifice_buildings", "*", {"id": building_id})
        if buildings:
            building = buildings[0]

    # 3. Fetch notes for this mission
    notes = supabase.select("edifice_notes", "*", {"project_id": mission_id})
    print(f"  Found {len(notes)} note(s).")

    # 4. Fetch photos for this mission
    photos = supabase.select("edifice_photos", "*", {"project_id": mission_id})
    print(f"  Found {len(photos)} photo(s).")

    # 5. Download photos via signed URLs
    photos_dir = output_dir / "photos"
    photos_dir.mkdir(parents=True, exist_ok=True)
    failed_count = 0
    for photo in photos:
        storage_path = photo.get("storage_path", "")
        if not storage_path:
            continue
        filename = Path(storage_path).name
        dest = photos_dir / filename
        print(f"  Downloading {filename}...")
        try:
            signed_url = supabase.create_signed_url("edifice-photos", storage_path)
            data = supabase.download_file(signed_url)
            dest.write_bytes(data)
            failed_count = 0  # reset consecutive counter on success
        except Exception as exc:
            failed_count += 1
            print(f"  Warning: download failed for {storage_path}: {exc}", file=sys.stderr)
            if failed_count >= 3:
                print(f"  Error: {failed_count} consecutive failures — possible auth or config issue. Stopping downloads.", file=sys.stderr)
                break

    if failed_count:
        print(f"  {failed_count} photo download(s) failed in last batch.", file=sys.stderr)

    # 6. Save raw data as JSON (for debugging / enrichment)
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "project.json").write_text(json.dumps(project, indent=2, default=str), encoding="utf-8")
    (data_dir / "building.json").write_text(json.dumps(building, indent=2, default=str), encoding="utf-8")
    (data_dir / "notes.json").write_text(json.dumps(notes, indent=2, default=str), encoding="utf-8")
    (data_dir / "photos.json").write_text(json.dumps(photos, indent=2, default=str), encoding="utf-8")

    # 7. Build context for DOCX rendering
    project_type = project.get("type") or "suivi_chantier"
    context = {
        "project_type": project_type,
        "building_id": building_id or "",
        "titre_service": project.get("name", "Mission Edifice"),
        "client": project.get("client_name", ""),
        "residence": building.get("name", ""),
        "batiments_visites": building.get("name", ""),
        "adresse": building.get("address", ""),
        "code_postal_ville": building.get("city", ""),
        "description_batiment": building.get("description", ""),
        "ref_dossier": project.get("reference", ""),
        "date_visite": (project.get("visited_at") or project.get("created_at") or "")[:10],
        "participants": [],
        "objet_visite": project.get("mission_context") or project.get("description", ""),
        "synthese": "",
        "observations": [],
        "conclusion": "",
    }

    # Map notes to observations — sorted by display_order
    sorted_notes = sorted(notes, key=lambda n: n.get("display_order") or 999)

    # Separate linked photos (note_id set) from free photos (note_id null)
    linked_photos = [p for p in photos if p.get("note_id")]
    free_photos = sorted(
        [p for p in photos if not p.get("note_id")],
        key=lambda p: p.get("created_at") or ""
    )

    # If no photo is linked to any note, distribute free photos to observations
    # by chronological order (best-effort matching — 1 photo per observation)
    unlinked_pool = list(free_photos) if not linked_photos else []

    for i, note in enumerate(sorted_notes):
        # Collect ALL photos linked to this note (sorted by created_at)
        note_photos = sorted(
            [p for p in linked_photos if p.get("note_id") == note.get("id")],
            key=lambda p: p.get("created_at") or ""
        )
        if note_photos:
            photo_files = [Path(p.get("storage_path", "")).name for p in note_photos if p.get("storage_path")]
        elif unlinked_pool:
            photo_files = [Path(unlinked_pool.pop(0).get("storage_path", "")).name]
        else:
            photo_files = []

        photo_file = photo_files[0] if photo_files else ""  # backward-compat single field

        name = note.get("name") or ""
        description = note.get("description") or note.get("content") or note.get("text") or ""
        full_text = f"{name} — {description}" if name and description else (name or description)

        context["observations"].append({
            "ref": f"OBS-{i + 1:02d}",
            "note_id": note["id"],
            "name": name,
            "etage_facade": note.get("location") or "",
            "localisation": note.get("location") or "",
            "observation": full_text,
            "desordre": full_text,
            "zone": "",        # APT/BAL/CAV/FAC — filled by /edifice improve for devis
            "ie": None,        # 1-5 — filled by /edifice improve for devis
            "action": "",
            "photo": photo_file,   # first photo (backward compat)
            "photos": photo_files, # all photos for this note
        })

    # Keep remaining free photos (overflow) for the gallery section
    context["gallery_photos"] = [
        Path(p.get("storage_path", "")).name for p in unlinked_pool if p.get("storage_path")
    ]

    # Save context JSON
    context_path = output_dir / "context.json"
    context_path.write_text(json.dumps(context, indent=2, ensure_ascii=False), encoding="utf-8")

    return context


# ---------------------------------------------------------------------------
# DOCX rendering
# ---------------------------------------------------------------------------

def render_report(context: dict, photos_dir: Path, output_path: Path, report_type: str = "diagnostic") -> Path:
    """Render the DOCX report using the appropriate renderer.

    Routing by report_type / project_type:
      diagnostic     → render_diagnostic.render_diagnostic()
      suivi_chantier → render_cr_visite.render_cr() + templates/suivi_chantier.docx
      devis          → render_devis.render_devis()
    """
    script_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(script_dir))

    if report_type == "diagnostic":
        from render_diagnostic import render_diagnostic
        return render_diagnostic(
            context=context,
            photos_dir=str(photos_dir),
            output_path=str(output_path),
        )

    if report_type == "devis":
        from render_devis import render_devis
        return render_devis(
            context=context,
            photos_dir=str(photos_dir),
            output_path=str(output_path),
        )

    if report_type == "suivi_chantier":
        template_path = script_dir / "templates" / "suivi_chantier.docx"
        if not template_path.exists():
            raise SystemExit(f"Template not found: {template_path}")
        from render_cr_visite import render_cr
        return render_cr(
            context=context,
            photos_dir=str(photos_dir),
            output_path=str(output_path),
            template_path=str(template_path),
        )

    raise SystemExit(
        f"Unknown report_type: {report_type!r}\n"
        "Supported values: diagnostic, suivi_chantier, devis"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pull an Edifice mission and generate the DOCX report.",
    )
    parser.add_argument(
        "briefing_file",
        type=Path,
        help="Path to the *.edifice.md briefing file",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: mission/ next to the briefing file)",
    )
    parser.add_argument(
        "--report-type",
        default=None,
        help="Report template to use (default: auto-detect from mission type)",
    )
    parser.add_argument(
        "--pull-only",
        action="store_true",
        help="Pull data only — skip DOCX rendering",
    )
    args = parser.parse_args()

    briefing_path = args.briefing_file.resolve()
    if not briefing_path.exists():
        raise SystemExit(f"File not found: {briefing_path}")

    output_dir = args.output_dir or (briefing_path.parent / "mission")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Parse briefing file
    print(f"Reading briefing file: {briefing_path.name}")
    fm = parse_briefing(briefing_path)
    mission_id = fm["edifice_mission_id"]
    supabase_url = fm.get("supabase_url", "https://zgkvbjqlvebttbnkklpo.supabase.co")

    # 2. Resolve and load credentials
    config_file = resolve_config_file(briefing_path)
    print(f"Looking for credentials at: {config_file}")
    config = load_config(config_file)
    if config is None or "access_token" not in config:
        raise SystemExit(
            f"Credentials not found at: {config_file}\n"
            "Fix options (pick one):\n"
            "  A) Run /edifice pair from Claude Code CLI to store fresh credentials.\n"
            "  B) Place edifice-credentials.json next to the .edifice.md briefing file.\n"
            "  C) Set EDIFICE_CONFIG_PATH=/path/to/config.json env var.\n"
            f"  (Sandbox home detected: {Path.home()})"
        )

    config["supabase_url"] = supabase_url

    # 3. Create authenticated Supabase client
    print("Authenticating with Supabase...")
    supabase = get_supabase_client(config, config_file)
    print("Authenticated.\n")

    # 4. Pull mission data
    context = pull_mission(supabase, mission_id, output_dir)

    if args.pull_only:
        n_obs = len(context.get("observations", []))
        n_photos = len(list((output_dir / "photos").glob("*"))) if (output_dir / "photos").exists() else 0
        print(f"\nDone (pull only). Data in: {output_dir}")
        print(f"  {n_obs} observation(s), {n_photos} photo(s) downloaded")
        print(f"  Context: {output_dir / 'context.json'}")
        return

    # 5. Auto-detect report type from mission type if not specified
    report_type = args.report_type or context.get("project_type", "suivi_chantier")
    print(f"\nRendering report ({report_type})...")
    report_path = output_dir / "rapport.docx"
    render_report(context, output_dir / "photos", report_path, report_type)

    print(f"\nDone. Report: {report_path}")


if __name__ == "__main__":
    main()
