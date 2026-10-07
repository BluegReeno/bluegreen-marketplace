"""
Invariants of the `gtm:call` skill (hal#192) — the contract that `jobsearch:log-cr`
(renaud-marketplace) and `plugins/gtm/commands/call.md` rely on, and the hygiene a public repo
needs. Prose skills have no unit test; these guards catch the drifts that would break a caller
silently: a renamed skill, a `disable-model-invocation` that would refuse the cross-plugin
`Skill("gtm:call")`, a hal tool dropped from `allowed-tools`, an email literal, or `/crm log`
resurrected next to its replacement.

The skill is written against hal's target tool contract (hal q49, migration-roadmap.md § 6):
`TARGET_PARAMS` mirrors the zod input schemas of `supabase/functions/hal-mcp/index.ts` in the hal
repo for every tool this skill calls, so a parameter the server does not declare cannot be written
into the skill. Update it with index.ts, never ahead of it.

Frontmatter is parsed by hand (no PyYAML at CI time), like the other tests in this directory.
"""
import pathlib
import re
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
GTM = REPO / "plugins/gtm"
SKILL = GTM / "skills/call/SKILL.md"
COMMAND = GTM / "commands/call.md"
CRM_SKILL = GTM / "skills/crm/SKILL.md"
CRM_COMMAND = GTM / "commands/crm.md"

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
HAL_PREFIX = "mcp__plugin_hal_hal-mcp__"

# The input parameters hal-mcp declares on the target, per tool (index.ts zod schemas).
TARGET_PARAMS = {
    "whoami": set(),
    "list_projects": {"workspace_slug", "kind", "stage", "tags", "limit", "parent_project_id",
                      "converted_from_id"},
    "update_project": {"workspace_slug", "project_id", "name", "kind", "amount_ht", "currency",
                       "project_ref", "location", "description", "due_date", "company_id",
                       "primary_contact_id", "tags", "converted_from_id", "parent_project_id"},
    "update_project_stage": {"workspace_slug", "project_id", "stage"},
    "list_companies": {"workspace_slug", "search", "limit", "offset"},
    "list_contacts": {"workspace_slug", "company_id", "search", "limit", "offset"},
    "create_contact": {"workspace_slug", "name", "company_id", "role", "email", "phone",
                       "linkedin", "tone", "tags", "notes"},
    "list_interactions": {"workspace_slug", "contact_id", "project_id", "channel", "since",
                          "until", "search", "limit", "offset"},
    "log_interaction": {"workspace_slug", "channel", "summary", "project_id", "contact_id",
                        "occurred_at", "created_by", "transcript", "sensitive", "tags"},
    "update_interaction": {"workspace_slug", "interaction_id", "summary", "transcript", "channel",
                           "occurred_at", "contact_id", "project_id", "sensitive", "tags"},
    "list_tasks": {"workspace_slug", "project_id", "assignee_email", "status", "sprint_id", "tags",
                   "limit"},
    "create_task": {"workspace_slug", "title", "project_id", "assignee_email", "due_date",
                    "sprint_id", "description", "priority", "external_ref", "tags"},
    "list_sprints": {"workspace_slug", "status"},
    "list_documents": {"workspace_slug", "search", "domain", "kind", "person_name",
                       "expiring_before", "project_id", "knowledge", "summary_only", "limit",
                       "offset"},
    "save_document": {"workspace_slug", "slug", "domain", "kind", "title", "person_name",
                      "content_md", "facts", "storage", "issued_date", "valid_until", "sensitive",
                      "knowledge", "project_id"},
    "get_document_link": {"workspace_slug", "slug"},
    "kb_search": {"workspace_slug", "query", "limit", "kind", "since", "until"},
}


def _allowed_tools(path: pathlib.Path) -> list:
    # `Bash(uv *)` holds a space: tokens are either `Name(...)` or a bare name.
    return re.findall(r"\S+\([^)]*\)|\S+", _frontmatter(path)["allowed-tools"].strip('"'))


def _body(path: pathlib.Path) -> str:
    return re.sub(r"^---\n.*?\n---\n", "", path.read_text(encoding="utf-8"), count=1, flags=re.S)


def _split_args(args: str) -> list:
    """Top-level comma split: commas inside <…>, (…), […], "…" or « … » are part of a value."""
    parts, depth, cur, quote = [], 0, "", None
    for ch in args:
        if quote:
            cur += ch
            if ch == quote:
                quote = None
            continue
        if ch in '"«':
            quote = '"' if ch == '"' else "»"
        elif ch in "([<{":
            depth += 1
        elif ch in ")]>}":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
            continue
        cur += ch
    parts.append(cur)
    return parts


def _hal_calls(text: str) -> list:
    """Every `tool(args)` written in the skill body for a hal tool, as (tool, [param names])."""
    calls = []
    for m in re.finditer(r"\b(" + "|".join(TARGET_PARAMS) + r")\(", text):
        depth, j = 1, m.end()
        while depth and j < len(text):
            depth += {"(": 1, ")": -1}.get(text[j], 0)
            j += 1
        names = []
        for part in _split_args(" ".join(text[m.end():j - 1].split())):
            part = part.strip()
            if not part or part.startswith("…"):
                continue
            named = re.match(r"^(\w+)\??\s*=", part) or re.match(r"^(\w+)\??$", part)
            names.append(named.group(1) if named else part)
        calls.append((m.group(1), names))
    return calls


def _frontmatter(path: pathlib.Path) -> dict:
    """The `key: value` pairs of the YAML block — folded `>` scalars joined on one line."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, f"{path} has no frontmatter"
    fields, key = {}, None
    for line in m.group(1).splitlines():
        if line.startswith(" ") and key:
            fields[key] = (fields[key] + " " + line.strip()).strip()
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        fields[key] = value.strip().lstrip(">").strip()
    return fields


class TestCallSkillFrontmatter(unittest.TestCase):
    def setUp(self):
        self.fm = _frontmatter(SKILL)

    def test_name_is_call(self):
        # `Skill("gtm:call")` resolves on plugin name + this field; a rename breaks log-cr.
        self.assertEqual(self.fm["name"], "call")

    def test_no_disable_model_invocation(self):
        # Rule 2 of the cross-plugin test (hal#192 comment 2): the target never sets it.
        self.assertNotIn("disable-model-invocation", self.fm)

    def test_allowed_tools_cover_the_hal_writes(self):
        tools = _allowed_tools(SKILL)
        for name in ("save_document", "log_interaction", "list_interactions",
                     "update_interaction", "whoami", "list_projects", "list_documents",
                     "kb_search"):
            self.assertIn(f"{HAL_PREFIX}{name}", tools, name)
        self.assertIn("Bash(uv *)", tools)   # `uv run --project "$HAL" …` for render + ingest
        self.assertIn("Bash(test *)", tools)  # the pre-flight

    def test_allowed_tools_call_no_other_skill(self):
        # gtm:call is the leaf of the chain: log-cr calls it, it calls nobody.
        self.assertNotIn("Skill(", self.fm["allowed-tools"])

    def test_description_names_the_caller(self):
        self.assertIn("log-cr", self.fm["description"])


class TestCallSkillTargetContract(unittest.TestCase):
    """hal q49 / migration-roadmap.md § 6: the contract the skill is rewritten against."""

    def setUp(self):
        self.text = SKILL.read_text(encoding="utf-8")
        self.body = _body(SKILL)

    def test_document_link_replaces_document_file(self):
        tools = _allowed_tools(SKILL)
        self.assertIn(f"{HAL_PREFIX}get_document_link", tools)
        self.assertNotIn(f"{HAL_PREFIX}get_document_file", tools)
        self.assertNotIn("get_document_file", self.text)

    def test_every_hal_tool_exists_on_the_target(self):
        for tool in _allowed_tools(SKILL):
            if tool.startswith(HAL_PREFIX):
                self.assertIn(tool[len(HAL_PREFIX):], TARGET_PARAMS, tool)

    def test_every_hal_call_is_allowed(self):
        tools = set(_allowed_tools(SKILL))
        for name, _ in _hal_calls(self.body):
            self.assertIn(f"{HAL_PREFIX}{name}", tools, name)

    def test_no_parameter_the_target_does_not_declare(self):
        calls = _hal_calls(self.body)
        self.assertGreater(len(calls), 20)
        for name, params in calls:
            for param in params:
                self.assertIn(param, TARGET_PARAMS[name], f"{name}({param})")

    def test_no_upload_path(self):
        # save_document references a file through `storage`; there is no upload parameter.
        self.assertNotIn("filename", self.text)
        self.assertNotIn("upload_url", self.text)

    def test_workspace_resolved_by_type_not_by_tag(self):
        self.assertIn('`type == "jobsearch"`', self.body)
        self.assertIn('`type == "company"`', self.body)
        self.assertIsNone(re.search(r"allowed_tags`?[^.\n]*contient[^.\n]*jobsearch", self.body))
        self.assertIsNone(re.search(r"tagu[ée]e?\s+`?jobsearch", self.body))

    def test_archived_workspace_is_never_written(self):
        self.assertIn("`archived`", self.body)
        self.assertIn("est archivé : hal n'y accepte aucune écriture", self.body)

    def test_project_kinds_are_the_target_four(self):
        self.assertNotIn('kind="project"', self.body)
        self.assertNotIn('kind == "project"', self.body)
        self.assertIn("kind_stages[<kind>]", self.body)
        self.assertIn('kind == "client"', self.body)

    def test_interaction_is_a_call(self):
        self.assertIn('log_interaction(workspace_slug=WS, channel="call"', " ".join(self.body.split()))
        self.assertIn('"channel": "call"', self.body)
        self.assertNotIn('channel="meeting"', self.body)

    def test_no_silent_workaround(self):
        lowered = self.text.lower()
        for word in ("skip silently", "fallback", "best-effort", "best effort", "gracefully"):
            self.assertNotIn(word, lowered, word)

    def test_acceptance_s01_lists_the_nine_steps(self):
        section = self.body.split("## Acceptance — S01", 1)
        self.assertEqual(len(section), 2)
        steps = re.findall(r"^\| (\d+) \|", section[1], re.M)
        self.assertEqual(steps, [str(n) for n in range(1, 10)])


class TestCallSkillKnowledgeFlag(unittest.TestCase):
    def test_the_analysis_is_saved_as_knowledge(self):
        # hal#235: `ingest.py --pending` indexes a document only when its fiche carries
        # `knowledge`. Without the flag the analysis is counted as skipped and the run succeeds.
        body = " ".join(SKILL.read_text(encoding="utf-8").split())
        call = re.search(r'`save_document\(workspace_slug=WS[^`]*kind="call_analysis"[^`]*\)`', body)
        self.assertIsNotNone(call)
        self.assertIn("knowledge=true", call.group(0))
        self.assertIn("project_id=P", call.group(0))
        self.assertIn("content_md", call.group(0))
        # knowledge and sensitive cannot both hold on a document; the analysis is never sensitive.
        self.assertNotIn("sensitive", call.group(0))
        self.assertNotIn("storage", call.group(0))


class TestCallSkillHygiene(unittest.TestCase):
    def test_no_email_literal(self):
        # Public repo: owner addresses come from whoami / Granola, never from this file.
        found = [e for e in EMAIL.findall(SKILL.read_text(encoding="utf-8"))
                 if not e.endswith("example.com")]
        self.assertEqual(found, [])

    def test_renderer_is_the_hal_cli(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("call_analysis.py", text)
        self.assertIn("render", text)
        self.assertIn("prompts", text)
        self.assertIn("ingest.py", text)

    def test_source_keys_match_call_analysis_render(self):
        # `render` refuses a `source` missing any of these (hal call_analysis.CALL_SOURCE_KEYS).
        text = SKILL.read_text(encoding="utf-8")
        for key in ("granola_id", "opportunite", "outcome", "type_entretien", "feeling",
                    "format", "heure", "interlocuteurs"):
            self.assertIn(f'"{key}"', text, key)

    def test_reflection_is_a_string_under_reflexion(self):
        # H1 deviation 1: `facts.reflection` is a string rendered as `## Réflexion`.
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("## Réflexion", text)
        self.assertNotIn("reflection.fit", text)
        self.assertNotIn("Lecture Renaud", text)


class TestCallCommand(unittest.TestCase):
    def test_command_delegates_to_the_namespaced_skill(self):
        text = COMMAND.read_text(encoding="utf-8")
        self.assertIn('Skill("gtm:call"', text)
        self.assertIn("Unknown skill", text)
        fm = _frontmatter(COMMAND)
        self.assertIn("Skill(gtm:call)", fm["allowed-tools"])


class TestCrmLogRetired(unittest.TestCase):
    """`/crm log` is gone from the gtm plugin; only `/crm log update` remains."""

    def test_no_crm_log_left_except_log_update(self):
        for path in GTM.rglob("*.md"):
            if path.name == "CHANGELOG.md":
                continue
            for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                for m in re.finditer(r"/crm log(?! update)\b", line):
                    # Allowed only when the line records the retirement itself.
                    self.assertIn("retiré", line, f"{path}:{n}: {line.strip()}")

    def test_no_log_section_in_crm(self):
        self.assertNotIn("## /crm log `", CRM_SKILL.read_text(encoding="utf-8"))
        self.assertNotIn("### `log <", CRM_COMMAND.read_text(encoding="utf-8"))
        self.assertIn("log update", CRM_COMMAND.read_text(encoding="utf-8"))

    def test_crm_no_longer_logs_interactions(self):
        fm = _frontmatter(CRM_SKILL)
        self.assertNotIn("mcp__plugin_hal_hal-mcp__log_interaction", fm["allowed-tools"])
        self.assertIn("mcp__plugin_hal_hal-mcp__update_interaction", fm["allowed-tools"])
        self.assertIn("mcp__plugin_hal_hal-mcp__list_interactions", fm["allowed-tools"])


if __name__ == "__main__":
    unittest.main()
