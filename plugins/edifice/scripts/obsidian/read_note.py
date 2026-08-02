#!/usr/bin/env python3
"""Read an Obsidian note and output parsed JSON.

Usage:
    python read_note.py "CRM-BlueGreen/Contacts/Jean Dupont.md"
    python read_note.py "Welcome.md" --raw
"""

import argparse
import json
import sys

from obsidian_api import ObsidianAPI


def main():
    parser = argparse.ArgumentParser(description="Read a note from the Obsidian vault")
    parser.add_argument("path", help="Vault-relative path to the note")
    parser.add_argument("--raw", action="store_true", help="Output raw markdown instead of JSON")
    args = parser.parse_args()

    api = ObsidianAPI()

    try:
        if args.raw:
            print(api.read_raw(args.path))
        else:
            note = api.read_note(args.path)
            print(json.dumps(note, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
