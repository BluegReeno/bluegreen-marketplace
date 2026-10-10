"""hal q56's rule, for every skill that launches a hal script: the environment file is a variable
(`HAL_ENV_FILE`) and the host of `SUPABASE_URL` is shown before any write — so the script and the
`hal-mcp` connector aim at the same instance. A skill that hard-codes `$HAL/.env` writes to whatever
that checkout's `.env` names, which on 2026-10-10 was still the frozen cloud.
"""
import re
import unittest

from skilltext import REPO, read

LAUNCHES_A_HAL_SCRIPT = re.compile(r'"\$HAL/scripts/')


def script_skills():
    return [p for p in sorted((REPO / "plugins").rglob("SKILL.md")) if LAUNCHES_A_HAL_SCRIPT.search(read(p))]


class TestEnvFileRule(unittest.TestCase):
    def test_the_rule_has_skills_to_guard(self):
        # gtm:call and knowledge:ingest today; zero would mean the pattern above went stale.
        self.assertGreaterEqual(len(script_skills()), 2)

    def test_every_script_skill_selects_its_env_file_and_shows_the_host(self):
        for path in script_skills():
            text = read(path)
            with self.subTest(skill=str(path.relative_to(REPO))):
                self.assertIn('ENVF="${HAL_ENV_FILE:-$HAL/.env}"', text)
                self.assertIn("grep '^SUPABASE_URL=' \"$ENVF\"", text)
                self.assertNotRegex(text, r'--env-file "\$HAL/\.env"')
                self.assertNotIn("cat \"$ENVF\"", text)


if __name__ == "__main__":
    unittest.main()
