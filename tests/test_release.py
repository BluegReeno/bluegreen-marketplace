"""
Tests for scripts/release.sh — the one-command version-bump release tool.
Drives the real script via subprocess against a throwaway git-repo fixture so
the actual repo is never mutated. Covers: arg validation, the strictly-greater
guard, dirty-tree refusal, the happy-path multi-file bump + commit, duplicate
rejection, --mcp-version, and marketplace.json key-ordering regressions.
"""
import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"


def _git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args],
                          capture_output=True, text=True, check=True)


class ReleaseFixture:
    """A minimal committed git repo with the release + sync scripts and a hal plugin."""
    def __init__(self, tmp: pathlib.Path, plugin_ver="0.10.1", top_ver="0.10.1",
                 marketplace_json_text=None):
        self.root = tmp
        (tmp / "scripts").mkdir()
        (tmp / "plugins/hal/.claude-plugin").mkdir(parents=True)
        (tmp / ".claude-plugin").mkdir()
        # Copy the scripts under test verbatim (REPO_ROOT resolves from their location).
        for s in ("release.sh", "check_version_sync.sh"):
            shutil.copy(SCRIPTS / s, tmp / "scripts" / s)
            (tmp / "scripts" / s).chmod(0o755)
        (tmp / "plugins/hal/.claude-plugin/plugin.json").write_text(
            json.dumps({"name": "hal", "version": plugin_ver,
                        "author": {"name": "BG"}}, indent=2) + "\n")
        if marketplace_json_text is None:
            marketplace_json_text = json.dumps(
                {"version": top_ver,
                 "plugins": [{"name": "hal", "version": plugin_ver}]}, indent=2) + "\n"
        (tmp / ".claude-plugin/marketplace.json").write_text(marketplace_json_text)
        (tmp / "plugins/hal/CHANGELOG.md").write_text(
            "# Changelog\n\n---\n\n## [0.10.1] — 2026-06-01 — baseline\n")
        (tmp / "plugins/hal/.mcp.json").write_text(
            json.dumps({"version": "0.2.1"}, indent=2) + "\n")
        _git(tmp, "init", "-q")
        _git(tmp, "config", "user.email", "t@t.io")
        _git(tmp, "config", "user.name", "t")
        _git(tmp, "add", "-A")
        _git(tmp, "commit", "-q", "-m", "fixture")

    def run(self, *args):
        return subprocess.run(["bash", str(self.root / "scripts/release.sh"), *args],
                              cwd=self.root, capture_output=True, text=True)

    def read_json(self, rel):
        return json.loads((self.root / rel).read_text())

    def dirty(self):
        return bool(_git(self.root, "status", "--porcelain").stdout.strip())


class TestReleaseValidation(unittest.TestCase):
    def _fx(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        return ReleaseFixture(pathlib.Path(self.tmp.name))

    def test_no_args_exits_1_and_prints_usage(self):
        r = self._fx().run()
        self.assertEqual(r.returncode, 1)
        self.assertIn("Usage:", r.stderr)

    def test_empty_changelog_line_refused(self):
        r = self._fx().run("hal", "0.10.2", "")
        self.assertEqual(r.returncode, 1)

    def test_version_not_strictly_greater_refused(self):
        fx = self._fx()
        r = fx.run("hal", "0.10.1", "same version")
        self.assertEqual(r.returncode, 1)
        self.assertFalse(fx.dirty(), "a refused release must write nothing")

    def test_unknown_plugin_refused(self):
        r = self._fx().run("nope", "9.9.9", "x")
        self.assertEqual(r.returncode, 1)

    def test_dirty_tree_refused(self):
        fx = self._fx()
        (fx.root / "plugins/hal/CHANGELOG.md").write_text("dirty\n")
        r = fx.run("hal", "0.10.2", "x")
        self.assertEqual(r.returncode, 1)
        self.assertIn("dirty", r.stderr.lower())

    def test_invalid_semver_refused(self):
        # e.g. "0.10" — guards the SemVer parser, not just the ordering.
        r = self._fx().run("hal", "0.10", "not semver")
        self.assertEqual(r.returncode, 1)

    def test_malformed_and_not_greater_give_distinct_messages(self):
        # A malformed version must not be misreported as "not greater" (M2).
        malformed = self._fx().run("hal", "0.10", "typo")
        self.assertIn("X.Y.Z", malformed.stderr)
        self.assertNotIn("greater", malformed.stderr.lower())
        not_greater = self._fx().run("hal", "0.10.1", "same")
        self.assertIn("greater", not_greater.stderr.lower())


class TestReleaseHappyPath(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.fx = ReleaseFixture(pathlib.Path(self.tmp.name))
        self.r = self.fx.run("hal", "0.10.2", "test release")

    def test_exits_0(self):
        self.assertEqual(self.r.returncode, 0, self.r.stderr)

    def test_plugin_and_marketplace_entry_bumped_identically(self):
        self.assertEqual(self.fx.read_json("plugins/hal/.claude-plugin/plugin.json")["version"],
                         "0.10.2")
        mkt = self.fx.read_json(".claude-plugin/marketplace.json")
        self.assertEqual(mkt["plugins"][0]["version"], "0.10.2")

    def test_top_level_counter_bumped_independently(self):
        # Monotonic PATCH +1 from the fixture's 0.10.1 top-level.
        self.assertEqual(self.fx.read_json(".claude-plugin/marketplace.json")["version"],
                         "0.10.2")

    def test_changelog_entry_prepended_as_topmost(self):
        text = (self.fx.root / "plugins/hal/CHANGELOG.md").read_text()
        first = text.index("## [")
        self.assertTrue(text[first:].startswith("## [0.10.2] — "), text[first:first+40])
        self.assertIn("test release", text[first:first+80])

    def test_commit_made_with_exact_subject_and_tree_clean(self):
        subj = _git(self.fx.root, "log", "-1", "--pretty=%s").stdout.strip()
        self.assertEqual(subj, "chore(hal): release v0.10.2")
        self.assertFalse(self.fx.dirty())

    def test_mcp_untouched_without_flag(self):
        self.assertEqual(self.fx.read_json("plugins/hal/.mcp.json")["version"], "0.2.1")

    def test_no_tag_created(self):
        self.assertEqual(_git(self.fx.root, "tag").stdout.strip(), "")


class TestReleaseDuplicateAndMcp(unittest.TestCase):
    def _fx(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        return ReleaseFixture(pathlib.Path(self.tmp.name))

    def test_second_release_same_version_refused(self):
        fx = self._fx()
        self.assertEqual(fx.run("hal", "0.10.2", "first").returncode, 0)
        self.assertEqual(fx.run("hal", "0.10.2", "again").returncode, 1)

    def test_mcp_version_flag_bumps_mcp_json(self):
        fx = self._fx()
        r = fx.run("hal", "0.10.2", "with mcp", "--mcp-version", "9.9.9")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(fx.read_json("plugins/hal/.mcp.json")["version"], "9.9.9")


class TestReleaseKeyOrdering(unittest.TestCase):
    """Regression coverage for #36 — marketplace.json key order must not corrupt the bump.

    release.sh locates the top-level and plugin-entry "version" keys with a
    position-based regex search (to keep formatting byte-identical). Before this
    fix that search assumed "plugins" always comes after the top-level "version"
    key and that "name" always precedes "version" inside an entry. Reordering
    either one made the top-level counter search land on the entry's version
    instead — a swap that was NOT caught by the None guards from the M3 quick-win
    (both regexes still matched *something*, just the wrong key) and produced a
    silently wrong marketplace.json on a successful (exit 0) run.
    """

    def _fx(self, marketplace_json_text, plugin_ver="0.10.1"):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        return ReleaseFixture(pathlib.Path(self.tmp.name), plugin_ver=plugin_ver,
                               marketplace_json_text=marketplace_json_text)

    def test_plugins_array_before_top_level_version_bumps_correct_fields(self):
        # "plugins" written before the top-level "version" key.
        fx = self._fx(json.dumps({
            "plugins": [{"name": "hal", "version": "0.10.1"}],
            "version": "0.10.5",
        }, indent=2) + "\n")
        r = fx.run("hal", "0.10.2", "reordered top-level key")
        self.assertEqual(r.returncode, 0, r.stderr)
        mkt = fx.read_json(".claude-plugin/marketplace.json")
        self.assertEqual(mkt["plugins"][0]["version"], "0.10.2",
                          "plugin entry must get the new plugin version, not the top-level bump")
        self.assertEqual(mkt["version"], "0.10.6",
                          "top-level counter must still get its independent +1 patch bump")

    def test_entry_version_before_name_fails_cleanly_not_traceback(self):
        # Inside the plugin entry, "version" written before "name"/"id".
        fx = self._fx(json.dumps({
            "plugins": [{"version": "0.10.1", "name": "hal"}],
            "version": "0.10.5",
        }, indent=2) + "\n")
        r = fx.run("hal", "0.10.2", "reordered entry keys")
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("version", r.stderr.lower())
        # A clean failure must not silently rewrite marketplace.json.
        mkt = fx.read_json(".claude-plugin/marketplace.json")
        self.assertEqual(mkt["version"], "0.10.5")
        self.assertEqual(mkt["plugins"][0]["version"], "0.10.1")

    def test_both_reorderings_together_still_bump_correct_fields(self):
        # "plugins" before top-level "version", AND "id" before "version" inside
        # the entry (id used instead of name) — the two guards compose.
        fx = self._fx(json.dumps({
            "plugins": [{"id": "hal", "name": "hal", "version": "0.10.1"}],
            "version": "0.10.5",
        }, indent=2) + "\n")
        r = fx.run("hal", "0.10.2", "reordered + id-based lookup")
        self.assertEqual(r.returncode, 0, r.stderr)
        mkt = fx.read_json(".claude-plugin/marketplace.json")
        self.assertEqual(mkt["plugins"][0]["version"], "0.10.2")
        self.assertEqual(mkt["version"], "0.10.6")


if __name__ == "__main__":
    unittest.main()
