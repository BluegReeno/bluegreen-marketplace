"""
Parity tripwire between build_context.py and hal-mcp's TypeScript port.

`plugins/edifice/scripts/build_context.py` (build_header, build_observations,
_clean_address, _parse_mission_context) and hal-mcp's `index.ts`
(buildHeader, buildObservationsAndNotes, cleanAddress, parseMissionContext) hold the
same context.json-shape logic in two languages, in two repositories. hal-mcp is
private and not checked out alongside this repo, so this test cannot invoke the
TypeScript side directly and assert byte-for-byte equality across the repo boundary
— see plugins/edifice/scripts/build_context.py's module docstring for the declared
source-of-truth split (this file is authoritative; hal-mcp mirrors it).

What this test CAN enforce from here: build_header() + build_observations() must
keep producing exactly the recorded golden shape for a fixed input, for all three
project types. Any accidental field addition, removal or rename fails this test —
that is the signal to also update hal-mcp's mirror, not something a golden-shape
diff can catch on its own.

Golden fixtures: tests/fixtures/edifice/<project_type>/context_shape.golden.json —
the literal return value of build_header() + build_observations() on the matching
mcp_response.json. Distinct from the sibling context.json used by
test_edifice_render_smoke.py, which has already been hand-edited to simulate the
post-/edifice-improve step and is not a raw build_context.py output.

Closes #84.
"""
import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "plugins/edifice/scripts"))
import build_context  # noqa: E402

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures/edifice"
PROJECT_TYPES = ["diagnostic", "suivi_chantier", "devis"]


def _build_shape(project_type: str) -> dict:
    data = json.loads((FIXTURES_DIR / project_type / "mcp_response.json").read_text(encoding="utf-8"))
    project = data.get("project") or {}
    building = data.get("building")
    notes = data.get("notes") or []
    photos = data.get("photos") or []
    header = build_context.build_header(project, building, project_type)
    observations, free_notes = build_context.build_observations(notes, photos, project_type)
    return {**header, "observations": observations, "notes": free_notes}


class TestContextShapeParity(unittest.TestCase):
    """build_header()/build_observations() output must match the recorded golden shape."""

    def test_diagnostic_shape_matches_golden(self):
        self._assert_matches_golden("diagnostic")

    def test_suivi_chantier_shape_matches_golden(self):
        self._assert_matches_golden("suivi_chantier")

    def test_devis_shape_matches_golden(self):
        self._assert_matches_golden("devis")

    def _assert_matches_golden(self, project_type: str):
        golden = json.loads(
            (FIXTURES_DIR / project_type / "context_shape.golden.json").read_text(encoding="utf-8")
        )
        self.assertEqual(_build_shape(project_type), golden)

    def test_golden_fixtures_cover_all_three_project_types(self):
        for project_type in PROJECT_TYPES:
            self.assertTrue(
                (FIXTURES_DIR / project_type / "context_shape.golden.json").exists(),
                f"missing context_shape.golden.json for {project_type}",
            )


if __name__ == "__main__":
    unittest.main()
