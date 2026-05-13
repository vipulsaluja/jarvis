from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "memory" / "prospective.db"


class ProspectiveStore:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS prospective (
                id                TEXT PRIMARY KEY,
                content           TEXT NOT NULL,
                due_date          TEXT,
                trigger_condition TEXT,
                status            TEXT NOT NULL DEFAULT 'pending',
                source_episode    TEXT,
                created_at        TEXT NOT NULL
            );
        """)
        self._conn.commit()

    def add(
        self,
        content: str,
        due_date: str | None = None,
        trigger_condition: str | None = None,
        source_episode: str | None = None,
    ) -> str:
        item_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self._conn.execute(
            """
            INSERT INTO prospective (id, content, due_date, trigger_condition, status, source_episode, created_at)
            VALUES (?, ?, ?, ?, 'pending', ?, ?)
            """,
            (item_id, content, due_date, trigger_condition, source_episode, now),
        )
        self._conn.commit()
        return item_id

    def get_due(self, as_of: str) -> list[dict]:
        rows = self._conn.execute(
            """
            SELECT * FROM prospective
            WHERE status = 'pending'
              AND due_date IS NOT NULL
              AND due_date <= ?
            ORDER BY due_date ASC
            """,
            (as_of,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_condition_triggered(self, keywords: list[str]) -> list[dict]:
        if not keywords:
            return []
        rows = self._conn.execute(
            "SELECT * FROM prospective WHERE status = 'pending' AND trigger_condition IS NOT NULL"
        ).fetchall()
        matched = []
        kw_lower = [k.lower() for k in keywords]
        for row in rows:
            condition = row["trigger_condition"].lower()
            if any(kw in condition for kw in kw_lower):
                matched.append(dict(row))
        return matched

    def complete(self, item_id: str) -> None:
        self._conn.execute(
            "UPDATE prospective SET status = 'done' WHERE id = ?",
            (item_id,),
        )
        self._conn.commit()

    def list_pending(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM prospective WHERE status = 'pending' ORDER BY due_date ASC NULLS LAST"
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        self._conn.close()
