#!/usr/bin/env python3
"""List notes in a vault folder with optional frontmatter filtering.

Usage:
    python list_notes.py "CRM-BlueGreen/Opportunites"
    python list_notes.py "CRM-BlueGreen/Opportunites" --field stage --value "Prospecting"
    python list_notes.py "Taches" --field etat --value "En cours" --limit 10
"""

import argparse
import json
import sys

from obsidian_api import ObsidianAPI


def main():
    parser = argparse.ArgumentParser(description="List notes in a vault folder")
    parser.add_argument("folder", help="Vault-relative folder path")
    parser.add_argument("--field", help="Frontmatter field to filter on")
    parser.add_argument("--value", help="Expected value for the field")
    parser.add_argument("--limit", type=int, default=50, help="Max notes to return")
    args = parser.parse_args()

    if (args.field and not args.value) or (args.value and not args.field):
        parser.error("--field and --value must be used together")

    api = ObsidianAPI()

    try:
        entries = api.list_directory(args.folder)
        md_files = [e for e in entries if isinstance(e, str) and e.endswith(".md")]
        if not md_files:
            # API may return dicts with "path" key
            md_files = [
                e["path"] if isinstance(e, dict) else e
                for e in entries
                if (isinstance(e, dict) and e.get("path", "").endswith(".md"))
                or (isinstance(e, str) and e.endswith(".md"))
            ]

        results = []
        for filepath in md_files:
            if len(results) >= args.limit:
                break

            path = f"{args.folder}/{filepath}" if "/" not in filepath else filepath

            try:
                note = api.read_note(path)
            except Exception:
                continue

            fm = note.get("frontmatter", {}) or {}

            # Apply filter
            if args.field:
                val = fm.get(args.field)
                if val is None:
                    continue
                # Handle list fields (e.g. etiquettes)
                if isinstance(val, list):
                    if args.value not in val:
                        continue
                elif str(val) != args.value:
                    continue

            results.append({
                "path": note.get("path", path),
                "frontmatter": fm,
            })

        print(json.dumps(results, ensure_ascii=False, indent=2))
        print(f"\n# {len(results)} notes returned (of {len(md_files)} in folder)", file=sys.stderr)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
