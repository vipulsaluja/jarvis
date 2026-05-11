# Embeddings: sentence-transformers all-MiniLM-L6-v2 (384-dim, local, no API key).
# Model is downloaded once (~90MB) to ~/.cache/huggingface on first use.
import json
import sqlite3
import struct
import time
from pathlib import Path

import sqlite_vec
from sentence_transformers import SentenceTransformer

DB_PATH = Path(__file__).parent.parent.parent / "memory" / "episodic.db"

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _embed(text: str) -> bytes:
    vec = _get_model().encode(text, normalize_embeddings=True)
    return struct.pack(f"{len(vec)}f", *vec)


def _unpack(blob: bytes) -> list[float]:
    n = len(blob) // 4
    return list(struct.unpack(f"{n}f", blob))


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
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp    REAL    NOT NULL,
                summary      TEXT    NOT NULL,
                embedding    BLOB,
                entities     TEXT    NOT NULL DEFAULT '[]',
                importance   REAL    NOT NULL DEFAULT 0.5,
                access_count INTEGER NOT NULL DEFAULT 0
            );
        """)
        self._conn.commit()

    def add_episode(self, summary: str, entities: list[str], importance: float) -> int:
        embedding = _embed(summary)
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
