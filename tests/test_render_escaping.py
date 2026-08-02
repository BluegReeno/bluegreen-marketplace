"""
Integration tests: each render_*.py entry point must escape XML in the
context it hands to doc.render(), while InlineImage objects (photos, the
2D building map) pass through unchanged. Closes #47.
"""
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Stub all external packages before importing the modules under test.
for _mod in ("docxtpl", "docx", "docx.shared", "PIL", "PIL.Image", "PIL.ImageOps"):
    sys.modules.setdefault(_mod, MagicMock())

SCRIPTS_DIR = pathlib.Path(__file__).parent.parent / "plugins/edifice/scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
import render_diagnostic
import render_devis
import render_cr_visite


def _mock_docx_template(tmp_dir):
    """A DocxTemplate stand-in whose .save() writes a real (fake) file, so
    the renderer's out.stat() call after save() succeeds."""
    mock_doc = MagicMock()
    mock_doc.save.side_effect = lambda path: pathlib.Path(path).write_bytes(b"fake docx")
    return mock_doc


class TestRenderDiagnosticEscaping(unittest.TestCase):
    def test_ampersand_escaped_and_photo_object_preserved(self):
        photo_sentinel = object()
        with tempfile.TemporaryDirectory() as tmp:
            photo_file = pathlib.Path(tmp) / "photo.jpg"
            photo_file.write_bytes(b"fake")
            context = {
                "client": "Dupont & Fils",
                "adresse": "1 rue <Test>",
                "objet_visite": "Visite & contrôle",
                "disorders": [
                    {"description": "Fissure & humidité", "photos": ["photo.jpg"]},
                ],
                "notes": [],
            }
            mock_doc = _mock_docx_template(tmp)
            out_path = pathlib.Path(tmp) / "out.docx"
            with patch.object(render_diagnostic, "DocxTemplate", return_value=mock_doc), \
                 patch.object(render_diagnostic, "_inline_image_auto_orient", return_value=photo_sentinel):
                render_diagnostic.render_diagnostic(context, photos_dir=tmp, output_path=str(out_path))

        rendered_ctx = mock_doc.render.call_args.args[0]
        self.assertEqual(rendered_ctx["client"], "Dupont &amp; Fils")
        self.assertEqual(rendered_ctx["adresse"], "1 rue &lt;Test&gt;")
        self.assertEqual(rendered_ctx["contexte"], "Visite &amp; contrôle")
        self.assertEqual(rendered_ctx["disorders"][0]["description"], "Fissure &amp; humidité")
        # The photo InlineImage stand-in must survive escaping untouched — not stringified.
        self.assertIs(rendered_ctx["disorders"][0]["photo1"], photo_sentinel)

    def test_building_image_2d_none_stays_none_not_stringified(self):
        with tempfile.TemporaryDirectory() as tmp:
            context = {"client": "A & B", "disorders": [], "notes": []}
            mock_doc = _mock_docx_template(tmp)
            out_path = pathlib.Path(tmp) / "out.docx"
            with patch.object(render_diagnostic, "DocxTemplate", return_value=mock_doc):
                render_diagnostic.render_diagnostic(context, photos_dir=tmp, output_path=str(out_path))
        rendered_ctx = mock_doc.render.call_args.args[0]
        self.assertIsNone(rendered_ctx["building"]["image_2d"])


class TestRenderDevisEscaping(unittest.TestCase):
    def test_ampersand_escaped_in_devis_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            context = {
                "client": "Dupont & Fils",
                "description_batiment": "Immeuble < 1950 & réhabilité",
                "documents_fournis": [{"name": "Plan & coupe", "fourni": True}],
            }
            mock_doc = _mock_docx_template(tmp)
            out_path = pathlib.Path(tmp) / "out.docx"
            with patch.object(render_devis, "DocxTemplate", return_value=mock_doc):
                render_devis.render_devis(context, output_path=str(out_path))

        rendered_ctx = mock_doc.render.call_args.args[0]
        self.assertEqual(rendered_ctx["client"], "Dupont &amp; Fils")
        self.assertEqual(rendered_ctx["description_batiment"], "Immeuble &lt; 1950 &amp; réhabilité")
        self.assertEqual(rendered_ctx["documents_fournis"][0]["name"], "Plan &amp; coupe")
        self.assertEqual(rendered_ctx["documents_fournis"][0]["fourni_str"], "Oui")


class TestRenderCrVisiteEscaping(unittest.TestCase):
    def test_ampersand_escaped_and_photo_object_preserved(self):
        photo_sentinel = object()
        with tempfile.TemporaryDirectory() as tmp:
            photo_file = pathlib.Path(tmp) / "photo.jpg"
            photo_file.write_bytes(b"fake")
            context = {
                "client": "Dupont & Fils",
                "synthese": "RAS & conforme",
                "participants": [{"nom": "A & B", "fonction": "MOE"}],
                "observations": [
                    {"description": "Fissure & humidité", "photo": "photo.jpg"},
                ],
            }
            mock_doc = _mock_docx_template(tmp)
            out_path = pathlib.Path(tmp) / "out.docx"
            with patch.object(render_cr_visite, "DocxTemplate", return_value=mock_doc), \
                 patch.object(render_cr_visite, "_inline_image_auto_orient", return_value=photo_sentinel):
                render_cr_visite.render_cr(context, photos_dir=tmp, output_path=str(out_path))

        rendered_ctx = mock_doc.render.call_args.args[0]
        self.assertEqual(rendered_ctx["client"], "Dupont &amp; Fils")
        self.assertEqual(rendered_ctx["synthese"], "RAS &amp; conforme")
        self.assertEqual(rendered_ctx["participants"][0]["nom"], "A &amp; B")
        self.assertEqual(rendered_ctx["observations"][0]["observation_action"], "Fissure &amp; humidité")
        self.assertIs(rendered_ctx["observations"][0]["photo"], photo_sentinel)


if __name__ == "__main__":
    unittest.main()
