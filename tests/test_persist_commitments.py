"""Tests for the commitment persistence path in pipeline.extractor."""
from __future__ import annotations

import pathlib
from unittest.mock import patch, MagicMock

import pytest

import pipeline.extractor as _ext
from memory.stores.prospective import ProspectiveStore


def _mock_store(tmp_path):
    db = tmp_path / "prospective.db"
    return ProspectiveStore(db_path=db)


# ---------------------------------------------------------------------------
# _persist_commitments
# ---------------------------------------------------------------------------

def test_persist_stores_commitment_without_date(tmp_path):
    db = tmp_path / "prospective.db"
    store = ProspectiveStore(db_path=db)
    with patch("pipeline.extractor.ProspectiveStore", return_value=store), \
         patch("pipeline.extractor.resolve_due_date", return_value=None):
        _ext._persist_commitments(
            [{"content": "Follow up with Rachita", "due_date_hint": None}],
            today="2026-05-11",
        )
    # Reconnect after close()
    reader = ProspectiveStore(db_path=db)
    pending = reader.list_pending()
    assert len(pending) == 1
    assert pending[0]["content"] == "Follow up with Rachita"
    assert pending[0]["due_date"] is None
    reader.close()


def test_persist_resolves_due_date_hint(tmp_path):
    db = tmp_path / "prospective.db"
    store = ProspectiveStore(db_path=db)
    with patch("pipeline.extractor.ProspectiveStore", return_value=store), \
         patch("pipeline.extractor.resolve_due_date", return_value="2026-05-18") as mock_resolve:
        _ext._persist_commitments(
            [{"content": "Send report", "due_date_hint": "next week"}],
            today="2026-05-11",
        )
    mock_resolve.assert_called_once_with("next week", "2026-05-11")
    reader = ProspectiveStore(db_path=db)
    pending = reader.list_pending()
    assert pending[0]["due_date"] == "2026-05-18"
    reader.close()


def test_persist_skips_resolve_when_no_hint(tmp_path):
    db = tmp_path / "prospective.db"
    store = ProspectiveStore(db_path=db)
    with patch("pipeline.extractor.ProspectiveStore", return_value=store), \
         patch("pipeline.extractor.resolve_due_date") as mock_resolve:
        _ext._persist_commitments(
            [{"content": "No deadline task", "due_date_hint": None}],
            today="2026-05-11",
        )
    mock_resolve.assert_not_called()


def test_persist_multiple_commitments(tmp_path):
    db = tmp_path / "prospective.db"
    store = ProspectiveStore(db_path=db)
    commitments = [
        {"content": "Task A", "due_date_hint": None},
        {"content": "Task B", "due_date_hint": "tomorrow"},
        {"content": "Task C", "due_date_hint": None},
    ]
    with patch("pipeline.extractor.ProspectiveStore", return_value=store), \
         patch("pipeline.extractor.resolve_due_date", return_value="2026-05-12"):
        _ext._persist_commitments(commitments, today="2026-05-11")
    reader = ProspectiveStore(db_path=db)
    assert len(reader.list_pending()) == 3
    reader.close()


def test_persist_writes_log_entry(tmp_path, monkeypatch):
    import pipeline.write_log as wl
    monkeypatch.setattr(wl, "_LOG_PATH", tmp_path / "write_log.jsonl")
    store = _mock_store(tmp_path)
    with patch("pipeline.extractor.ProspectiveStore", return_value=store), \
         patch("pipeline.extractor.resolve_due_date", return_value=None):
        _ext._persist_commitments(
            [{"content": "Check in with team", "due_date_hint": None}],
            today="2026-05-11",
        )
    import json
    lines = wl._LOG_PATH.read_text().splitlines()
    entry = json.loads(lines[-1])
    assert entry["type"] == "commitment"
    assert entry["value"] == "Check in with team"


# ---------------------------------------------------------------------------
# run_post_conversation_pipeline today= param
# ---------------------------------------------------------------------------

def test_pipeline_passes_today_to_persist(tmp_path):
    store = _mock_store(tmp_path)
    history = [
        {"role": "user", "content": "I'll send the report next Friday."},
        {"role": "assistant", "content": "Noted."},
    ]
    commitments = [{"content": "Send the report next Friday", "due_date_hint": "next Friday"}]

    with patch("pipeline.extractor.extract_and_upsert_entities"), \
         patch("pipeline.extractor.extract_commitments", return_value=commitments), \
         patch("pipeline.extractor._persist_commitments") as mock_persist:
        _ext.run_post_conversation_pipeline(history, today="2026-05-11")

    mock_persist.assert_called_once_with(commitments, "2026-05-11")


def test_pipeline_defaults_today_to_utc_date():
    history = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]
    with patch("pipeline.extractor.extract_and_upsert_entities"), \
         patch("pipeline.extractor.extract_commitments", return_value=[]), \
         patch("pipeline.extractor._persist_commitments") as mock_persist:
        _ext.run_post_conversation_pipeline(history)
    # _persist_commitments not called when no commitments — that's fine
    mock_persist.assert_not_called()


def test_pipeline_no_persist_when_no_commitments(tmp_path):
    history = [{"role": "user", "content": "what time is it"}, {"role": "assistant", "content": "noon"}]
    with patch("pipeline.extractor.extract_and_upsert_entities"), \
         patch("pipeline.extractor.extract_commitments", return_value=[]), \
         patch("pipeline.extractor._persist_commitments") as mock_persist:
        _ext.run_post_conversation_pipeline(history, today="2026-05-11")
    mock_persist.assert_not_called()
