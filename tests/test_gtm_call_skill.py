"""Invariants of the `gtm:call` skill — the contract that `jobsearch:log-cr` (renaud-marketplace)
relies on, and the hygiene a public repo needs.

Prose skills have no unit test; these guards catch the drifts that would break a caller silently:
a renamed skill, a `disable-model-invocation` that would refuse the cross-plugin
`Skill("gtm:call")`, a hal tool dropped from `allowed-tools`, `knowledge=true` lost from the
analysis write (hal#235), an email literal, or a retired `/crm log` resurrected.
"""
import pathlib
import re
import unittest

from skilltext import HAL_TOOLS, REPO, allowed_tools, frontmatter, hal_tools_allowed, hal_tools_mentioned, read

GTM = REPO / "plugins/gtm"
SKILL = GTM / "skills/call/SKILL.md"
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


class TestCallSkillFrontmatter(unittest.TestCase):
    def setUp(self):
        self.fm = frontmatter(SKILL)

    def test_name_is_call(self):
        # `Skill("gtm:call")` resolves on plugin name + this field; a rename breaks log-cr.
        self.assertEqual(self.fm["name"], "call")

    def test_no_disable_model_invocation(self):
        self.assertNotIn("disable-model-invocation", self.fm)

    def test_allowed_tools_cover_the_hal_writes(self):
        tools = hal_tools_allowed(SKILL)
        for name in ("save_document", "log_interaction", "list_interactions",
                     "update_interaction", "whoami", "list_projects", "update_project"):
            self.assertIn(name, tools, name)
        self.assertIn("Bash(uv *)", allowed_tools(SKILL))   # render + ingest
        self.assertIn("Bash(test *)", allowed_tools(SKILL))  # the pre-flight

    def test_allowed_tools_call_no_other_skill(self):
        # gtm:call is the leaf of the chain: log-cr calls it, it calls nobody.
        self.assertNotIn("Skill(", self.fm["allowed-tools"])

    def test_description_names_the_caller(self):
        self.assertIn("log-cr", self.fm["description"])


class TestCallSkillAgainstTheTargetContract(unittest.TestCase):
    def setUp(self):
        self.text = read(SKILL)

    def test_every_tool_named_exists_in_hal_mcp(self):
        self.assertLessEqual(hal_tools_allowed(SKILL), HAL_TOOLS)
        self.assertLessEqual(hal_tools_mentioned(SKILL), HAL_TOOLS)

    def test_the_analysis_is_saved_as_knowledge(self):
        # hal#235: `ingest.py --pending` indexes a document only when its fiche carries
        # `knowledge`. Without the flag the analysis is counted as skipped and the run succeeds.
        body = " ".join(self.text.split())
        call = re.search(r'`save_document\(workspace_slug=WS[^`]*kind="call_analysis"[^`]*\)`', body)
        self.assertIsNotNone(call)
        self.assertIn("knowledge=true", call.group(0))

    def test_projects_are_read_by_the_four_kinds_not_the_old_project_kind(self):
        self.assertIn('kind="opportunity"', self.text)
        self.assertIn('kind="client"', self.text)
        self.assertNotIn('kind="project"', self.text)

    def test_archived_workspaces_are_refused_by_name(self):
        self.assertIn("archived", self.text)

    def test_the_analysis_carries_no_file(self):
        # `save_document` takes `storage {provider, uri}` now; an analysis is text, not a file.
        self.assertNotIn("filename", self.text)
        self.assertIn("Aucun `storage`", self.text)

    def test_the_interview_workspace_comes_from_its_type_not_a_tag_or_a_slug(self):
        self.assertIn('type == "jobsearch"', self.text)

    def test_no_legacy_table_names(self):
        self.assertNotIn("halcrm", self.text)


class TestCallSkillHygiene(unittest.TestCase):
    def setUp(self):
        self.text = read(SKILL)

    def test_no_email_literal(self):
        # Public repo: owner addresses come from whoami / Granola, never from this file.
        found = [e for e in EMAIL.findall(self.text) if not e.endswith("example.com")]
        self.assertEqual(found, [])

    def test_renderer_is_the_hal_cli(self):
        for needle in ("call_analysis.py", "render", "prompts", "ingest.py"):
            self.assertIn(needle, self.text)

    def test_source_keys_match_call_analysis_render(self):
        # `render` refuses a `source` missing any of these (hal call_analysis.CALL_SOURCE_KEYS).
        for key in ("granola_id", "opportunite", "outcome", "type_entretien", "feeling",
                    "format", "heure", "interlocuteurs"):
            self.assertIn(key, self.text, key)

    def test_reflection_is_a_string_under_reflexion(self):
        self.assertIn("## Réflexion", self.text)
        self.assertNotIn("reflection.fit", self.text)


class TestCrmLogRetired(unittest.TestCase):
    """`/crm log` and `/crm log update` are gone from the gtm plugin: `gtm:call` replaced the first,
    `update_interaction` named in the sentence replaces the second."""

    def test_no_crm_log_left_in_the_plugin(self):
        for path in GTM.rglob("*.md"):
            if path.name == "CHANGELOG.md":
                continue
            for n, line in enumerate(read(path).splitlines(), 1):
                self.assertNotRegex(line, r"/crm log", f"{path}:{n}")

    def test_crm_no_longer_logs_interactions(self):
        tools = hal_tools_allowed(GTM / "skills/crm/SKILL.md")
        self.assertNotIn("log_interaction", tools)
        self.assertNotIn("update_interaction", tools)


if __name__ == "__main__":
    unittest.main()
