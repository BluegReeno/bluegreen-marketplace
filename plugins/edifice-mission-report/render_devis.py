#!/usr/bin/env python3
"""
render_devis.py — Rapport préliminaire / demande de devis IC Ingénieurs (docxtpl).

Usage:
    python render_devis.py context.json [--output rapport_devis.docx]
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

from docxtpl import DocxTemplate

TEMPLATE_PATH = Path(__file__).parent / "templates" / "ic-ingenieurs" / "devis.docx"

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


def _build_context(context: dict) -> dict:
    # Enrich documents_fournis with human-readable fourni_str
    docs = []
    for d in context.get("documents_fournis", []):
        docs.append({
            **d,
            "fourni_str": "Oui" if d.get("fourni") else "Non",
        })

    return {
        "titre_service":         context.get("titre_service", ""),
        "client":                context.get("client", ""),
        "type_acteur":           context.get("type_acteur", ""),
        "interlocuteur_nom":     context.get("interlocuteur_nom", ""),
        "interlocuteur_role":    context.get("interlocuteur_role", ""),
        "interlocuteur_contact": context.get("interlocuteur_contact", ""),
        "type_mission":          context.get("type_mission", ""),
        "declencheur":           context.get("declencheur", ""),
        "livrable":              context.get("livrable", ""),
        "urgence":               context.get("urgence", ""),
        "adresse":               context.get("adresse", ""),
        "type_batiment":         context.get("type_batiment", ""),
        "annee_construction":    context.get("annee_construction", ""),
        "nb_etages":             str(context.get("nb_etages", "")),
        "description_batiment":  context.get("description_batiment", ""),
        "documents_fournis":     docs,
        "observations":          context.get("observations", []),
        "proposition_mission":   context.get("proposition_mission", ""),
        "incertitudes":          context.get("incertitudes", ""),
        "chiffrage":             context.get("chiffrage", []),
        "technicien":            context.get("technicien", ""),
        "date_visite":           format_date_french(context.get("date_visite", "")),
        "date_envoi":            format_date_french(context.get("date_envoi", "")),
    }


def render_devis(context: dict, photos_dir: str = ".", output_path: str = "rapport_devis.docx") -> str:
    doc = DocxTemplate(str(TEMPLATE_PATH))
    tpl_ctx = _build_context(context)
    doc.render(tpl_ctx)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out))
    size_kb = out.stat().st_size / 1024
    print(f"✅ Rapport devis : {out}")
    print(f"   {size_kb:.0f} KB")
    return str(out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rapport devis IC Ingénieurs")
    parser.add_argument("context", help="context.json")
    parser.add_argument("--output", default="rapport_devis.docx", help="Fichier de sortie")
    args = parser.parse_args()

    with open(args.context, encoding="utf-8") as f:
        ctx = json.load(f)

    render_devis(ctx, output_path=args.output)
