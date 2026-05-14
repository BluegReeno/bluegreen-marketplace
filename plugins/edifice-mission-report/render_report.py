#!/usr/bin/env python3
"""
render_report.py — Standalone DOCX renderer for IC Ingénieurs Conseils missions.

Reads a local context.json and generates the appropriate DOCX report
based on project_type. No Supabase connection required.

Usage:
    python render_report.py mission/context.json
    python render_report.py mission/context.json --photos-dir mission/photos --output mission/rapport.docx
    python render_report.py mission/context.json --org ic-ingenieurs

Supported project types:
    diagnostic      → render_diagnostic.py  (rapport de diagnostic structurel)
    suivi_chantier  → render_cr_visite.py   (compte-rendu de visite de chantier)
    devis           → render_devis.py       (rapport préliminaire / demande de devis)
"""

import argparse
import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PLUGIN_DIR = SCRIPT_DIR
sys.path.insert(0, str(SCRIPT_DIR))


def _template_path(org: str, project_type: str) -> Path:
    path = PLUGIN_DIR / "templates" / org / f"{project_type}.docx"
    if not path.exists():
        raise SystemExit(f"Template not found: {path}\nSet EDIFICE_ORG or use --org flag.")
    return path


def normalize_v1(ctx: dict) -> dict:
    """Upgrade v1.0 context.json to v2.0 format."""
    if ctx.get("edifice_version", "2.0") != "1.0":
        return ctx
    mission = ctx.get("mission", {})
    building = ctx.get("building", {})
    observations = []
    for note in ctx.get("notes", []):
        observations.append({
            "ref": note.get("ref", ""),
            "localisation": "",
            "etage_facade": "",
            "observation": note.get("description", ""),
            "action": "",
            "photo": note.get("photos", [""])[0].replace("photos/", "") if note.get("photos") else "",
        })
    return {
        "edifice_version": "2.0",
        "project_type": mission.get("type", "suivi_chantier"),
        "titre_service": mission.get("name", ""),
        "client": "",
        "residence": building.get("name", ""),
        "adresse": building.get("address", ""),
        "ref_dossier": "",
        "date_visite": (mission.get("visited_at") or "")[:10],
        "participants": [],
        "objet_visite": mission.get("brief", ""),
        "synthese": "",
        "conclusion": "",
        "observations": observations,
    }


def render(context: dict, photos_dir: str, output_path: str, org=None) -> None:
    context = normalize_v1(context)
    org = org or context.get("org") or os.environ.get("EDIFICE_ORG") or "ic-ingenieurs"
    project_type = context.get("project_type", "diagnostic")

    if project_type == "diagnostic":
        from render_diagnostic import render_diagnostic
        render_diagnostic(context, photos_dir=photos_dir, output_path=output_path)

    elif project_type == "suivi_chantier":
        tpl = _template_path(org, "suivi_chantier")
        from render_cr_visite import render_cr
        render_cr(
            context=context,
            photos_dir=photos_dir,
            output_path=output_path,
            template_path=str(tpl),
        )

    elif project_type == "devis":
        from render_devis import render_devis
        render_devis(context, photos_dir=photos_dir, output_path=output_path)

    else:
        raise SystemExit(
            f"Unknown project_type: {project_type!r}\n"
            "Supported values: diagnostic, suivi_chantier, devis"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render an IC Ingénieurs DOCX report from a local context.json."
    )
    parser.add_argument("context", help="Path to context.json")
    parser.add_argument(
        "--photos-dir",
        default=None,
        help="Directory containing photos (default: same directory as context.json)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output .docx path (default: rapport.docx next to context.json)",
    )
    parser.add_argument(
        "--org",
        default=None,
        help="Organisation template set (default: ic-ingenieurs, or EDIFICE_ORG env var)",
    )
    args = parser.parse_args()

    context_path = Path(args.context).resolve()
    if not context_path.exists():
        raise SystemExit(f"Context file not found: {context_path}")

    with open(context_path, encoding="utf-8") as f:
        context = json.load(f)

    photos_dir = args.photos_dir or str(context_path.parent / "photos")
    output_path = args.output or str(context_path.parent / "rapport.docx")

    context_normalized = normalize_v1(context)
    print(f"Project type : {context_normalized.get('project_type', 'diagnostic')}")
    print(f"Photos dir   : {photos_dir}")
    print(f"Output       : {output_path}")
    print(f"Org          : {args.org or os.environ.get('EDIFICE_ORG') or 'ic-ingenieurs (default)'}")
    print()

    render(context, photos_dir=photos_dir, output_path=output_path, org=args.org)


if __name__ == "__main__":
    main()
