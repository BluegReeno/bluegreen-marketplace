#!/usr/bin/env python3
"""Search the Obsidian vault using text or Dataview DQL.

Usage:
    python search_vault.py "TotalEnergies"
    python search_vault.py "TotalEnergies" --limit 5
    python search_vault.py --dql 'TABLE statut, entreprise FROM "CRM-JobSearch/Opportunites" WHERE statut != "❌ Refus" SORT date_candidature DESC'
"""

import argparse
import json
import sys

from obsidian_api import ObsidianAPI


def main():
    parser = argparse.ArgumentParser(description="Search the Obsidian vault")
    parser.add_argument("query", nargs="?", help="Text search query")
    parser.add_argument("--dql", help="Dataview DQL query (instead of text search)")
    parser.add_argument("--limit", type=int, default=20, help="Max results for text search")
    parser.add_argument("--context", type=int, default=200, help="Context length for text matches")
    args = parser.parse_args()

    if not args.query and not args.dql:
        parser.error("Provide a text query or --dql")

    api = ObsidianAPI()

    try:
        if args.dql:
            results = api.search_dql(args.dql)
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            results = api.search_simple(args.query, context_length=args.context)
            # Limit results
            results = results[: args.limit]
            # Compact output: filename + score + first match context
            output = []
            for r in results:
                entry = {"filename": r["filename"], "score": r.get("score", 0)}
                matches = r.get("matches", [])
                if matches:
                    entry["first_match"] = matches[0].get("context", "")[:300]
                output.append(entry)
            print(json.dumps(output, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
