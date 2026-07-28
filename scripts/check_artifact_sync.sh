#!/usr/bin/env bash
# Rebuild every ui/<name>/ workspace member and fail if the committed
# plugins/hal/artifacts/<name>.html differs from a fresh rebuild (ignoring the
# non-reproducible build-stamp comment line, which legitimately changes every
# run — see ui/scripts/build-artifact.mjs).
# Usage: ./scripts/check_artifact_sync.sh
# Exit 0 = every artifact matches its committed output. Exit 1 = any drift.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACTS_DIR="$REPO_ROOT/plugins/hal/artifacts"
ERRORS=0

if [ ! -d "$REPO_ROOT/ui" ]; then
  echo "OK: no ui/ workspace present, nothing to check."
  exit 0
fi

( cd "$REPO_ROOT/ui" && pnpm install --frozen-lockfile )

for app_dir in "$REPO_ROOT"/ui/*/; do
  name="$(basename "$app_dir")"
  [ "$name" = "scripts" ] && continue
  [ -f "$app_dir/package.json" ] || continue

  committed="$ARTIFACTS_DIR/$name.html"
  if [ ! -f "$committed" ]; then
    echo "ERROR    [$name] no committed artifact at plugins/hal/artifacts/$name.html"
    ERRORS=$((ERRORS + 1))
    continue
  fi

  # Snapshot the currently-committed file (build-stamp line stripped) BEFORE the
  # rebuild overwrites it in place. This is the single most important design
  # point: build-artifact.mjs writes straight into $committed, so we must
  # capture the pre-rebuild content to diff against the fresh output. Stripping
  # the stamp on both sides is what makes the check meaningful despite the
  # stamp's date/commit fields changing on every run. Comparing against this
  # snapshot (rather than `git show HEAD`) also catches an uncommitted hand-edit
  # of the committed HTML, which the acceptance criteria require.
  before_file="$(mktemp)"
  trap 'rm -f "$before_file"' EXIT

  grep -v '^<!-- build:' "$committed" > "$before_file" && grep_status=0 || grep_status=$?
  if [ "$grep_status" -gt 1 ]; then
    echo "ERROR    [$name] failed to read committed artifact $committed (grep exit $grep_status)"
    ERRORS=$((ERRORS + 1))
    rm -f "$before_file"
    continue
  fi

  ( cd "$REPO_ROOT/ui" && pnpm --filter "$name" build ) >/dev/null

  if ! diff "$before_file" <(grep -v '^<!-- build:' "$committed") >/dev/null 2>&1; then
    echo "MISMATCH [$name] committed plugins/hal/artifacts/$name.html differs from a fresh rebuild (excluding build-stamp line)"
    ERRORS=$((ERRORS + 1))
  else
    echo "OK       [$name] committed artifact matches a fresh rebuild"
  fi
  rm -f "$before_file"
done

if [ "$ERRORS" -gt 0 ]; then
  echo ""
  echo "FAIL: $ERRORS artifact-sync error(s) found."
  exit 1
fi

echo ""
echo "OK: all artifacts in sync with their committed output."
