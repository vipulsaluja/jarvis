"""Tests for pipeline.date_parser.resolve_due_date."""
from __future__ import annotations

import subprocess
from unittest.mock import patch, MagicMock

import pytest

from pipeline.date_parser import resolve_due_date, _DATE_RE


# ---------------------------------------------------------------------------
# _DATE_RE sanity
# ---------------------------------------------------------------------------

def test_date_re_matches_valid():
    assert _DATE_RE.match("2026-05-15")
    assert _DATE_RE.match("2026-12-31")


def test_date_re_rejects_invalid():
    assert not _DATE_RE.match("05-15-2026")
    assert not _DATE_RE.match("2026-5-15")
    assert not _DATE_RE.match("tomorrow")


# ---------------------------------------------------------------------------
# None / empty input — no claude call needed
# ---------------------------------------------------------------------------

def test_none_hint_returns_none():
    assert resolve_due_date(None, "2026-05-11") is None


def test_empty_string_returns_none():
    assert resolve_due_date("", "2026-05-11") is None


def test_whitespace_only_returns_none():
    assert resolve_due_date("   ", "2026-05-11") is None


# ---------------------------------------------------------------------------
# Mocked claude responses
# ---------------------------------------------------------------------------

def _mock_run(stdout: str, returncode: int = 0):
    m = MagicMock()
    m.returncode = returncode
    m.stdout = stdout
    m.stderr = ""
    return m


def test_clean_date_returned_as_is():
    with patch("subprocess.run", return_value=_mock_run("2026-05-15\n")):
        assert resolve_due_date("next Friday", "2026-05-11") == "2026-05-15"


def test_none_response_returns_none():
    with patch("subprocess.run", return_value=_mock_run("none")):
        assert resolve_due_date("eventually", "2026-05-11") is None


def test_quoted_date_is_extracted():
    with patch("subprocess.run", return_value=_mock_run('"2026-05-15"')):
        assert resolve_due_date("next Friday", "2026-05-11") == "2026-05-15"


def test_date_embedded_in_text_is_extracted():
    with patch("subprocess.run", return_value=_mock_run("The date is 2026-05-15.")):
        assert resolve_due_date("next Friday", "2026-05-11") == "2026-05-15"


def test_claude_failure_returns_none():
    with patch("subprocess.run", return_value=_mock_run("", returncode=1)):
        assert resolve_due_date("tomorrow", "2026-05-11") is None


def test_empty_claude_output_returns_none():
    with patch("subprocess.run", return_value=_mock_run("")):
        assert resolve_due_date("tomorrow", "2026-05-11") is None


def test_unparseable_output_returns_none():
    with patch("subprocess.run", return_value=_mock_run("I cannot determine a specific date")):
        assert resolve_due_date("soon", "2026-05-11") is None


# ---------------------------------------------------------------------------
# Live integration test (skipped if claude unavailable)
# ---------------------------------------------------------------------------

def _claude_available() -> bool:
    try:
        r = subprocess.run(["claude", "--version"], capture_output=True, timeout=5)
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


@pytest.mark.skipif(not _claude_available(), reason="claude CLI not available")
def test_live_next_friday_resolves():
    result = resolve_due_date("next Friday", "2026-05-11")
    assert result == "2026-05-15", f"expected 2026-05-15, got {result}"


@pytest.mark.skipif(not _claude_available(), reason="claude CLI not available")
def test_live_tomorrow_resolves():
    result = resolve_due_date("tomorrow", "2026-05-11")
    assert result == "2026-05-12", f"expected 2026-05-12, got {result}"


@pytest.mark.skipif(not _claude_available(), reason="claude CLI not available")
def test_live_none_hint_skips_claude():
    # None should short-circuit before any subprocess call
    with patch("subprocess.run", side_effect=AssertionError("should not call claude")):
        assert resolve_due_date(None, "2026-05-11") is None
