"""Shape invariants that hold for every plugin of the marketplace."""
import unittest

from skilltext import REPO

PLUGINS = sorted(p for p in (REPO / "plugins").iterdir() if p.is_dir())


class TestNoCommandShadowsASkill(unittest.TestCase):
    def test_no_command_is_named_like_a_skill_of_its_plugin(self):
        # A command and a skill of one plugin share the namespace `<plugin>:<name>`; the command
        # wins, so a skill of the same name is unreachable through the Skill tool (hal S05 run
        # 20261011-165111: `work:sprint-planner` served its command stub, never its SKILL.md).
        for plugin in PLUGINS:
            commands = {p.stem for p in (plugin / "commands").glob("*.md")}
            skills = {p.parent.name for p in (plugin / "skills").glob("*/SKILL.md")}
            self.assertEqual(sorted(commands & skills), [], f"{plugin.name}: command shadows skill")


if __name__ == "__main__":
    unittest.main()
