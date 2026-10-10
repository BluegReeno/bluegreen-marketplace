"""Invariants of the `knowledge` plugin (hal audit q29, q35, q39, q41): two skills, `ingest` and
`file`, written against the target contract — a file is referenced by `storage {provider, uri}`,
never uploaded; `ingest` refuses by name off the Mac; an archived workspace is never written.
"""
import json
import unittest

from skilltext import HAL_TOOLS, REPO, flat, frontmatter, hal_tools_allowed, hal_tools_mentioned, read

KNOWLEDGE = REPO / "plugins/knowledge"
INGEST = KNOWLEDGE / "skills/ingest/SKILL.md"
FILE = KNOWLEDGE / "skills/file/SKILL.md"


class TestPluginShape(unittest.TestCase):
    def test_three_mandatory_files_exist(self):
        self.assertTrue((KNOWLEDGE / ".claude-plugin/plugin.json").is_file())
        self.assertTrue((KNOWLEDGE / "CHANGELOG.md").is_file())
        market = json.loads(read(REPO / ".claude-plugin/marketplace.json"))
        self.assertIn("knowledge", [p["name"] for p in market["plugins"]])

    def test_exactly_ingest_and_file(self):
        names = sorted(p.parent.name for p in (KNOWLEDGE / "skills").glob("*/SKILL.md"))
        self.assertEqual(names, ["file", "ingest"])
        for path in (INGEST, FILE):
            self.assertEqual(frontmatter(path)["name"], path.parent.name)

    def test_the_plugin_carries_no_connector(self):
        # Only `hal` carries a .mcp.json: a second one would create a second tool prefix.
        self.assertFalse((KNOWLEDGE / ".mcp.json").exists())

    def test_only_existing_tools(self):
        for path in (INGEST, FILE):
            self.assertLessEqual(hal_tools_allowed(path), HAL_TOOLS, path)
            self.assertLessEqual(hal_tools_mentioned(path), HAL_TOOLS, path)


class TestIngest(unittest.TestCase):
    def setUp(self):
        self.text = read(INGEST)

    def test_runs_the_hal_checkout_script_and_dry_runs_first(self):
        self.assertIn("scripts/kb/ingest.py", self.text)
        self.assertIn("--pending", self.text)
        self.assertIn("--dry-run", self.text)

    def test_refuses_by_name_off_the_mac(self):
        self.assertIn("refuser en le nommant", self.text)
        self.assertIn("Jamais une source écrite sans passages", flat(self.text))

    def test_never_reads_the_env_file(self):
        self.assertIn("Ne jamais lire ni afficher `.env`", self.text)

    def test_date_is_required_for_course_and_video(self):
        self.assertIn("`--date`", self.text)
        self.assertIn("jamais l'inventer", self.text)

    def test_calls_stay_with_gtm_call(self):
        self.assertIn("gtm:call", self.text)

    def test_archived_and_non_knowledge_workspaces_are_refused(self):
        self.assertIn("knowledge_enabled", self.text)
        self.assertIn("archived", self.text)

    def test_no_direct_kb_index_call(self):
        self.assertNotIn("kb_index", hal_tools_allowed(INGEST))


class TestFile(unittest.TestCase):
    def setUp(self):
        self.text = read(FILE)

    def test_references_the_file_by_storage_never_uploads_it(self):
        self.assertIn("storage {provider, uri}", self.text)
        for legacy in ("filename", "mime_type", "gdrive_uri", "get_document_file", "bucket", "halcrm"):
            self.assertNotIn(legacy, self.text, legacy)

    def test_reads_folders_and_storage_from_whoami(self):
        self.assertIn("folders", self.text)
        self.assertIn("storage", self.text)

    def test_asks_the_one_knowledge_question(self):
        self.assertIn("voudrai-je un jour retrouver une phrase", self.text)

    def test_reuses_existing_kinds_before_coining_one(self):
        self.assertIn("by_kind", self.text)

    def test_archived_is_refused_and_no_location_is_invented(self):
        self.assertIn("archived", self.text)
        self.assertIn("ne pas inventer d'emplacement", flat(self.text))

    def test_facts_are_shown_before_anything_is_written(self):
        self.assertIn("Les montrer avant d'écrire", self.text)


if __name__ == "__main__":
    unittest.main()
