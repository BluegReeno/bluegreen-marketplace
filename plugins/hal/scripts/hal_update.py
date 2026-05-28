#!/usr/bin/env python3
"""hal_update.py — Natural-language updates to the Obsidian SecondLife vault.

Pipeline:
    1. PARSE   — extract entity + intent + value from free-form text
    2. RESOLVE — locate the target note (search_vault.py + rapidfuzz)
    3. PLAN    — build the list of frontmatter writes
    4. CONFIRM — print the plan (skip if --force or unambiguous match)
    5. WRITE   — call update_frontmatter.py for each write
    6. REPORT  — one line per change

Usage:
    python hal_update.py --vault <path> --text "<user instruction>"
    python hal_update.py --vault <path> --text "..." --dry-run
    python hal_update.py --vault <path> --text "..." --force
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OBSIDIAN_SCRIPTS = SCRIPT_DIR / "obsidian"


FOLDER_HINTS = {
    "candidature": "CRM-JobSearch",
    "poste": "CRM-JobSearch",
    "entretien": "CRM-JobSearch",
    "client": "CRM-BlueGreen",
    "propale": "CRM-BlueGreen",
    "devis": "CRM-BlueGreen",
    "mission": "CRM-BlueGreen",
    "tâche": "Taches",
    "tache": "Taches",
    "faire": "Taches",
    "task": "Taches",
}


def _parse_date(s: str) -> str:
    """Normalize a date string to YYYY-MM-DD."""
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return s
    parts = s.split("/")
    if len(parts) == 2:
        d, m = parts
        y = datetime.now().year
    elif len(parts) == 3:
        d, m, y = parts
        if len(y) == 2:
            y = "20" + y
    else:
        return s
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"


DATE_RE = r"(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}(?:/\d{2,4})?)"


def detect_intent(text: str) -> list[dict]:
    """Return a list of {field, value} writes derived from the user text."""
    writes: list[dict] = []
    lower = text.lower()

    m = re.search(rf"(?:rdv|entretien)\s+(?:pr[ée]vu\s+)?(?:le\s+)?{DATE_RE}", lower)
    if m:
        writes.append({"field": "prochain_rdv", "value": _parse_date(m.group(1))})
        writes.append({"field": "statut", "value": "📞 Entretien prévu"})
        return writes

    m = re.search(rf"relance(?:r)?\s+(?:le\s+)?{DATE_RE}", lower)
    if m:
        writes.append({"field": "date_relance", "value": _parse_date(m.group(1))})
        return writes

    if re.search(r"\b(refus|dead|pas retenu)\b", lower):
        writes.append({"field": "statut", "value": "❌ Refus"})
        return writes

    if "offre reçue" in lower or "offre recue" in lower:
        writes.append({"field": "statut", "value": "✅ Offre reçue"})
        return writes

    if re.search(r"\b(termin[ée]|fait|done)\b", lower):
        writes.append({"field": "etat", "value": "Terminé"})
        return writes

    if "pas de contact" in lower or "candidature plateforme" in lower:
        writes.append({"field": "date_relance", "value": ""})
        return writes

    return writes


def detect_folder_hint(text: str) -> str | None:
    lower = text.lower()
    for kw, folder in FOLDER_HINTS.items():
        if kw in lower:
            return folder
    return None


def extract_entity(text: str) -> str:
    """Heuristic: best guess at the note's title from free text."""
    q = re.search(r'"([^"]+)"', text)
    if q:
        return q.group(1)
    caps = re.findall(r"\b[A-Z][a-zA-ZÀ-ÿ&'-]+(?:\s+[A-Z][a-zA-ZÀ-ÿ&'-]+)*\b", text)
    if caps:
        return max(caps, key=len)
    words = text.split()
    return " ".join(words[:3])


def search_vault(query: str, vault: str) -> list[dict]:
    env = {**os.environ, "OBSIDIAN_VAULT_PATH": vault}
    cmd = ["python3", str(OBSIDIAN_SCRIPTS / "search_vault.py"), query, "--limit", "10"]
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if r.returncode != 0:
        print(f"search_vault.py failed: {r.stderr}", file=sys.stderr)
        return []
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError as e:
        print(f"search_vault.py output parse error: {e} — raw: {r.stdout[:200]!r}", file=sys.stderr)
        return []


def fuzzy_rank(entity: str, candidates: list[dict]) -> list[dict]:
    """Re-rank search_vault.py results with rapidfuzz on filename stems."""
    if not candidates:
        return []
    try:
        from rapidfuzz import fuzz, process
    except ImportError:
        return [
            {"path": c.get("filename"), "score": float(c.get("score", 0)) * 10, "title": Path(c.get("filename", "")).stem}
            for c in candidates
        ]
    titles = [Path(c["filename"]).stem for c in candidates]
    ranked = process.extract(entity, titles, scorer=fuzz.WRatio, limit=len(titles))
    by_title = {title: score for title, score, _ in ranked}
    out = []
    for c in candidates:
        title = Path(c["filename"]).stem
        out.append({"path": c["filename"], "score": by_title.get(title, 0.0), "title": title})
    out.sort(key=lambda x: x["score"], reverse=True)
    return out


def update_field(path: str, field: str, value, vault: str) -> dict:
    env = {**os.environ, "OBSIDIAN_VAULT_PATH": vault}
    cmd = ["python3", str(OBSIDIAN_SCRIPTS / "update_frontmatter.py"), path, field, str(value)]
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if r.returncode != 0:
        return {"ok": False, "error": r.stderr.strip()}
    try:
        return {"ok": True, **json.loads(r.stdout)}
    except json.JSONDecodeError:
        return {"ok": True, "stdout": r.stdout}


def main():
    parser = argparse.ArgumentParser(description="Update the Obsidian vault from natural language")
    parser.add_argument("--vault", required=True, help="Path to the Obsidian vault root")
    parser.add_argument("--text", required=True, help="User instruction (verbatim)")
    parser.add_argument("--force", action="store_true", help="Skip confirmation on ambiguous matches")
    parser.add_argument("--dry-run", action="store_true", help="Print the plan without writing")
    args = parser.parse_args()

    if not Path(args.vault).exists():
        print(f"ERROR: vault not found: {args.vault}", file=sys.stderr)
        sys.exit(1)

    folder_hint = detect_folder_hint(args.text)
    entity = extract_entity(args.text)
    writes = detect_intent(args.text)

    print(f"📝 Text: {args.text}")
    print(f"🎯 Entity: {entity}")
    print(f"📁 Folder hint: {folder_hint or '(none)'}")
    print(f"✏️  Writes: {len(writes)}")

    if not writes:
        print("⚠️  No actionable intent detected. Exiting.")
        return

    candidates = search_vault(entity, args.vault)
    if folder_hint:
        filtered = [c for c in candidates if c.get("filename", "").startswith(folder_hint + "/")]
        if filtered:
            candidates = filtered

    scored = fuzzy_rank(entity, candidates)

    if not scored:
        print(f"❌ Note introuvable pour: {entity}")
        print("   Proposition: créer une nouvelle note (action manuelle requise).")
        return

    top = scored[0]
    print(f"🔍 Top match: {top['title']} (score {top['score']:.0f}) → {top['path']}")

    if top["score"] < 50:
        print(f"❌ Score trop bas ({top['score']:.0f} < 50). Note probablement absente.")
        print("   Proposition: créer la note manuellement.")
        return

    if top["score"] < 80 and not args.force:
        print("⚠️  Match ambigu. Candidats :")
        for c in scored[:3]:
            print(f"   - {c['title']} (score {c['score']:.0f}) → {c['path']}")
        print("   Re-lancer avec --force pour appliquer au top match.")
        return

    target = top["path"]
    print(f"\n📋 Plan ({len(writes)} write(s)) sur {target}:")
    for w in writes:
        print(f"   {target} → {w['field']}: {w['value']}")

    if args.dry_run:
        print("\n🔎 Dry-run — aucun write effectué.")
        return

    print("")
    for w in writes:
        result = update_field(target, w["field"], w["value"], args.vault)
        if result.get("ok"):
            print(f"✅ {target} → {w['field']}: {w['value']}")
        else:
            print(f"❌ {target} → {w['field']}: {result.get('error')}")


if __name__ == "__main__":
    main()
