"""
Tests for build_context.py — IGN 2D map functions.
Covers: build_building_context, _download_building_2d_map.
Closes #5.
"""
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from io import BytesIO
from urllib.error import URLError

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "plugins/hal/scripts"))
import build_context


class FakeResponse:
    def __init__(self, data: bytes, content_type: str = "image/png"):
        self._data = data
        self._ct = content_type
        self.headers = {"Content-Type": content_type}

    def read(self, n=-1):
        return self._data if n == -1 else self._data[:n]

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass


class TestDownloadBuilding2dMap(unittest.TestCase):
    def test_valid_png_written_to_disk(self):
        png_bytes = b"\x89PNG fake"
        resp = FakeResponse(png_bytes, "image/png")
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp)
            with patch("urllib.request.urlopen", return_value=resp):
                result = build_context._download_building_2d_map(
                    "https://example.com/map.png", "b1", out
                )
            self.assertIsNotNone(result)
            self.assertTrue(result.exists())
            self.assertEqual(result.read_bytes(), png_bytes)

    def test_xml_content_type_rejected(self):
        resp = FakeResponse(b"<xml/>", "application/xml")
        with tempfile.TemporaryDirectory() as tmp:
            with patch("urllib.request.urlopen", return_value=resp):
                result = build_context._download_building_2d_map(
                    "https://example.com/bad", "b2", pathlib.Path(tmp)
                )
            self.assertIsNone(result)

    def test_http_error_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("urllib.request.urlopen", side_effect=URLError("timeout")):
                result = build_context._download_building_2d_map(
                    "https://example.com/map.png", "b3", pathlib.Path(tmp)
                )
            self.assertIsNone(result)


class TestBuildBuildingContext(unittest.TestCase):
    def test_url_present_download_path_taken(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake_path = pathlib.Path(tmp) / "b1_2d_map.png"
            with patch.object(build_context, "_download_building_2d_map", return_value=fake_path) as mock_dl:
                result = build_context.build_building_context(
                    {"id": "b1", "building_2d_map_url": "https://example.com/map.png"},
                    pathlib.Path(tmp),
                )
            mock_dl.assert_called_once()
            self.assertEqual(result["image_2d"], str(fake_path))
            self.assertEqual(result["image_2d_url"], "https://example.com/map.png")

    def test_url_absent_lat_lon_present_ign_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake_path = pathlib.Path(tmp) / "b2_2d_map_auto.png"
            with patch.object(build_context, "_generate_ign_map", return_value=fake_path) as mock_ign:
                result = build_context.build_building_context(
                    {"id": "b2", "latitude": 48.8566, "longitude": 2.3522},
                    pathlib.Path(tmp),
                )
            mock_ign.assert_called_once()
            self.assertEqual(result["image_2d"], str(fake_path))

    def test_url_absent_no_coords_returns_none_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = build_context.build_building_context(
                {"id": "b3"},
                pathlib.Path(tmp),
            )
        self.assertIsNone(result["image_2d"])

    def test_download_fails_falls_back_to_ign(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake_path = pathlib.Path(tmp) / "b4_2d_map_auto.png"
            with patch.object(build_context, "_download_building_2d_map", return_value=None), \
                 patch.object(build_context, "_generate_ign_map", return_value=fake_path) as mock_ign:
                result = build_context.build_building_context(
                    {"id": "b4", "building_2d_map_url": "https://x.com/map.png",
                     "latitude": 48.8566, "longitude": 2.3522},
                    pathlib.Path(tmp),
                )
            mock_ign.assert_called_once()
            self.assertEqual(result["image_2d"], str(fake_path))

    def test_building_none_returns_none(self):
        result = build_context.build_building_context(None, pathlib.Path("/tmp"))
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
