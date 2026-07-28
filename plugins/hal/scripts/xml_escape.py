#!/usr/bin/env python3
"""
xml_escape.py — Recursive XML-escaping helper for docxtpl render contexts.

docxtpl interpolates values straight into the docx's XML with no autoescaping,
so free text containing &, <, or > produces an invalid document. Escape every
str leaf with xml.sax.saxutils.escape (it orders & before </>, avoiding the
double-escaping bug of hand-rolled .replace() chains) while recursing through
dict/list containers. Every other type (InlineImage, int, bool, None, ...) is
passed through untouched so photos and non-text fields keep working.
"""

from xml.sax.saxutils import escape


def escape_xml_values(value):
    if isinstance(value, str):
        return escape(value)
    if isinstance(value, dict):
        return {k: escape_xml_values(v) for k, v in value.items()}
    if isinstance(value, list):
        return [escape_xml_values(v) for v in value]
    return value
