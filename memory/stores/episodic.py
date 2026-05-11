# Embeddings: sentence-transformers all-MiniLM-L6-v2 (384-dim, local, no API key).
# Model is downloaded once (~90MB) to ~/.cache/huggingface on first use.
import json
import sqlite3
import struct
import time
from pathlib import Path
from typing import Optional

try:
    import sqlite_vec
    _SQLITE_VEC_AVAILABLE = True
except ImportError:
    _SQLITE_VEC_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    _ST_AVAILABLE = True
except ImportError:
    _ST_AVAILABLE = False

DB_PATH = Path(__file__).parent.parent.parent / "memory" / "episodic.db"

_model: Optional["SentenceTransformer"] = None


def _get_model() -> "SentenceTransformer":
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _embed(text: str) -> Optional[bytes]:
    if not _ST_AVAILABLE:
        return None
    vec = _get_model().encode(text, normalize_embeddings=True)
    return struct.pack(f"{len(vec)}f", *vec)


def _unpack(blob: bytes) -> list:
    n = len(blob) // 4
    return list(struct.unpack(f"{n}f", blob))


class EpisodicStore:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._vec_enabled = False
        if _SQLITE_VEC_AVAILABLE and hasattr(self._conn, "enable_load_extension"):
            self._conn.enable_load_extension(True)
            sqlite_vec.load(self._conn)
            self._conn.enable_load_extension(False)
            self._vec_enabled = True
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

    def add_episode(self, summary: str, entities: list, importance: float) -> int:
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

    def search(self, query: str, top_k: int = 3) -> list:
        if not _ST_AVAILABLE:
            return []
        query_vec = _embed(query)
        if query_vec is None:
            return []
        q = _unpack(query_vec)
        q_norm = sum(x * x for x in q) ** 0.5

        rows = self._conn.execute(
            "SELECT id, timestamp, summary, embedding, entities, importance FROM episodes WHERE embedding IS NOT NULL"
        ).fetchall()
        if not rows:
            return []

        now = time.time()
        oldest = min(r[1] for r in rows)
        age_range = max(now - oldest, 1.0)

        scored = []
        for row_id, ts, summary, blob, entities_json, importance in rows:
            v = _unpack(blob)
            dot = sum(a * b for a, b in zip(q, v))
            v_norm = sum(x * x for x in v) ** 0.5
            cosine = dot / (q_norm * v_norm) if q_norm and v_norm else 0.0
            recency = (ts - oldest) / age_range  # 0 (oldest) … 1 (newest)
            score = cosine * (1 + 0.1 * recency)
            scored.append((score, row_id, ts, summary, entities_json, importance))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:top_k]

        ids = [r[1] for r in top]
        self._conn.execute(
            f"UPDATE episodes SET access_count = access_count + 1 WHERE id IN ({','.join('?' * len(ids))})",
            ids,
        )
        self._conn.commit()

        return [
            {"summary": r[3], "entities": json.loads(r[4]), "importance": r[5], "timestamp": r[2]}
            for r in top
        ]

    def get_all(self) -> list:
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


def score_importance(summary: str) -> float:
    """Score a summary's importance in [0.0, 1.0].

    High (0.8): decided, agreed, will, committed, promised, need to, must, should,
                concluded, resolved, plan to, going to, scheduled
    Low (0.2):  chatted, mentioned, asked about, talked about, discussed briefly,
                said hi, caught up, small talk, greeted, inquired, checked in,
                asked how, exchanged, how are you, how is, doing well
    Default: 0.3 — neutral content defaults low; saves only if clearly significant.
    Skip threshold in writer: <= 0.3 (so LOW=0.2 and DEFAULT=0.3 are both skipped).
    """
    text = summary.lower()
    HIGH = [
        "decided", "agreed", "will ", "committed", "promised",
        "need to", "must ", "should ", "concluded", "resolved",
        "plan to", "going to", "scheduled",
    ]
    LOW = [
        "chatted", "mentioned", "asked about", "talked about",
        "discussed briefly", "said hi", "caught up", "small talk",
        "greeted", "inquired", "checked in", "asked how",
        "exchanged", "how are you", "how is", "doing well",
    ]
    if any(kw in text for kw in HIGH):
        return 0.8
    if any(kw in text for kw in LOW):
        return 0.2
    return 0.3
