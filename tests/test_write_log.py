"""Tests for pipeline.write_log."""
from __future__ import annotations

import json
import pathlib

import pytest

import pipeline.write_log as wl


@pytest.fixture(autouse=True)
def patch_log_path(tmp_path, monkeypatch):
    monkeypatch.setattr(wl, "_LOG_PATH", tmp_path / "write_log.jsonl")


def test_append_creates_file():
    wl.append("entity", "rachita/role", "manager")
    assert wl._LOG_PATH.exists()


def test_append_writes_valid_json_line():
    wl.append("preference", "user/morning_meetings", "prefers morning")
    lines = wl._LOG_PATH.read_text().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["type"] == "preference"
    assert entry["key"] == "user/morning_meetings"
    assert entry["value"] == "prefers morning"
    assert "timestamp" in entry


def test_append_multiple_lines():
    wl.append("entity", "a/b", "v1")
    wl.append("commitment", "none", "follow up")
    wl.append("episode", "importance=0.8", "summary text")
    lines = wl._LOG_PATH.read_text().splitlines()
    assert len(lines) == 3


def test_append_is_append_only():
    wl.append("entity", "x/y", "first")
    wl.append("entity", "x/y", "second")
    lines = wl._LOG_PATH.read_text().splitlines()
    values = [json.loads(l)["value"] for l in lines]
    assert values == ["first", "second"]


def test_append_includes_source_turn_when_provided():
    wl.append("entity", "k", "v", source_turn=3)
    entry = json.loads(wl._LOG_PATH.read_text().strip())
    assert entry.get("source_turn") == 3
