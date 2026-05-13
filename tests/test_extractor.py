"""Tests for pipeline.extractor — unit-testable parts only (no claude -p calls)."""
from __future__ import annotations

import json
import pathlib
import sys

import pytest


# ---------------------------------------------------------------------------
# _entity_path
# ---------------------------------------------------------------------------

from pipeline.extractor import _entity_path, _SEMANTIC_DIR


def test_entity_path_person():
    p = _entity_path("person", "rachita")
    assert p == _SEMANTIC_DIR / "people" / "rachita.json"


def test_entity_path_project():
    p = _entity_path("project", "jarvis")
    assert p == _SEMANTIC_DIR / "projects" / "jarvis.json"


def test_entity_path_preference():
    p = _entity_path("preference", "user")
    assert p == _SEMANTIC_DIR / "preferences.json"


# ---------------------------------------------------------------------------
# _load_entity
# ---------------------------------------------------------------------------

from pipeline.extractor import _load_entity


def test_load_entity_nonexistent_person(tmp_path):
    path = tmp_path / "nobody.json"
    data = _load_entity(path, "person", "nobody")
    assert data["name"] == "Nobody"
    assert data["type"] == "person"
    assert data["facts"] == {}


def test_load_entity_nonexistent_preference(tmp_path):
    path = tmp_path / "preferences.json"
    data = _load_entity(path, "preference", "user")
    assert "facts" in data


def test_load_entity_existing_file(tmp_path):
    path = tmp_path / "rachita.json"
    content = {"name": "Rachita", "type": "person", "facts": {"role": {"value": "manager", "confidence": 0.9}}}
    path.write_text(json.dumps(content))
    data = _load_entity(path, "person", "rachita")
    assert data["facts"]["role"]["value"] == "manager"


# ---------------------------------------------------------------------------
# _upsert_fact — using tmp directory to avoid touching real semantic store
# ---------------------------------------------------------------------------

from pipeline.extractor import _upsert_fact, _SEMANTIC_DIR as _REAL_DIR
import pipeline.extractor as _ext_mod


def test_upsert_fact_creates_file(tmp_path, monkeypatch):
    monkeypatch.setattr(_ext_mod, "_SEMANTIC_DIR", tmp_path)
    _upsert_fact("person", "priya", "role", "engineer", 0.9)
    written = (tmp_path / "people" / "priya.json")
    assert written.exists()
    data = json.loads(written.read_text())
    assert data["facts"]["role"]["value"] == "engineer"
    assert data["facts"]["role"]["confidence"] == 0.9


def test_upsert_fact_skips_high_confidence(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(_ext_mod, "_SEMANTIC_DIR", tmp_path)
    # Write a high-confidence fact first
    _upsert_fact("person", "priya", "role", "engineer", 0.9)
    # Try to overwrite with lower confidence — should be skipped
    _upsert_fact("person", "priya", "role", "intern", 0.6)
    data = json.loads((tmp_path / "people" / "priya.json").read_text())
    assert data["facts"]["role"]["value"] == "engineer"
    captured = capsys.readouterr()
    assert "skipped" in captured.err


def test_upsert_fact_overwrites_low_confidence(tmp_path, monkeypatch):
    monkeypatch.setattr(_ext_mod, "_SEMANTIC_DIR", tmp_path)
    _upsert_fact("person", "priya", "role", "intern", 0.6)
    _upsert_fact("person", "priya", "role", "engineer", 0.9)
    data = json.loads((tmp_path / "people" / "priya.json").read_text())
    assert data["facts"]["role"]["value"] == "engineer"


def test_upsert_preference_uses_preferences_json(tmp_path, monkeypatch):
    monkeypatch.setattr(_ext_mod, "_SEMANTIC_DIR", tmp_path)
    _upsert_fact("preference", "user", "prefers_morning_meetings", "I prefer morning meetings", 0.9)
    prefs_path = tmp_path / "preferences.json"
    assert prefs_path.exists()
    data = json.loads(prefs_path.read_text())
    assert "prefers_morning_meetings" in data["facts"]


# ---------------------------------------------------------------------------
# run_post_conversation_pipeline — smoke: empty history is a no-op
# ---------------------------------------------------------------------------

from pipeline.extractor import run_post_conversation_pipeline


def test_pipeline_empty_history_does_not_raise():
    run_post_conversation_pipeline([])


def test_pipeline_single_turn_does_not_raise():
    # Single assistant-only turn — should not error even if claude is unavailable
    try:
        run_post_conversation_pipeline([{"role": "user", "content": "hello"}])
    except SystemExit:
        pass  # claude -p not available in test env is acceptable
