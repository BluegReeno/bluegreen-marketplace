#!/usr/bin/env bash
# Enforce the two-field version invariant for every plugin:
#   1. plugin.json.version == marketplace.json plugin entry version
#   2. CHANGELOG.md has a "## [<version>]" entry for that version
# Usage: ./scripts/check_version_sync.sh
# Exit 0 = all plugins in sync with a matching CHANGELOG entry. Exit 1 = any failure.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MARKETPLACE="$REPO_ROOT/.claude-plugin/marketplace.json"
ERRORS=0

for plugin_json in "$REPO_ROOT"/plugins/*/.claude-plugin/plugin.json; do
  plugin_dir="$(dirname "$(dirname "$plugin_json")")"
  plugin_name="$(basename "$plugin_dir")"
  plugin_ver="$(python3 -c "import json; print(json.load(open('$plugin_json'))['version'])" 2>/dev/null || echo "READ_ERROR")"
  if [ "$plugin_ver" = "READ_ERROR" ]; then
    echo "ERROR    [$plugin_name] cannot read 'version' from plugin.json (missing key or malformed JSON)"
    ERRORS=$((ERRORS + 1))
    continue
  fi

  # 1. plugin.json must match the marketplace plugin entry.
  # A broken marketplace.json prints PARSE_ERROR; a valid file with no entry prints NOT_FOUND.
  market_ver="$(python3 -c "
import json
try:
    data = json.load(open('$MARKETPLACE'))
except Exception:
    print('PARSE_ERROR'); raise SystemExit(0)
plugins = data.get('plugins', data) if isinstance(data, dict) else data
entry = next((p for p in plugins if p.get('name','').lower() == '$plugin_name' or p.get('id','').lower() == '$plugin_name'), None)
print(entry['version'] if entry else 'NOT_FOUND')
" 2>/dev/null || echo "PARSE_ERROR")"

  if [ "$market_ver" = "PARSE_ERROR" ]; then
    echo "ERROR    [$plugin_name] cannot parse marketplace.json (malformed/unreadable)"
    ERRORS=$((ERRORS + 1))
  elif [ "$market_ver" = "NOT_FOUND" ]; then
    echo "ERROR    [$plugin_name] no matching entry in marketplace.json"
    ERRORS=$((ERRORS + 1))
  elif [ "$market_ver" != "$plugin_ver" ]; then
    echo "MISMATCH [$plugin_name] plugin.json=$plugin_ver marketplace.json=$market_ver"
    ERRORS=$((ERRORS + 1))
  else
    echo "OK       [$plugin_name] v$plugin_ver"
  fi

  # 2. CHANGELOG.md must carry a "## [<plugin_ver>]" entry for this version.
  changelog="$plugin_dir/CHANGELOG.md"
  if [ ! -f "$changelog" ]; then
    echo "ERROR    [$plugin_name] missing CHANGELOG.md"
    ERRORS=$((ERRORS + 1))
  elif ! grep -qE "^## \[${plugin_ver}\]" "$changelog"; then
    echo "ERROR    [$plugin_name] CHANGELOG.md has no '## [$plugin_ver]' entry"
    ERRORS=$((ERRORS + 1))
  fi
done

if [ "$ERRORS" -gt 0 ]; then
  echo ""
  echo "FAIL: $ERRORS version-sync error(s) found."
  exit 1
fi

echo ""
echo "OK: all plugin versions in sync with a matching CHANGELOG entry."
