#!/usr/bin/env python3
"""Create a CRM note from JSON input.

Reads JSON from stdin with: name, type, folder, fields.
Generates proper YAML frontmatter (no PyYAML) and creates the note.

Usage:
    echo '{"name":"Jean Dupont","type":"contact-bg","folder":"CRM-BlueGreen/Contacts","fields":{"entreprise":"[[TotalEnergies]]","poste":"CTO"}}' | python create_note.py
    echo '{"name":"Deal XYZ","type":"opportunite-bg","folder":"CRM-BlueGreen/Opportunites","fields":{"stage":"Prospecting","entreprise":"[[Acme]]"},"body":"## Notes\\n\\nFirst meeting went well."}' | python create_note.py
"""

import json
import re
import sys
import unicodedata

from note_schemas import get_schema, validate_create
from obsidian_api import ObsidianAPI


def sanitize_filename(name: str) -> str:
    """Sanitize a string for use as a filename."""
    name = unicodedata.normalize("NFC", name)
    name = re.sub(r'[<>:"/\\|?*]', "-", name)
    name = re.sub(r"\s+", " ", name).strip()
    name = name.strip(".")
    return name[:200] if name else "Untitled"


def yaml_value(value: object) -> str:
    """Format a Python value as YAML, using double quotes for strings."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        if not value:
            return "[]"
        items = [f"  - {yaml_value(v)}" for v in value]
        return "\n" + "\n".join(items)
    s = str(value)
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def dict_to_yaml(d: dict) -> str:
    """Convert a dict to YAML frontmatter string."""
    lines = []
    for key, value in d.items():
        formatted = yaml_value(value)
        if formatted.startswith("\n"):
            lines.append(f"{key}:{formatted}")
        else:
            lines.append(f"{key}: {formatted}")
    return "\n".join(lines)


def main():
    raw = sys.stdin.read().strip()
    if not raw:
        print("Error: no JSON input on stdin", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    name = data.get("name")
    note_type = data.get("type")
    folder = data.get("folder")
    fields = data.get("fields", {})
    body = data.get("body", "")

    if not name or not note_type or not folder:
        print("Error: name, type, and folder are required", file=sys.stderr)
        sys.exit(1)

    # Validate fields against schema
    result = validate_create(note_type, fields)
    for w in result.warnings:
        print(f"Warning: {w}", file=sys.stderr)
    if not result.ok:
        for e in result.errors:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Auto-generate body sections if none provided
    schema = get_schema(note_type)
    if schema and schema.body_sections and not body:
        body = "\n\n".join(f"{h}\n" for h in schema.body_sections)

    # Build frontmatter
    fm = {"type": note_type}
    fm.update(fields)

    frontmatter = dict_to_yaml(fm)
    content = f"---\n{frontmatter}\n---\n"
    if body:
        content += f"\n{body}\n"

    # Build path
    filename = sanitize_filename(name)
    path = f"{folder}/{filename}.md"

    api = ObsidianAPI()

    try:
        api.create_note(path, content, overwrite=False)
        print(json.dumps({"created": path}, ensure_ascii=False))
    except FileExistsError:
        print(f"Error: note already exists: {path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
