#!/usr/bin/env python3
"""
Push updated mission context back to Supabase.

Reads mission/data/context.json and updates edifice_notes for each observation
that has a note_id. Preserves the connection between context edits (made by
/edifice improve) and the Supabase source of truth.

Usage:
    python push_mission.py <path-to-edifice.md> [--mission-dir ./mission]
"""

import argparse
import json
import sys
from pathlib import Path

# Import helpers from pull_mission (same directory)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pull_mission import resolve_config_file, load_config, get_supabase_client, parse_briefing, SupabaseClient


def push_building(supabase: SupabaseClient, building_id: str, context: dict) -> bool:
    """Update edifice_buildings.description if description_batiment was improved."""
    description = (context.get("description_batiment") or "").strip()
    if not building_id or not description:
        return False
    try:
        supabase.update("edifice_buildings", {"description": description}, {"id": building_id})
        print(f"  ✓ Building description updated ({len(description)} chars)")
        return True
    except Exception as exc:
        print(f"  ✗ Building description update failed: {exc}", file=sys.stderr)
        return False


def push_notes(supabase: SupabaseClient, observations: list) -> tuple[int, int]:
    """Update edifice_notes rows from context observations. Returns (updated, skipped)."""
    updated = 0
    skipped = 0

    for obs in observations:
        note_id = obs.get("note_id")
        if not note_id:
            skipped += 1
            continue

        # Build update payload from context fields
        description = obs.get("desordre") or obs.get("observation") or ""
        location = obs.get("localisation") or obs.get("etage_facade") or ""

        # Store devis-specific metadata (zone, ie) in the metadata JSON column
        metadata: dict = {}
        zone = obs.get("zone")
        ie = obs.get("ie")
        if zone:
            metadata["zone"] = zone
        if ie is not None:
            metadata["ie"] = ie

        update_data: dict = {}
        if description:
            update_data["description"] = description
        if location:
            update_data["location"] = location
        if metadata:
            update_data["metadata"] = metadata

        if not update_data:
            skipped += 1
            continue

        try:
            supabase.update("edifice_notes", update_data, {"id": note_id})
            updated += 1
            ref = obs.get("ref") or note_id[:8]
            print(f"  ✓ {ref}: {description[:60]}")
        except Exception as exc:
            ref = obs.get("ref") or note_id[:8]
            print(f"  ✗ {ref}: {exc}", file=sys.stderr)
            skipped += 1

    return updated, skipped


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Push updated context back to Supabase edifice_notes.",
    )
    parser.add_argument(
        "briefing_file",
        type=Path,
        help="Path to the *.edifice.md briefing file",
    )
    parser.add_argument(
        "--mission-dir",
        type=Path,
        default=None,
        help="Mission directory containing context.json (default: mission/ next to briefing)",
    )
    args = parser.parse_args()

    briefing_path = args.briefing_file.resolve()
    if not briefing_path.exists():
        raise SystemExit(f"File not found: {briefing_path}")

    mission_dir = args.mission_dir or (briefing_path.parent / "mission")
    context_path = mission_dir / "context.json"

    if not context_path.exists():
        raise SystemExit(
            f"context.json not found at: {context_path}\n"
            "Run /edifice pull first."
        )

    # Load context
    context = json.loads(context_path.read_text(encoding="utf-8"))
    observations = context.get("observations", [])
    if not observations:
        raise SystemExit("No observations found in context.json.")

    # Auth
    fm = parse_briefing(briefing_path)
    supabase_url = fm.get("supabase_url", "https://zgkvbjqlvebttbnkklpo.supabase.co")

    config_file = resolve_config_file(briefing_path)
    config = load_config(config_file)
    if config is None or "access_token" not in config:
        raise SystemExit(f"Credentials not found at: {config_file}")

    config["supabase_url"] = supabase_url
    print("Authenticating with Supabase...")
    supabase = get_supabase_client(config, config_file)
    print(f"Authenticated. Pushing {len(observations)} observation(s)...\n")

    updated, skipped = push_notes(supabase, observations)

    # Push building description if improved during Cowork session
    building_id = context.get("building_id", "")
    push_building(supabase, building_id, context)

    print(f"\n{'='*40}")
    print(f"Done. {updated} note(s) updated, {skipped} skipped.")
    if skipped:
        print("  (Skipped = no note_id or no changes — normal for /edifice improve placeholders)")


if __name__ == "__main__":
    main()
