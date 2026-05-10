import json
import sqlite3
import time
from pathlib import Path

import sqlite_vec

DB_PATH = Path(__file__).parent.parent.parent / "memory" / "episodic.db"


class EpisodicStore:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.enable_load_extension(True)
        sqlite_vec.load(self._conn)
        self._conn.enable_load_extension(False)
        self._init_schema()

    def _init_schema(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS episodes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   REAL    NOT NULL,
                summary     TEXT    NOT NULL,
                embedding   BLOB,
                entities    TEXT    NOT NULL DEFAULT '[]',
                importance  REAL    NOT NULL DEFAULT 0.5,
                access_count INTEGER NOT NULL DEFAULT 0
            );
        """)
        self._conn.commit()

    def add_episode(self, summary: str, entities: list[str], importance: float, embedding: bytes | None = None) -> int:
        cur = self._conn.execute(
            """
            INSERT INTO episodes (timestamp, summary, embedding, entities, importance)
            VALUES (?, ?, ?, ?, ?)
            """,
            (time.time(), summary, embedding, json.dumps(entities), importance),
        )
        self._conn.commit()
        return cur.lastrowid

    def get_all(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT id, timestamp, summary, entities, importance, access_count FROM episodes ORDER BY timestamp DESC"
        ).fetchall()
        return [
            {"id": r[0], "timestamp": r[1], "summary": r[2],
             "entities": json.loads(r[3]), "importance": r[4], "access_count": r[5]}
            for r in rows
        ]

    def close(self):
        self._conn.close()
