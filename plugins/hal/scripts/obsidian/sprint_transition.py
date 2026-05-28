#!/usr/bin/env python3
"""Sprint transition — close current sprint, promote next, carry over tasks.

Pipeline: Passés → Dernier → Actuel → Suivant → À venir

Actions:
  1. "Dernier" → "Passés"
  2. "Actuel" → "Dernier" (carry over incomplete tasks to new Actuel)
  3. "Suivant" → "Actuel" (set dates to next Monday)
  4. "À venir" → "Suivant"
  5. Create new sprint at the end as "À venir"

Usage:
    python sprint_transition.py              # run transition
    python sprint_transition.py --dry-run    # preview without changes
"""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta

from obsidian_api import ObsidianAPI


def next_monday(from_date=None):
    """Return next Monday as YYYY-MM-DD string (returns today if today is Monday)."""
    d = from_date or datetime.now().date()
    days_ahead = (7 - d.weekday()) % 7  # 0 on Monday → returns today
    return (d + timedelta(days=days_ahead)).isoformat()


def find_sprints_by_etat(api):
    """Find all sprints grouped by etat."""
    files = api.list_directory("Sprints")
    sprints = {}  # etat -> list of (name, number, path)
    for f in files:
        if not f.endswith(".md"):
            continue
        path = f"Sprints/{f}"
        try:
            note = api.read_note(path)
        except Exception:
            continue
        fm = note.get("frontmatter", {}) or {}
        etat = fm.get("etat", "")
        name = f.replace(".md", "")
        # Extract sprint number
        m = re.search(r"(\d+)", name)
        number = int(m.group(1)) if m else 0
        sprints.setdefault(etat, []).append({
            "name": name,
            "number": number,
            "path": path,
            "frontmatter": fm,
        })
    # Sort each group by number
    for etat in sprints:
        sprints[etat].sort(key=lambda s: s["number"])
    return sprints


def find_tasks_for_sprint(api, sprint_name):
    """Find all tasks linked to a sprint via the cycle field."""
    files = api.list_directory("Taches")
    tasks = []
    for f in files:
        if not f.endswith(".md"):
            continue
        path = f"Taches/{f}"
        try:
            note = api.read_note(path)
        except Exception:
            continue
        fm = note.get("frontmatter", {}) or {}
        cycle = str(fm.get("cycle", ""))
        # Match specific sprint (e.g. "Sprint 43") but not generic "Sprint"
        if cycle and sprint_name in cycle and re.search(r"Sprint \d+", cycle):
            tasks.append({
                "name": f.replace(".md", ""),
                "path": path,
                "etat": fm.get("etat", ""),
                "frontmatter": fm,
            })
    return tasks


def main():
    parser = argparse.ArgumentParser(description="Sprint transition")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview changes without applying them")
    args = parser.parse_args()

    try:
        api = ObsidianAPI()
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
    dry = args.dry_run
    actions = []

    # Find all sprints by etat
    sprints = find_sprints_by_etat(api)

    actuel = sprints.get("Actuel", [])
    dernier = sprints.get("Dernier", [])
    suivant = sprints.get("Suivant", [])
    a_venir = sprints.get("À venir", [])

    if not actuel:
        print(json.dumps({"error": "No sprint with etat 'Actuel' found"},
                          ensure_ascii=False))
        sys.exit(1)

    current = actuel[0]
    print(f"Current sprint: {current['name']} (etat: Actuel)", file=sys.stderr)

    # --- Step 1: Dernier → Passés ---
    for s in dernier:
        actions.append(f"  {s['name']}: Dernier → Passés")
        if not dry:
            api.update_field(s["path"], "etat", "Passés")

    # --- Step 2: Actuel → Dernier ---
    actions.append(f"  {current['name']}: Actuel → Dernier")
    if not dry:
        api.update_field(current["path"], "etat", "Dernier")

    # --- Step 3: Suivant → Actuel (set dates) ---
    new_actuel = None
    if suivant:
        new_actuel = suivant[0]
        monday = next_monday()
        actions.append(f"  {new_actuel['name']}: Suivant → Actuel (dates: {monday})")
        if not dry:
            api.update_field(new_actuel["path"], "etat", "Actuel")
            api.update_field(new_actuel["path"], "dates", monday)
    else:
        # No "Suivant" sprint — create one
        new_number = current["number"] + 1
        new_name = f"Sprint {new_number}"
        new_id = f"QDBS-{new_number + 1}"
        monday = next_monday()
        new_path = f"Sprints/{new_name}.md"
        actions.append(f"  Create {new_name} (Actuel, dates: {monday})")
        if not dry:
            content = (
                f"---\n"
                f"type: \"sprint\"\n"
                f"id_sprint: \"{new_id}\"\n"
                f"dates: \"{monday}\"\n"
                f"etat: \"Actuel\"\n"
                f"---\n"
            )
            api.create_note(new_path, content)
        new_actuel = {"name": new_name, "number": new_number, "path": new_path}

    # --- Step 4: À venir → Suivant ---
    for s in a_venir:
        actions.append(f"  {s['name']}: À venir → Suivant")
        if not dry:
            api.update_field(s["path"], "etat", "Suivant")

    # --- Step 5: Create new "À venir" sprint ---
    # Find highest sprint number
    all_numbers = []
    for group in sprints.values():
        all_numbers.extend(s["number"] for s in group)
    if new_actuel and new_actuel["number"] not in all_numbers:
        all_numbers.append(new_actuel["number"])
    max_number = max(all_numbers) if all_numbers else current["number"]
    new_av_number = max_number + 1
    new_av_name = f"Sprint {new_av_number}"
    new_av_path = f"Sprints/{new_av_name}.md"
    new_av_id = f"QDBS-{new_av_number + 1}"

    if not api.note_exists(new_av_path):
        actions.append(f"  Create {new_av_name} (À venir)")
        if not dry:
            content = (
                f"---\n"
                f"type: \"sprint\"\n"
                f"id_sprint: \"{new_av_id}\"\n"
                f"etat: \"À venir\"\n"
                f"---\n"
            )
            api.create_note(new_av_path, content)

    # --- Step 6: Carry over incomplete tasks ---
    done_states = {"Terminé", "Archivé"}
    tasks = find_tasks_for_sprint(api, current["name"])
    completed_tasks = [t for t in tasks if t["etat"] in done_states]
    open_tasks = [t for t in tasks if t["etat"] not in done_states]

    new_sprint_name = new_actuel["name"] if new_actuel else f"Sprint {current['number'] + 1}"
    new_cycle = f"[[{new_sprint_name}]]"

    for t in open_tasks:
        actions.append(f"  Task \"{t['name']}\": cycle → {new_cycle}")
        if not dry:
            api.update_field(t["path"], "cycle", new_cycle)

    # --- Summary ---
    result = {
        "previous_sprint": current["name"],
        "new_sprint": new_sprint_name,
        "tasks_completed": len(completed_tasks),
        "tasks_carried_over": len(open_tasks),
        "dry_run": dry,
        "actions": actions,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
