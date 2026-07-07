#!/usr/bin/env bash
# Enforce the version invariant for every plugin in this marketplace:
#   plugin.json.version == marketplace.json plugin entry version
# and require a CHANGELOG.md entry for the current plugin version.
# Usage: ./scripts/check_version_sync.sh
# Exit 0 = all plugins in sync and changelogged. Exit 1 = any mismatch or missing entry.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MARKETPLACE="$REPO_ROOT/.claude-plugin/marketplace.json"
ERRORS=0

for plugin_json in "$REPO_ROOT"/plugins/*/.claude-plugin/plugin.json; do
  plugin_dir="$(dirname "$(dirname "$plugin_json")")"
  plugin_name="$(basename "$plugin_dir")"
  plugin_ver="$(python3 -c "import json; print(json.load(open('$plugin_json'))['version'])")"

  # Enforced invariant: plugin.json version must equal the marketplace entry version.
  market_ver="$(python3 -c "
import json
data = json.load(open('$MARKETPLACE'))
plugins = data.get('plugins', data) if isinstance(data, dict) else data
entry = next((p for p in plugins if p.get('name','').lower() == '$plugin_name' or p.get('id','').lower() == '$plugin_name'), None)
print(entry['version'] if entry else 'NOT_FOUND')
" 2>/dev/null || echo "NOT_FOUND")"

  if [ "$market_ver" = "NOT_FOUND" ]; then
    echo "MISSING  [$plugin_name] not found in marketplace.json"
    ERRORS=$((ERRORS + 1))
  elif [ "$market_ver" != "$plugin_ver" ]; then
    echo "MISMATCH [$plugin_name] plugin.json=$plugin_ver marketplace.json=$market_ver"
    ERRORS=$((ERRORS + 1))
  else
    echo "OK       [$plugin_name] v$plugin_ver"
  fi

  # CHANGELOG gate: require a heading for the current plugin version.
  # Guarded with `if` so a grep non-match does not trip `set -e` before ERRORS++.
  changelog="$plugin_dir/CHANGELOG.md"
  if [ ! -f "$changelog" ]; then
    echo "MISSING  [$plugin_name] CHANGELOG.md not found"
    ERRORS=$((ERRORS + 1))
  elif grep -Eq "^## \[$plugin_ver\]" "$changelog"; then
    echo "OK       [$plugin_name] CHANGELOG entry for v$plugin_ver"
  else
    echo "MISSING  [$plugin_name] CHANGELOG entry for v$plugin_ver"
    ERRORS=$((ERRORS + 1))
  fi
done

if [ "$ERRORS" -gt 0 ]; then
  echo ""
  echo "FAIL: $ERRORS error(s) found — version drift or missing CHANGELOG entry."
  exit 1
fi

echo ""
echo "OK: all plugin versions in sync with marketplace.json and changelogged."
