#!/usr/bin/env python3
"""
render_diagnostic.py — Rapport de diagnostic structurel IC Ingénieurs (docxtpl).

Usage:
    python render_diagnostic.py context.json [--photos-dir ./photos] [--output rapport.docx]
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

from docxtpl import DocxTemplate, InlineImage
from docx.shared import Cm

TEMPLATE_PATH = Path(__file__).parent / "templates" / "ic-ingenieurs" / "diagnostic.docx"

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
    # Accept both Edifice observations[] and IC direct disorders[]
    raw_list = context.get("disorders") or context.get("observations", [])
    disorders = []
    for obs in raw_list:
        photos_raw = obs.get("photos") or ([obs.get("photo")] if obs.get("photo") else [])
        # photos may be dicts {"path": ...} or plain strings
        photo_paths = []
        for p in photos_raw:
            if isinstance(p, dict):
                photo_paths.append(p.get("path", ""))
            else:
                photo_paths.append(str(p))

        photos_img = []
        for p in photo_paths[:4]:
            path = Path(photos_dir) / str(p)
            if path.exists():
                try:
                    photos_img.append(InlineImage(doc, str(path), width=Cm(7.5)))
                except Exception:
                    photos_img.append(None)
            else:
                photos_img.append(None)
        while len(photos_img) < 4:
            photos_img.append(None)

        disorders.append({
            "ref":             obs.get("ref", ""),
            "name":            obs.get("name") or obs.get("desordre", ""),
            "location":        obs.get("location") or obs.get("localisation") or obs.get("zone", ""),
            "description":     obs.get("description") or obs.get("observation") or obs.get("desordre", ""),
            "cause":           obs.get("cause", ""),
            "recommendations": obs.get("recommendations") or obs.get("action", ""),
            "ie":              str(obs.get("ie", "")) if obs.get("ie") is not None else "",
            "photo1": photos_img[0],
            "photo2": photos_img[1],
            "photo3": photos_img[2],
            "photo4": photos_img[3],
        })

    return {
        "service_type":          context.get("titre_service", ""),
        "client":                context.get("client", ""),
        "residence":             context.get("residence", ""),
        "adresse":               context.get("adresse", ""),
        "complement_adresse":    "",
        "code_postal":           "",
        "commune":               "",
        "dossier":               context.get("ref_dossier", ""),
        "date_rapport":          format_date_french(context.get("date_visite", "")),
        "contexte":              context.get("objet_visite", ""),
        "description_batiment":  context.get("description_batiment", ""),
        "construction_era":      context.get("construction_era", ""),
        "construction_type":     context.get("construction_type", ""),
        "n_etage":               context.get("n_etage", ""),
        "utilisation":           context.get("utilisation", ""),
        "detail_visite":         context.get("detail_visite", ""),
        "investigation_methods": context.get("investigation_methods", ""),
        "disorders":             disorders,
        "conclusions":           context.get("synthese", ""),
        "recommandations":       context.get("conclusion", ""),
    }


def render_diagnostic(context: dict, photos_dir: str = ".", output_path: str = "rapport_diagnostic.docx") -> str:
    doc = DocxTemplate(str(TEMPLATE_PATH))
    tpl_ctx = _build_context(context, photos_dir, doc)
    doc.render(tpl_ctx)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out))
    n = len(tpl_ctx["disorders"])
    size_kb = out.stat().st_size / 1024
    print(f"✅ Rapport diagnostic : {out}")
    print(f"   {n} désordre(s) | {size_kb:.0f} KB")
    return str(out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rapport diagnostic IC Ingénieurs")
    parser.add_argument("context", help="context.json")
    parser.add_argument("--photos-dir", default=".", help="Dossier photos")
    parser.add_argument("--output", default="rapport_diagnostic.docx", help="Fichier de sortie")
    args = parser.parse_args()

    with open(args.context, encoding="utf-8") as f:
        ctx = json.load(f)

    render_diagnostic(ctx, args.photos_dir, args.output)
