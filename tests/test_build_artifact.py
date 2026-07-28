"""
Tests for ui/scripts/build-artifact.mjs — the shared post-build step for
artifact front-ends. Drives the real script via subprocess (node), matching
test_release.py's fixture-driven pattern.

Unlike test_release.py, fixtures live inside the real ui/ workspace rather
than a fully isolated tmp copy: the script imports cheerio via ESM, which
only resolves through ui/node_modules, and resolves its repo root via
`git rev-parse` against its own real location — both require staying rooted
in the actual repo. Each fixture app and its written artifact are removed in
tearDown so nothing lingers for check_artifact_sync.sh or git to see.
"""
import json
import os
import pathlib
import shutil
import subprocess
import time
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
UI_DIR = REPO / "ui"
ARTIFACTS_DIR = REPO / "plugins/hal/artifacts"
BUILD_SCRIPT = UI_DIR / "scripts/build-artifact.mjs"

DEFAULT_DIST_HTML = (
    "<!doctype html><html><head><style>.a{color:red}</style></head>"
    "<body><p>hello</p></body></html>"
)

META_BLOCK = (
    '<script type="application/json" id="cowork-artifact-meta">\n'
    '{"name":"fx","mcpTools":["mcp__UUID__list_edifice_missions"]}\n'
    "</script>"
)

DIST_HTML_WITH_META = (
    f"<!doctype html>\n<html><head>{META_BLOCK}"
    "<style>.a{color:red}</style></head>"
    "<body><p>hello</p></body></html>"
)


def _node_toolchain_ready():
    return shutil.which("node") is not None and (UI_DIR / "node_modules" / "cheerio").exists()


class BuildArtifactFixture:
    def __init__(self, dist_html=DEFAULT_DIST_HTML):
        self.name = f"_test_fixture_{int(time.time() * 1000)}"
        self.app_dir = UI_DIR / self.name
        (self.app_dir / "dist").mkdir(parents=True)
        (self.app_dir / "dist" / "index.html").write_text(dist_html)
        (self.app_dir / "package.json").write_text(json.dumps({"name": self.name}))
        self.artifact_file = ARTIFACTS_DIR / f"{self.name}.html"

    def build(self, target=None):
        env = {**os.environ, "ARTIFACT_TARGET": target} if target else None
        return subprocess.run(
            ["node", str(BUILD_SCRIPT), self.name],
            cwd=self.app_dir, capture_output=True, text=True, env=env,
        )

    def cleanup(self):
        shutil.rmtree(self.app_dir, ignore_errors=True)
        self.artifact_file.unlink(missing_ok=True)


@unittest.skipUnless(
    _node_toolchain_ready(),
    "ui/ Node toolchain not installed (run `pnpm install` in ui/ first) — "
    "CI only installs it for ui/**-touching PRs",
)
class TestBuildArtifact(unittest.TestCase):
    def _fx(self, dist_html=DEFAULT_DIST_HTML):
        fx = BuildArtifactFixture(dist_html)
        self.addCleanup(fx.cleanup)
        return fx

    def test_cowork_target_keeps_full_document_and_stamp(self):
        fx = self._fx()
        result = fx.build()
        self.assertEqual(result.returncode, 0, result.stderr)
        out = fx.artifact_file.read_text()
        self.assertIn("<html>", out)
        self.assertIn("<!-- build:", out)

    def test_cowork_target_hoists_meta_block_into_the_preamble(self):
        # Cowork reads this block at publish time to build the artifact's
        # mcp_tools allowlist, and only reads it from the preamble. Left in
        # <head> it is ignored: the artifact is published with an empty
        # allowlist and every tool call is rejected (observed 2026-07-28).
        fx = self._fx(DIST_HTML_WITH_META)
        result = fx.build()
        self.assertEqual(result.returncode, 0, result.stderr)
        out = fx.artifact_file.read_text()
        self.assertEqual(out.count('id="cowork-artifact-meta"'), 1, "block duplicated")
        self.assertLess(
            out.index("cowork-artifact-meta"),
            out.index("<html>"),
            "meta block must sit between <!doctype html> and <html>",
        )
        self.assertIn("mcp__UUID__list_edifice_missions", out)
        self.assertIn("<!-- build:", out)

    def test_cowork_target_without_meta_block_is_untouched(self):
        fx = self._fx()
        result = fx.build()
        self.assertEqual(result.returncode, 0, result.stderr)
        out = fx.artifact_file.read_text()
        self.assertNotIn("cowork-artifact-meta", out)
        self.assertIn("<p>hello</p>", out)

    def test_fragment_target_keeps_meta_block_in_place(self):
        # A fragment has no doctype to anchor a preamble; hoisting there would
        # drop the block outside the returned markup.
        fx = self._fx(DIST_HTML_WITH_META)
        result = fx.build(target="fragment")
        self.assertEqual(result.returncode, 0, result.stderr)
        out = fx.artifact_file.read_text()
        self.assertIn('id="cowork-artifact-meta"', out)
        self.assertNotIn("<!doctype", out.lower())

    def test_fragment_target_strips_wrapper_but_keeps_stamp_and_content(self):
        fx = self._fx()
        result = fx.build(target="fragment")
        self.assertEqual(result.returncode, 0, result.stderr)
        out = fx.artifact_file.read_text()
        self.assertNotIn("<html>", out)
        self.assertIn(".a{color:red}", out)
        self.assertIn("<p>hello</p>", out)
        # Regression check: the stamp used to be inserted before <html>, so it
        # silently vanished from fragment output (see PR #52 review Finding 3/4).
        self.assertIn("<!-- build:", out)

    def test_unknown_target_fails_loud_and_writes_nothing(self):
        fx = self._fx()
        result = fx.build(target="bogus")
        self.assertEqual(result.returncode, 1)
        self.assertIn("unknown ARTIFACT_TARGET", result.stderr)
        self.assertFalse(fx.artifact_file.exists())

    def test_missing_dist_file_fails_loud(self):
        fx = self._fx()
        (fx.app_dir / "dist" / "index.html").unlink()
        result = fx.build()
        self.assertEqual(result.returncode, 1)
        self.assertIn("no build output at", result.stderr)

    def test_size_ceiling_fails_closed(self):
        big_html = ("<!doctype html><html><head></head><body>"
                    + ("x" * (17 * 1024 * 1024)) + "</body></html>")
        fx = self._fx(dist_html=big_html)
        result = fx.build()
        self.assertEqual(result.returncode, 1)
        self.assertIn("exceeds the 16 MiB artifact ceiling", result.stderr)
        self.assertFalse(fx.artifact_file.exists())

    def test_warn_threshold_warns_but_still_succeeds(self):
        warn_html = ("<!doctype html><html><head></head><body>"
                     + ("x" * (3 * 1024 * 1024)) + "</body></html>")
        fx = self._fx(dist_html=warn_html)
        result = fx.build()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("exceeds the 2 MiB warn threshold", result.stderr)


if __name__ == "__main__":
    unittest.main()
