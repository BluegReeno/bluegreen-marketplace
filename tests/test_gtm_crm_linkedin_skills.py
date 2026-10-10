"""Invariants of `gtm:crm` and `gtm:linkedin` after the rewrite against the target contract
(hal audit q17, q25, q49): four crm gestes, a linkedin `draft` that reads `tone_of_voice` through
real tool calls, no duplicated command files, no tool that hal-mcp does not have.
"""
import re
import unittest

from skilltext import HAL_TOOLS, REPO, flat, frontmatter, hal_tools_allowed, hal_tools_mentioned, read

GTM = REPO / "plugins/gtm"
CRM = GTM / "skills/crm/SKILL.md"
LINKEDIN = GTM / "skills/linkedin/SKILL.md"


class TestPluginShape(unittest.TestCase):
    def test_gtm_has_exactly_three_skills(self):
        names = sorted(p.parent.name for p in (GTM / "skills").glob("*/SKILL.md"))
        self.assertEqual(names, ["call", "crm", "linkedin"])

    def test_duplicated_command_files_are_gone(self):
        # q17: « les commands/*.md dupliqués » disappear. `git rm -r plugins/gtm/commands`.
        left = sorted(p.name for p in (GTM / "commands").glob("*.md")) if (GTM / "commands").exists() else []
        self.assertEqual(left, [], "plugins/gtm/commands/ must be removed (q17)")

    def test_every_skill_name_matches_its_directory(self):
        for path in (GTM / "skills").glob("*/SKILL.md"):
            self.assertEqual(frontmatter(path)["name"], path.parent.name)

    def test_skills_are_short(self):
        # The rewrite exists to make them shorter: crm was 394 lines, linkedin 270.
        self.assertLess(len(read(CRM).splitlines()), 130)
        self.assertLess(len(read(LINKEDIN).splitlines()), 130)


class TestCrm(unittest.TestCase):
    def setUp(self):
        self.text = read(CRM)

    def test_four_gestes_and_only_four(self):
        gestes = re.findall(r"^## `(\w+)", self.text, re.M)
        self.assertEqual(gestes, ["new", "qualify", "stage", "review"])

    def test_retired_gestes_are_not_documented(self):
        for gone in ("/crm update", "/crm contact", "/crm doc", "/crm list", "/crm log"):
            self.assertNotIn(gone, self.text)

    def test_only_existing_tools(self):
        self.assertLessEqual(hal_tools_allowed(CRM), HAL_TOOLS)
        self.assertLessEqual(hal_tools_mentioned(CRM), HAL_TOOLS)

    def test_opportunities_use_the_target_kind_and_counterpart(self):
        self.assertIn('kind="opportunity"', self.text)
        self.assertIn("company_id", self.text)
        self.assertIn("primary_contact_id", self.text)
        self.assertNotIn('kind="project"', self.text)

    def test_stages_come_from_whoami_never_from_the_file(self):
        self.assertIn("kind_stages.opportunity", self.text)
        for stage in ("Prospect", "Qualification", "Devis envoyé", "Négociation", "Gagné", "Perdu"):
            self.assertNotIn(stage, self.text, f"stage name {stage!r} hard-coded")

    def test_a_win_creates_a_client_project_converted_from_the_opportunity(self):
        self.assertIn('kind="client"', self.text)
        self.assertIn("converted_from_id", self.text)

    def test_a_loss_needs_a_reason_before_the_stage_moves(self):
        text = flat(self.text)
        self.assertIn("une ligne de raison", text)
        self.assertIn("de fermer", text)
        self.assertIn("Pas de raison, pas de fermeture", text)

    def test_bant_merge_never_overwrites(self):
        self.assertIn("jamais écraser", self.text)

    def test_archived_workspace_is_checked(self):
        self.assertIn("archived", self.text)

    def test_no_legacy_table_names(self):
        self.assertNotIn("halcrm", self.text)


class TestLinkedin(unittest.TestCase):
    def setUp(self):
        self.text = read(LINKEDIN)

    def test_three_gestes_idea_draft_log(self):
        gestes = re.findall(r"^## `(\w+)", self.text, re.M)
        self.assertEqual(gestes, ["idea", "draft", "log"])

    def test_trend_and_backlog_are_gone(self):
        self.assertNotRegex(self.text, r"^## `(trend|backlog)", )
        self.assertNotIn("search_engine", self.text)
        self.assertNotIn("web_data_linkedin", self.text)

    def test_stats_is_not_claimed_as_implemented(self):
        self.assertNotRegex(self.text, r"^## `stats")
        self.assertNotIn("append_values", self.text)

    def test_draft_reads_tone_of_voice_through_real_tool_calls(self):
        tools = hal_tools_allowed(LINKEDIN)
        self.assertLessEqual({"list_documents", "get_document", "save_document"}, tools)
        self.assertIn('kind="tone_of_voice"', self.text)
        self.assertIn("introuvable → s'arrêter", flat(self.text))

    def test_draft_saves_with_the_arguments_save_document_has(self):
        call = re.search(r"`save_document\([^`]*\)`", " ".join(self.text.split()))
        self.assertIsNotNone(call)
        for arg in ("slug=", "domain=", "kind", "title=", "content_md="):
            self.assertIn(arg, call.group(0))
        self.assertNotIn("content=", call.group(0).replace("content_md=", ""))

    def test_posts_are_short_weekly_and_job_search_oriented(self):
        self.assertIn("un post par semaine", self.text)
        self.assertIn("800 caractères", self.text)
        self.assertIn("recherche d'emploi", self.text)

    def test_publication_is_logged_on_the_linkedin_channel(self):
        self.assertIn('channel="linkedin"', self.text)

    def test_only_existing_tools(self):
        self.assertLessEqual(hal_tools_allowed(LINKEDIN), HAL_TOOLS)
        self.assertLessEqual(hal_tools_mentioned(LINKEDIN), HAL_TOOLS)


if __name__ == "__main__":
    unittest.main()
