#!/usr/bin/env python3
"""
render_cr_visite.py — CR de visite de chantier IC Ingénieurs (docxtpl).

Usage:
    python render_cr_visite.py context.json [--photos-dir ./photos] [--output cr.docx]
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

from docxtpl import DocxTemplate, InlineImage
from docx.shared import Cm

TEMPLATE_PATH = Path(__file__).parent / "templates" / "ic-ingenieurs" / "suivi_chantier.docx"

MOIS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]


def format_date_french(iso: str) -> str:
    try:
        dt = datetime.strptime(iso[:10], "%Y-%m-%d")
        return f"{dt.day} {MOIS_FR[dt.month - 1]} {dt.year}"
    except (ValueError, TypeError):
        return iso or ""


def _build_context(context: dict, photos_dir: str, doc: DocxTemplate) -> dict:
    participants = [
        {
            "nom":        p.get("nom", ""),
            "fonction":   p.get("fonction", ""),
            "entreprise": p.get("entreprise", ""),
            "contact":    p.get("contact", ""),
        }
        for p in context.get("participants", [])
    ]

    observations = []
    for obs in context.get("observations", []):
        photo_file = obs.get("photo", "")
        photo_img = None
        if photo_file:
            path = Path(photos_dir) / photo_file
            if path.exists():
                try:
                    photo_img = InlineImage(doc, str(path), width=Cm(5.0))
                except Exception:
                    photo_img = None
        observation_text = obs.get("description") or obs.get("observation", "")
        action_text = obs.get("recommendations") or obs.get("action", "")
        observation_action = observation_text + ("\n→ " + action_text if action_text else "")
        observations.append({
            "etage_facade":       obs.get("location") or obs.get("etage_facade", ""),
            "observation_action": observation_action,
            "photo":              photo_img,
        })

    date_fr = format_date_french(context.get("date_visite", ""))
    return {
        "service_type":       context.get("service_type", ""),
        "client":             context.get("client", ""),
        "residence":          context.get("residence", ""),
        "complement_adresse": context.get("complement_adresse", ""),
        "adresse":            context.get("adresse", ""),
        "code_postal":        context.get("code_postal", ""),
        "commune":            context.get("commune", ""),
        "dossier":            context.get("dossier", "") or context.get("ref_dossier", ""),
        "date_visite":        date_fr,
        "date_rapport":       date_fr,
        "objet_visite":       context.get("objet_visite", ""),
        "synthese":           context.get("synthese", ""),
        "conclusion":         context.get("conclusion", ""),
        "participants":       participants,
        "observations":       observations,
    }


def render_cr(context: dict, photos_dir: str = ".", output_path: str = "cr_visite.docx",
              template_path: str = None) -> str:
    tpl = template_path or str(TEMPLATE_PATH)
    doc = DocxTemplate(tpl)
    tpl_ctx = _build_context(context, photos_dir, doc)
    doc.render(tpl_ctx)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out))
    n = len(tpl_ctx["observations"])
    print(f"✅ CR Visite : {out}")
    print(f"   {n} observation(s)")
    return str(out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CR Visite IC Ingénieurs")
    parser.add_argument("context", help="context.json")
    parser.add_argument("--photos-dir", default=".", help="Dossier photos")
    parser.add_argument("--output", default="cr_visite.docx", help="Fichier de sortie")
    parser.add_argument("--template", default=None, help="Template path (optionnel)")
    args = parser.parse_args()

    with open(args.context, encoding="utf-8") as f:
        ctx = json.load(f)

    render_cr(ctx, args.photos_dir, args.output, args.template)
