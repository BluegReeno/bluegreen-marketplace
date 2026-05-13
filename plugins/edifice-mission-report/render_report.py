#!/usr/bin/env python3
"""
render_report.py — Standalone DOCX renderer for IC Ingénieurs Conseils missions.

Reads a local context.json and generates the appropriate DOCX report
based on project_type. No Supabase connection required.

Usage:
    python render_report.py mission/context.json
    python render_report.py mission/context.json --photos-dir mission/photos --output mission/rapport.docx

Supported project types:
    diagnostic      → render_diagnostic.py  (rapport de diagnostic structurel)
    suivi_chantier  → render_cr_visite.py   (compte-rendu de visite de chantier)
    devis           → render_devis.py       (rapport préliminaire / demande de devis)
"""

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

TEMPLATE_SUIVI = SCRIPT_DIR / "templates" / "suivi_chantier.docx"


def render(context: dict, photos_dir: str, output_path: str) -> None:
    project_type = context.get("project_type", "diagnostic")

    if project_type == "diagnostic":
        from render_diagnostic import render_diagnostic
        render_diagnostic(context, photos_dir=photos_dir, output_path=output_path)

    elif project_type == "suivi_chantier":
        if not TEMPLATE_SUIVI.exists():
            raise SystemExit(f"Template not found: {TEMPLATE_SUIVI}")
        from render_cr_visite import render_cr
        render_cr(
            context=context,
            photos_dir=photos_dir,
            output_path=output_path,
            template_path=str(TEMPLATE_SUIVI),
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
    args = parser.parse_args()

    context_path = Path(args.context).resolve()
    if not context_path.exists():
        raise SystemExit(f"Context file not found: {context_path}")

    with open(context_path, encoding="utf-8") as f:
        context = json.load(f)

    photos_dir = args.photos_dir or str(context_path.parent / "photos")
    output_path = args.output or str(context_path.parent / "rapport.docx")

    print(f"Project type : {context.get('project_type', 'diagnostic')}")
    print(f"Photos dir   : {photos_dir}")
    print(f"Output       : {output_path}")
    print()

    render(context, photos_dir=photos_dir, output_path=output_path)


if __name__ == "__main__":
    main()
