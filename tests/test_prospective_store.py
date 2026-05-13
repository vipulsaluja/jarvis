"""Tests for memory.stores.prospective.ProspectiveStore."""
from __future__ import annotations

import pathlib
import tempfile

import pytest

from memory.stores.prospective import ProspectiveStore


@pytest.fixture
def store(tmp_path):
    db = tmp_path / "test_prospective.db"
    s = ProspectiveStore(db_path=db)
    yield s
    s.close()


# ---------------------------------------------------------------------------
# add / list_pending
# ---------------------------------------------------------------------------

def test_add_returns_id(store):
    item_id = store.add("Buy groceries")
    assert isinstance(item_id, str) and len(item_id) == 36  # UUID


def test_list_pending_empty_on_init(store):
    assert store.list_pending() == []


def test_list_pending_returns_added_items(store):
    store.add("Task A")
    store.add("Task B")
    pending = store.list_pending()
    assert len(pending) == 2
    assert all(p["status"] == "pending" for p in pending)


def test_add_stores_all_fields(store):
    item_id = store.add(
        content="Follow up with Rachita",
        due_date="2026-05-15",
        trigger_condition="rachita promotion",
        source_episode="ep-123",
    )
    pending = store.list_pending()
    assert len(pending) == 1
    item = pending[0]
    assert item["id"] == item_id
    assert item["content"] == "Follow up with Rachita"
    assert item["due_date"] == "2026-05-15"
    assert item["trigger_condition"] == "rachita promotion"
    assert item["source_episode"] == "ep-123"
    assert item["created_at"] is not None


# ---------------------------------------------------------------------------
# get_due
# ---------------------------------------------------------------------------

def test_get_due_returns_overdue_items(store):
    store.add("Overdue task", due_date="2026-05-09")
    store.add("Future task", due_date="2026-05-20")
    store.add("No date task")

    due = store.get_due("2026-05-11")
    assert len(due) == 1
    assert due[0]["content"] == "Overdue task"


def test_get_due_includes_same_day(store):
    store.add("Due today", due_date="2026-05-11")
    due = store.get_due("2026-05-11")
    assert len(due) == 1


def test_get_due_excludes_no_date_items(store):
    store.add("No date", trigger_condition="something happens")
    due = store.get_due("2026-05-11")
    assert due == []


def test_get_due_excludes_completed(store):
    item_id = store.add("Was due", due_date="2026-05-09")
    store.complete(item_id)
    due = store.get_due("2026-05-11")
    assert due == []


def test_get_due_ordered_by_date(store):
    store.add("Later", due_date="2026-05-10")
    store.add("Earlier", due_date="2026-05-08")
    due = store.get_due("2026-05-11")
    assert due[0]["content"] == "Earlier"
    assert due[1]["content"] == "Later"


# ---------------------------------------------------------------------------
# get_condition_triggered
# ---------------------------------------------------------------------------

def test_condition_triggered_matches_keyword(store):
    store.add("Follow up after release", trigger_condition="release deployment")
    result = store.get_condition_triggered(["release"])
    assert len(result) == 1


def test_condition_triggered_case_insensitive(store):
    store.add("Check Rachita status", trigger_condition="Rachita promotion")
    result = store.get_condition_triggered(["rachita"])
    assert len(result) == 1


def test_condition_triggered_no_match(store):
    store.add("Check Rachita status", trigger_condition="rachita promotion")
    result = store.get_condition_triggered(["release", "deployment"])
    assert result == []


def test_condition_triggered_empty_keywords(store):
    store.add("Something", trigger_condition="keyword")
    assert store.get_condition_triggered([]) == []


def test_condition_triggered_excludes_no_condition(store):
    store.add("Plain reminder", due_date="2026-05-15")
    result = store.get_condition_triggered(["reminder"])
    assert result == []


def test_condition_triggered_excludes_completed(store):
    item_id = store.add("Done item", trigger_condition="release")
    store.complete(item_id)
    result = store.get_condition_triggered(["release"])
    assert result == []


# ---------------------------------------------------------------------------
# complete
# ---------------------------------------------------------------------------

def test_complete_removes_from_pending(store):
    item_id = store.add("Finish report")
    store.complete(item_id)
    assert store.list_pending() == []


def test_complete_sets_status_done(store):
    item_id = store.add("Task")
    store.complete(item_id)
    # Direct DB check — fetch all rows
    rows = store._conn.execute("SELECT status FROM prospective WHERE id = ?", (item_id,)).fetchall()
    assert rows[0][0] == "done"


def test_complete_unknown_id_is_noop(store):
    store.add("Real task")
    store.complete("non-existent-id")
    assert len(store.list_pending()) == 1


# ---------------------------------------------------------------------------
# persistence across connections
# ---------------------------------------------------------------------------

def test_data_persists_across_reconnect(tmp_path):
    db = tmp_path / "persist.db"
    s1 = ProspectiveStore(db_path=db)
    item_id = s1.add("Persisted task", due_date="2026-06-01")
    s1.close()

    s2 = ProspectiveStore(db_path=db)
    pending = s2.list_pending()
    s2.close()

    assert len(pending) == 1
    assert pending[0]["id"] == item_id
    assert pending[0]["content"] == "Persisted task"
