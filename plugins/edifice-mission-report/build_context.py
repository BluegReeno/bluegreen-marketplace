#!/usr/bin/env python3
"""
build_context.py — Build context.json from MCP response + download photos.

Reads the raw JSON from get_mission_with_assets, builds a complete
context.json skeleton (all fields for the service_type, even if empty),
and downloads all photos from their signed_urls.

Usage:
    python3 build_context.py <mcp_response.json> <output_dir> [--photos-dir <dir>]
"""

import argparse
import datetime
import json
import pathlib
import sys
import urllib.request


# ---------------------------------------------------------------------------
# Context builders
# ---------------------------------------------------------------------------

def _parse_mission_context(project: dict) -> dict:
    mc = project.get("mission_context") or {}
    if isinstance(mc, str):
        try:
            mc = json.loads(mc)
        except Exception:
            mc = {}
    return mc


def _build_header_diagnostic(project: dict, building: dict | None, mc: dict) -> dict:
    return {
        "project_type": "diagnostic",
        "building_id": project.get("building_id") or "",
        "titre_service": mc.get("titre_service") or project.get("name") or "",
        "client": mc.get("client") or "",
        "residence": mc.get("residence") or (building.get("name") if building else "") or "",
        "adresse": mc.get("adresse") or (building.get("address") if building else "") or "",
        "code_postal_ville": mc.get("code_postal_ville") or "",
        "ref_dossier": mc.get("ref_dossier") or "",
        "date_visite": mc.get("date_visite") or datetime.date.today().isoformat(),
        "description_batiment": (building.get("description") if building else "") or "",
        "objet_visite": mc.get("objet_visite") or "",
        "synthese": mc.get("synthese") or "",
        "conclusion": mc.get("conclusion") or "",
    }


def _build_header_suivi_chantier(project: dict, building: dict | None, mc: dict) -> dict:
    return {
        "project_type": "suivi_chantier",
        "building_id": project.get("building_id") or "",
        "titre_service": mc.get("titre_service") or project.get("name") or "",
        "client": mc.get("client") or "",
        "residence": mc.get("residence") or (building.get("name") if building else "") or "",
        "batiments_visites": mc.get("batiments_visites") or "",
        "adresse": mc.get("adresse") or (building.get("address") if building else "") or "",
        "code_postal_ville": mc.get("code_postal_ville") or "",
        "ref_dossier": mc.get("ref_dossier") or "",
        "date_visite": mc.get("date_visite") or datetime.date.today().isoformat(),
        "participants": mc.get("participants") or [],
        "objet_visite": mc.get("objet_visite") or "",
        "synthese": mc.get("synthese") or "",
        "conclusion": mc.get("conclusion") or "",
    }


def _build_header_devis(project: dict, building: dict | None, mc: dict) -> dict:
    return {
        "project_type": "devis",
        "building_id": project.get("building_id") or "",
        "titre_service": mc.get("titre_service") or project.get("name") or "",
        "client": mc.get("client") or "",
        "type_acteur": mc.get("type_acteur") or "",
        "interlocuteur_nom": mc.get("interlocuteur_nom") or "",
        "interlocuteur_role": mc.get("interlocuteur_role") or "",
        "interlocuteur_contact": mc.get("interlocuteur_contact") or "",
        "adresse": mc.get("adresse") or (building.get("address") if building else "") or "",
        "type_batiment": (building.get("building_type") if building else "") or "",
        "annee_construction": mc.get("annee_construction") or "",
        "nb_etages": mc.get("nb_etages") or "",
        "description_batiment": (building.get("description") if building else "") or "",
        "declencheur": mc.get("declencheur") or "",
        "livrable": mc.get("livrable") or "",
        "urgence": mc.get("urgence") or "Normal",
        "date_visite": mc.get("date_visite") or datetime.date.today().isoformat(),
        "documents_fournis": mc.get("documents_fournis") or [],
        "proposition_mission": mc.get("proposition_mission") or "",
        "incertitudes": mc.get("incertitudes") or "",
        "chiffrage": mc.get("chiffrage") or [
            {"prestation": "Déplacement terrain", "nb_heures": "", "montant_ht": ""},
            {"prestation": "Visite terrain", "nb_heures": "", "montant_ht": ""},
            {"prestation": "Rédaction du rapport", "nb_heures": "", "montant_ht": ""},
        ],
    }


def build_header(project: dict, building: dict | None, project_type: str) -> dict:
    mc = _parse_mission_context(project)
    if project_type == "suivi_chantier":
        return _build_header_suivi_chantier(project, building, mc)
    if project_type == "devis":
        return _build_header_devis(project, building, mc)
    return _build_header_diagnostic(project, building, mc)


def build_observations(notes: list, photos: list, project_type: str) -> list:
    # Index photos by note_id
    photos_by_note: dict[str, list] = {}
    for p in photos:
        nid = p.get("note_id")
        if nid:
            photos_by_note.setdefault(nid, []).append(p)

    obs = []
    for i, note in enumerate(notes):
        nid = note.get("id", "")
        note_photos = photos_by_note.get(nid, [])
        filenames = [
            pathlib.Path(p["storage_path"]).name
            for p in note_photos
            if p.get("storage_path")
        ]

        if project_type == "devis":
            obs.append({
                "ref": f"OBS-{i + 1:02d}",
                "note_id": nid,
                "name": note.get("name") or "",
                "location": note.get("location") or "",
                "description": note.get("description") or "",
                "metadata": {
                    "donnees_cles": "",
                    "ref_photo": filenames[0] if filenames else "",
                },
                "photos": filenames,
                "photo": filenames[0] if filenames else "",
            })
        elif project_type == "suivi_chantier":
            obs.append({
                "ref": f"V1-{i + 1:02d}",
                "note_id": nid,
                "name": note.get("name") or "",
                "location": note.get("location") or "",
                "description": note.get("description") or "",
                "assessment": note.get("assessment") or "",  # observation | a_faire | reserve
                "recommendations": note.get("recommendations") or "",
                "photos": filenames,
                "photo": filenames[0] if filenames else "",
                "metadata": note.get("metadata") or {},
            })
        else:  # diagnostic
            obs.append({
                "ref": f"OBS-{i + 1:02d}",
                "note_id": nid,
                "name": note.get("name") or "",
                "zone": note.get("zone") or "",
                "location": note.get("location") or "",
                "description": note.get("description") or "",
                "assessment": note.get("assessment") or "",  # 1 | 2 | 3 | 4 | -
                "recommendations": note.get("recommendations") or "",
                "photos": filenames,
                "photo": filenames[0] if filenames else "",
                "metadata": note.get("metadata") or {},
            })

    return obs


# ---------------------------------------------------------------------------
# Photo download
# ---------------------------------------------------------------------------

def download_photos(photos: list, photos_dir: pathlib.Path) -> tuple[int, int]:
    photos_dir.mkdir(parents=True, exist_ok=True)
    ok = skipped = 0
    for photo in photos:
        signed_url = photo.get("signed_url")
        storage_path = photo.get("storage_path") or ""
        filename = pathlib.Path(storage_path).name if storage_path else (
            photo.get("original_filename") or photo.get("filename") or ""
        )
        if not signed_url or not filename:
            skipped += 1
            continue
        try:
            urllib.request.urlretrieve(signed_url, photos_dir / filename)
            ok += 1
        except Exception as e:
            print(f"  ✗ {filename}: {e}", file=sys.stderr)
            skipped += 1
    return ok, skipped


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mcp_response", help="Path to mcp_response.json (output of get_mission_with_assets)")
    parser.add_argument("output_dir", help="Directory where context.json is written")
    parser.add_argument("--photos-dir", default=None, help="Directory for photos (default: output_dir/photos)")
    args = parser.parse_args()

    data = json.loads(pathlib.Path(args.mcp_response).read_text(encoding="utf-8"))
    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    photos_dir = pathlib.Path(args.photos_dir) if args.photos_dir else output_dir / "photos"

    project = data.get("project") or {}
    building = data.get("building")
    notes = data.get("notes") or []
    photos = data.get("photos") or []
    project_type = project.get("type") or "diagnostic"

    header = build_header(project, building, project_type)
    observations = build_observations(notes, photos, project_type)

    context = {**header, "observations": observations, "photos": photos}
    context_path = output_dir / "context.json"
    context_path.write_text(json.dumps(context, indent=2, ensure_ascii=False), encoding="utf-8")

    ok, skipped = download_photos(photos, photos_dir)

    # Summary
    print(f"\n✅  context.json → {context_path}")
    print(f"   {len(observations)} observations | {len(photos)} photos ({ok} téléchargées, {skipped} skippées)")
    print(f"   Type : {project_type}")
    print()
    if project_type == "diagnostic":
        print("Champs à remplir avec /edifice improve :")
        print("  header    → description_batiment, objet_visite, synthese, conclusion")
        print("  observations → zone, location, assessment (1-4/-), recommendations")
    elif project_type == "suivi_chantier":
        print("Champs à remplir avec /edifice improve :")
        print("  header    → participants, objet_visite, synthese, conclusion")
        print("  observations → location, assessment (observation/a_faire/reserve), recommendations")
    elif project_type == "devis":
        print("Champs à remplir avec /edifice improve :")
        print("  header    → declencheur, description_batiment, proposition_mission, chiffrage")
        print("  observations → location, description, metadata.donnees_cles")
    print()
    print(f"{'Ref':<8} {'Zone':<15} {'IE':<4} {'Nom':<30} Description")
    print("-" * 80)
    for obs in observations:
        ref = obs.get("ref", "")
        zone = (obs.get("zone") or "")[:14]
        ie = obs.get("assessment") or ""
        name = (obs.get("name") or "")[:29]
        desc = (obs.get("description") or "")[:40]
        print(f"{ref:<8} {zone:<15} {ie:<4} {name:<30} {desc}")


if __name__ == "__main__":
    main()
