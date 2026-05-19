#!/usr/bin/env python3
"""Download mission photos from signed URLs in context.json.

Usage:
    python download_photos.py <context.json> <output_dir>
"""
import json
import sys
import urllib.request
from pathlib import Path

context = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
output_dir = Path(sys.argv[2])
output_dir.mkdir(parents=True, exist_ok=True)

ok = skipped = 0
for photo in context.get("photos", []):
    signed_url = photo.get("signed_url")
    storage_path = photo.get("storage_path", "")
    filename = Path(storage_path).name if storage_path else photo.get("filename", "")
    if not signed_url or not filename:
        skipped += 1
        continue
    try:
        urllib.request.urlretrieve(signed_url, output_dir / filename)
        print(f"  ok {filename}")
        ok += 1
    except Exception as e:
        print(f"  fail {filename}: {e}", file=sys.stderr)
        skipped += 1

print(f"\n{ok} photo(s) downloaded, {skipped} skipped.")
