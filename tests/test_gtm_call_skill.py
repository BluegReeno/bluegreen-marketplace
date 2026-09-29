"""
Invariants of the `gtm:call` skill (hal#192) — the contract that `jobsearch:log-cr`
(renaud-marketplace) and `plugins/gtm/commands/call.md` rely on, and the hygiene a public repo
needs. Prose skills have no unit test; these guards catch the drifts that would break a caller
silently: a renamed skill, a `disable-model-invocation` that would refuse the cross-plugin
`Skill("gtm:call")`, a hal tool dropped from `allowed-tools`, an email literal, or `/crm log`
resurrected next to its replacement.

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
        # `Bash(uv *)` holds a space: tokens are either `Name(...)` or a bare name.
        tools = re.findall(r"\S+\([^)]*\)|\S+", self.fm["allowed-tools"].strip('"'))
        for name in ("save_document", "log_interaction", "list_interactions",
                     "update_interaction", "whoami", "list_projects"):
            self.assertIn(f"mcp__plugin_hal_hal-mcp__{name}", tools, name)
        self.assertIn("Bash(uv *)", tools)   # `uv run --project "$HAL" …` for render + ingest
        self.assertIn("Bash(test *)", tools)  # the pre-flight

    def test_allowed_tools_call_no_other_skill(self):
        # gtm:call is the leaf of the chain: log-cr calls it, it calls nobody.
        self.assertNotIn("Skill(", self.fm["allowed-tools"])

    def test_description_names_the_caller(self):
        self.assertIn("log-cr", self.fm["description"])


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
