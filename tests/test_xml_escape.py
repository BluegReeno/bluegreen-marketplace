"""
Tests for xml_escape.py — recursive XML-escaping helper for docxtpl contexts.
Closes #47 (an unescaped & in free text breaks the docx render).
"""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "plugins/hal/scripts"))
from xml_escape import escape_xml_values


class Sentinel:
    """Stand-in for InlineImage and any other non-str object that must pass through untouched."""


class TestEscapeXmlValues(unittest.TestCase):
    def test_ampersand_escaped(self):
        self.assertEqual(escape_xml_values("Dupont & Fils"), "Dupont &amp; Fils")

    def test_angle_brackets_escaped(self):
        self.assertEqual(escape_xml_values("< 2 mm"), "&lt; 2 mm")
        self.assertEqual(escape_xml_values("> 2 mm"), "&gt; 2 mm")

    def test_quotes_pass_through_unchanged(self):
        # Quotes are not special in XML element text content — no escaping needed.
        self.assertEqual(escape_xml_values('charpente "type A"'), 'charpente "type A"')
        self.assertEqual(escape_xml_values("charpente 'type A'"), "charpente 'type A'")

    def test_already_escaped_ampersand_not_double_escaped_by_a_single_pass(self):
        # escape() is only ever invoked once per render — a single pass over
        # literal "&amp;" turns just the "&" into "&amp;", never "&amp;amp;".
        result = escape_xml_values("Tension &amp; Cie")
        self.assertEqual(result, "Tension &amp;amp; Cie")
        self.assertNotIn("&amp;amp;amp;", result)

    def test_non_str_leaf_passed_through_untouched(self):
        sentinel = Sentinel()
        self.assertIs(escape_xml_values(sentinel), sentinel)
        self.assertIsNone(escape_xml_values(None))
        self.assertEqual(escape_xml_values(42), 42)
        self.assertIs(escape_xml_values(True), True)

    def test_recurses_into_dict(self):
        result = escape_xml_values({"client": "Dupont & Fils", "count": 3})
        self.assertEqual(result, {"client": "Dupont &amp; Fils", "count": 3})

    def test_recurses_into_list(self):
        result = escape_xml_values(["A & B", "C"])
        self.assertEqual(result, ["A &amp; B", "C"])

    def test_mixed_context_text_and_inline_image_objects_preserved(self):
        photo = Sentinel()
        context = {
            "client": "Dupont & Fils",
            "building": {"image_2d": photo, "image_2d_url": "https://example.com?a=1&b=2"},
            "disorders": [
                {"description": "Fissure < 2mm & humidité", "photo1": photo, "photo2": None},
            ],
        }
        result = escape_xml_values(context)
        self.assertEqual(result["client"], "Dupont &amp; Fils")
        self.assertIs(result["building"]["image_2d"], photo)
        self.assertEqual(result["building"]["image_2d_url"], "https://example.com?a=1&amp;b=2")
        self.assertEqual(result["disorders"][0]["description"], "Fissure &lt; 2mm &amp; humidité")
        self.assertIs(result["disorders"][0]["photo1"], photo)
        self.assertIsNone(result["disorders"][0]["photo2"])


if __name__ == "__main__":
    unittest.main()
