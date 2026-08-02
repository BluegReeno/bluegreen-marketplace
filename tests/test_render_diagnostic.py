"""
Tests for render_diagnostic.py — _render_methodo_item, methodo tag filtering,
and _building_block.
Closes #9 (methodo) and the _building_block case from #5.
"""
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch, call

# Stub all external packages before importing the module under test.
for _mod in ("docxtpl", "docx", "docx.shared", "PIL", "PIL.Image", "PIL.ImageOps"):
    sys.modules.setdefault(_mod, MagicMock())

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "plugins/edifice/scripts"))
import render_diagnostic


class TestRenderMethodoItem(unittest.TestCase):
    def setUp(self):
        self.doc = MagicMock()

    def test_photo_resolved_and_inline_image_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            photo_file = pathlib.Path(tmp) / "photo.jpg"
            photo_file.write_bytes(b"fake")
            note = {"photo": "photo.jpg", "description": "Fissure en façade"}
            with patch.object(render_diagnostic, "_inline_image_auto_orient", return_value="IMG") as mock_img:
                result = render_diagnostic._render_methodo_item(note, tmp, self.doc)
            mock_img.assert_called_once_with(self.doc, photo_file, max_width_cm=10.0, max_height_cm=12.0)
            self.assertEqual(result["photo"], "IMG")
            self.assertEqual(result["description"], "Fissure en façade")

    def test_description_falls_back_to_name_when_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            note = {"name": "Vue générale toiture"}
            result = render_diagnostic._render_methodo_item(note, tmp, self.doc)
            self.assertEqual(result["description"], "Vue générale toiture")
            self.assertIsNone(result["photo"])

    def test_photo_none_when_file_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            note = {"photo": "missing.jpg", "description": "Desc"}
            result = render_diagnostic._render_methodo_item(note, tmp, self.doc)
            self.assertIsNone(result["photo"])

    def test_photo_none_when_no_photo_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            note = {"description": "Desc"}
            result = render_diagnostic._render_methodo_item(note, tmp, self.doc)
            self.assertIsNone(result["photo"])


class TestMethodoTagFiltering(unittest.TestCase):
    """Tag filtering inside _build_context (lines ~131-138 of render_diagnostic.py)."""

    def _run_build_context(self, notes, tmp):
        context = {"disorders": [], "notes": notes}
        doc = MagicMock()
        with patch.object(render_diagnostic, "_render_methodo_item", return_value={"description": "", "photo": None}) as mock_item, \
             patch.object(render_diagnostic, "_inline_image_auto_orient", return_value=None):
            render_diagnostic._build_context(context, tmp, doc)
        return mock_item.call_args_list

    def test_visite_terrain_tag_included(self):
        note = {"metadata": {"tag": "methodo:visite_terrain"}, "name": "Vue"}
        with tempfile.TemporaryDirectory() as tmp:
            calls = self._run_build_context([note], tmp)
        called_notes = [c.args[0] for c in calls]
        self.assertIn(note, called_notes)

    def test_strict_tag_equality_no_partial_match(self):
        note = {"metadata": {"tag": "methodo:visite_terrainX"}, "name": "Wrong"}
        with tempfile.TemporaryDirectory() as tmp:
            calls = self._run_build_context([note], tmp)
        called_notes = [c.args[0] for c in calls]
        self.assertNotIn(note, called_notes)

    def test_note_without_tag_not_included(self):
        note = {"metadata": {}, "name": "No tag"}
        with tempfile.TemporaryDirectory() as tmp:
            calls = self._run_build_context([note], tmp)
        called_notes = [c.args[0] for c in calls]
        self.assertNotIn(note, called_notes)

    def test_moyens_tag_included(self):
        note = {"metadata": {"tag": "methodo:moyens"}, "name": "Équipement"}
        with tempfile.TemporaryDirectory() as tmp:
            calls = self._run_build_context([note], tmp)
        called_notes = [c.args[0] for c in calls]
        self.assertIn(note, called_notes)


class TestBuildingBlock(unittest.TestCase):
    """_building_block converts building.image_2d path to InlineImage, or None if missing."""

    def setUp(self):
        self.doc = MagicMock()

    def test_returns_none_image_when_path_absent(self):
        result = render_diagnostic._building_block({}, self.doc)
        self.assertIsNone(result["image_2d"])

    def test_returns_none_image_when_file_missing(self):
        result = render_diagnostic._building_block(
            {"building": {"image_2d": "/nonexistent/path.png"}}, self.doc
        )
        self.assertIsNone(result["image_2d"])

    def test_returns_inline_image_when_file_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            img_file = pathlib.Path(tmp) / "map.png"
            img_file.write_bytes(b"fake")
            with patch.object(render_diagnostic, "_inline_image_auto_orient", return_value="IMG") as mock_img:
                result = render_diagnostic._building_block(
                    {"building": {"image_2d": str(img_file)}}, self.doc
                )
            mock_img.assert_called_once()
            self.assertEqual(result["image_2d"], "IMG")


if __name__ == "__main__":
    unittest.main()
