"""Tests for pull_mission.py — briefing parsing and config persistence."""

import json
import pytest
from pathlib import Path
from pull_mission import parse_briefing, load_config, save_config


VALID_BRIEFING = """\
---
edifice_version: "2.0"
edifice_mission_id: "abc-123"
edifice_mission_type: "suivi_chantier"
exported_at: "2026-04-21T12:00:00Z"
exported_by: "test@example.com"
supabase_url: "https://zgkvbjqlvebttbnkklpo.supabase.co"
---

# Briefing: Test Mission
"""


class TestParseBriefing:
    def test_valid_briefing(self, tmp_path):
        f = tmp_path / "test.edifice.md"
        f.write_text(VALID_BRIEFING)
        fm = parse_briefing(f)
        assert fm["edifice_mission_id"] == "abc-123"
        assert fm["edifice_version"] == "2.0"

    def test_missing_mission_id(self, tmp_path):
        f = tmp_path / "test.edifice.md"
        f.write_text("---\nedifice_version: '2.0'\n---\n# No mission ID")
        with pytest.raises(SystemExit, match="missing 'edifice_mission_id'"):
            parse_briefing(f)

    def test_missing_frontmatter_delimiters(self, tmp_path):
        f = tmp_path / "test.edifice.md"
        f.write_text("Just plain text, no YAML")
        with pytest.raises(SystemExit, match="YAML front-matter"):
            parse_briefing(f)

    def test_v1_format_rejected(self, tmp_path):
        """v1 format used mission_id (no edifice_ prefix) — must fail."""
        f = tmp_path / "test.edifice.md"
        f.write_text("---\nmission_id: abc-123\n---\n# Old format")
        with pytest.raises(SystemExit, match="missing 'edifice_mission_id'"):
            parse_briefing(f)


class TestConfigPersistence:
    def test_save_and_load(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pull_mission.CONFIG_DIR", tmp_path)
        monkeypatch.setattr("pull_mission.CONFIG_FILE", tmp_path / "config.json")
        save_config({"access_token": "tok", "refresh_token": "ref"})
        loaded = load_config()
        assert loaded["access_token"] == "tok"
        assert loaded["refresh_token"] == "ref"

    def test_load_missing_returns_none(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pull_mission.CONFIG_FILE", tmp_path / "nonexistent.json")
        assert load_config() is None


class TestDateVisiteFallback:
    def test_both_none_does_not_crash(self):
        """If both visited_at and created_at are None, should not TypeError."""
        project = {"name": "Draft", "visited_at": None, "created_at": None}
        date = (project.get("visited_at") or project.get("created_at") or "")[:10]
        assert date == ""

    def test_visited_at_preferred(self):
        project = {"visited_at": "2026-04-21T10:00:00Z", "created_at": "2026-04-01T10:00:00Z"}
        date = (project.get("visited_at") or project.get("created_at") or "")[:10]
        assert date == "2026-04-21"

    def test_fallback_to_created_at(self):
        project = {"visited_at": None, "created_at": "2026-04-01T10:00:00Z"}
        date = (project.get("visited_at") or project.get("created_at") or "")[:10]
        assert date == "2026-04-01"
