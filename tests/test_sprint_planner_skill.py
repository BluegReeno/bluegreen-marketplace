"""Invariants of `work:sprint-planner` — the « valide » gate of step 5.

hal S05 on the real rows (migration block 4, 2026-10-15, `p6-valide`): a « valide » sent before
any plan was carried forward, and 41 writes landed on the next message, which carried none.
"""
import unittest

from skilltext import REPO, read

SKILL = REPO / "plugins/work/skills/sprint-planner/SKILL.md"


class TestSprintPlannerGate(unittest.TestCase):
    def setUp(self):
        self.body = " ".join(read(SKILL).split())

    def test_the_gate_is_a_section_of_step_5(self):
        step5 = self.body.split("## Étape 5", 1)[1].split("## Étape 6", 1)[0]
        self.assertIn("### La porte", step5)
        self.assertIn("répond au plan complet affiché dans ton message juste avant", step5)

    def test_early_valide_changed_plan_and_silence_are_not_a_go(self):
        for rule in ("Un « valide » arrivé avant le plan ne vaut pas go",
                     "ne vaut pas go, même si elle contient « valide »",
                     "Une réponse sans « valide » explicite n'écrit rien",
                     "Jamais un point ouvert réglé par un défaut que Renaud n'a pas vu"):
            self.assertIn(rule, self.body, rule)

    def test_open_points_are_listed_with_their_default(self):
        self.assertIn("**Points ouverts**", self.body)


if __name__ == "__main__":
    unittest.main()
