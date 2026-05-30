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
import math
import pathlib
import re
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed


# ---------------------------------------------------------------------------
# Context builders
# ---------------------------------------------------------------------------

def _clean_address(addr: str) -> str:
    """Strip BAN geocoder parenthetical suffixes e.g. '5 Place Jean Jaurès (Saint-Denis) 93200'."""
    if not addr:
        return addr
    return re.sub(r'\s*\([^)]*\)', '', addr).strip()


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
        "adresse": _clean_address(mc.get("adresse") or (building.get("address") if building else "") or ""),
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
        "adresse": _clean_address(mc.get("adresse") or (building.get("address") if building else "") or ""),
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
        "adresse": _clean_address(mc.get("adresse") or (building.get("address") if building else "") or ""),
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


# Routing config: which note.type goes into observations[] vs notes[]
# Source of truth: organizations/ic-ingenieurs/assessment-config.json
_OBSERVATION_TYPE = {
    "diagnostic": "disorder",
    "suivi_chantier": "reservation",
    # devis: TBD — all notes go to notes[] for now
}


def _filenames_for_note(note_id: str, photos_by_note: dict) -> list[str]:
    return [
        pathlib.Path(p["storage_path"]).name
        for p in photos_by_note.get(note_id, [])
        if p.get("storage_path")
    ]


def build_observations(notes: list, photos: list, project_type: str) -> tuple[list, list]:
    """Return (observations, free_notes) routed by note.type per service_type."""
    photos_by_note: dict[str, list] = {}
    for p in photos:
        nid = p.get("note_id")
        if nid:
            photos_by_note.setdefault(nid, []).append(p)

    obs_type = _OBSERVATION_TYPE.get(project_type)  # note.type that goes to observations[]
    observations = []
    free_notes = []
    obs_counter = 0

    for note in notes:
        nid = note.get("id", "")
        note_type = note.get("type") or "note"
        filenames = _filenames_for_note(nid, photos_by_note)
        photo = filenames[0] if filenames else ""

        if obs_type and note_type == obs_type:
            obs_counter += 1
            prefix = "V" if project_type == "suivi_chantier" else "OBS"
            entry: dict = {
                "ref": f"{prefix}-{obs_counter:02d}",
                "note_id": nid,
                "name": note.get("name") or "",
                "location": note.get("location") or "",
                "description": note.get("description") or "",
                "assessment": note.get("assessment") or "",
                "recommendations": note.get("recommendations") or "",
                "photos": filenames,
                "photo": photo,
                "metadata": note.get("metadata") or {},
            }
            if project_type == "diagnostic":
                entry["zone"] = note.get("zone") or ""
            observations.append(entry)
        else:
            # Free note — no required fields, kept as-is for context
            free_notes.append({
                "note_id": nid,
                "type": note_type,
                "name": note.get("name") or "",
                "description": note.get("description") or "",
                "photos": filenames,
                "photo": photo,
                "metadata": note.get("metadata") or {},
            })

    return observations, free_notes


# ---------------------------------------------------------------------------
# Building 2D map (download or IGN WMS fallback)
# ---------------------------------------------------------------------------

def _download_building_2d_map(url: str, building_id: str, output_dir: pathlib.Path) -> pathlib.Path | None:
    """Download building_2d_map_url to a local PNG. Return local path or None on failure."""
    dest = output_dir / f"{building_id}_2d_map.png"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            ct = resp.headers.get("Content-Type", "")
            if "xml" in ct or "text" in ct:
                print(f"[build_context] Unexpected content-type for 2D map: {ct}", file=sys.stderr)
                return None
            dest.write_bytes(resp.read())
        return dest
    except Exception as e:
        print(f"[build_context] Warning: could not download 2D map: {e}", file=sys.stderr)
        return None


def _generate_ign_map(lat: float, lon: float, output_path: pathlib.Path, radius_m: int = 300) -> pathlib.Path | None:
    """Generate an IGN WMS GetMap PNG from GPS coordinates. Return local path or None on failure."""
    delta_lat = radius_m / 111320
    delta_lon = radius_m / (111320 * math.cos(math.radians(lat)))
    # WMS 1.3.0 + EPSG:4326 bbox order: minLat, minLon, maxLat, maxLon
    bbox = f"{lat - delta_lat},{lon - delta_lon},{lat + delta_lat},{lon + delta_lon}"
    params = {
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "REQUEST": "GetMap",
        "LAYERS": "GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2",
        "FORMAT": "image/png",
        "CRS": "EPSG:4326",
        "BBOX": bbox,
        "WIDTH": "800",
        "HEIGHT": "600",
        "STYLES": "",
    }
    url = "https://data.geopf.fr/wms-r?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            ct = resp.headers.get("Content-Type", "")
            if "xml" in ct or "text" in ct:
                body = resp.read(500).decode("utf-8", errors="replace")
                print(f"[build_context] IGN WMS error: {body[:200]}", file=sys.stderr)
                return None
            output_path.write_bytes(resp.read())
        return output_path
    except Exception as e:
        print(f"[build_context] Warning: IGN WMS fallback failed: {e}", file=sys.stderr)
        return None


def build_building_context(building: dict | None, output_dir: pathlib.Path) -> dict | None:
    """Build the building context section with local 2D map path.

    Strategy:
      1. If `building_2d_map_url` is set → download it.
      2. Else if `latitude` + `longitude` are set → generate via IGN WMS.
      3. Else → image_2d is None (template block is skipped).
    """
    if not building:
        return None
    bid = building.get("id") or "building"
    url = building.get("building_2d_map_url")
    lat = building.get("latitude")
    lon = building.get("longitude")

    image_2d: pathlib.Path | None = None
    if url:
        image_2d = _download_building_2d_map(url, bid, output_dir)
        if image_2d is None and lat is not None and lon is not None:
            print(f"[build_context] Download failed for 2D map, falling back to IGN WMS for {bid}", file=sys.stderr)
            image_2d = _generate_ign_map(float(lat), float(lon), output_dir / f"{bid}_2d_map_auto.png")
    elif lat is not None and lon is not None:
        print(f"[build_context] building_2d_map_url absent — fallback IGN WMS for {bid}", file=sys.stderr)
        image_2d = _generate_ign_map(float(lat), float(lon), output_dir / f"{bid}_2d_map_auto.png")

    return {
        "image_2d": str(image_2d) if image_2d else None,
        "image_2d_url": url,
    }


# ---------------------------------------------------------------------------
# Photo download
# ---------------------------------------------------------------------------

def _download_one(photo: dict, photos_dir: pathlib.Path) -> tuple[str, bool, str]:
    signed_url = photo.get("signed_url")
    storage_path = photo.get("storage_path") or ""
    filename = pathlib.Path(storage_path).name if storage_path else (
        photo.get("original_filename") or photo.get("filename") or ""
    )
    if not signed_url or not filename:
        return filename, False, "missing url or filename"
    dest = photos_dir / filename
    if dest.exists():
        return filename, True, "already exists"
    try:
        urllib.request.urlretrieve(signed_url, dest)
        return filename, True, ""
    except Exception as e:
        return filename, False, str(e)


def download_photos(photos: list, photos_dir: pathlib.Path, workers: int = 8) -> tuple[int, int]:
    photos_dir.mkdir(parents=True, exist_ok=True)
    ok = skipped = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_download_one, p, photos_dir): p for p in photos}
        for future in as_completed(futures):
            filename, success, err = future.result()
            if success:
                ok += 1
            else:
                if err:
                    print(f"  ✗ {filename}: {err}", file=sys.stderr)
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
    observations, free_notes = build_observations(notes, photos, project_type)
    building_ctx = build_building_context(building, output_dir)

    context = {**header, "observations": observations, "notes": free_notes, "photos": photos}
    if building_ctx is not None:
        context["building"] = building_ctx
    context_path = output_dir / "context.json"
    context_path.write_text(json.dumps(context, indent=2, ensure_ascii=False), encoding="utf-8")

    ok, skipped = download_photos(photos, photos_dir)

    # Summary
    print(f"\n✅  context.json → {context_path}")
    print(f"   Type : {project_type}")
    print(f"   {len(observations)} observation(s) structurée(s) | {len(free_notes)} note(s) libre(s) | {len(photos)} photo(s) ({ok} téléchargées, {skipped} skippées)")

    if project_type == "diagnostic":
        print("\nObservations (désordres) — à qualifier avec /edifice improve :")
        print(f"  → zone, location, assessment (1=critique … 4=bon / -=N/A), recommendations")
        if free_notes:
            print(f"\nNotes libres ({len(free_notes)}) — contexte, rappels, non structurées :")
            for n in free_notes:
                print(f"  · {(n.get('name') or '')[:50]}  [{n.get('type','')}]")
    elif project_type == "suivi_chantier":
        print("\nObservations (réservations) — à qualifier avec /edifice improve :")
        print(f"  → location, assessment (observation / a_faire / reserve), recommendations")
        if free_notes:
            print(f"\nNotes libres ({len(free_notes)}) — points généraux :")
            for n in free_notes:
                print(f"  · {(n.get('name') or '')[:50]}")
    elif project_type == "devis":
        print("\nNotes — structure à définir lors du premier devis.")

    if observations:
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
