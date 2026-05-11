"""UAT for M4 T2 (embeddings) and T3 (cosine search + recency boost)."""
import os
import time
import tempfile
import pathlib

from memory.stores.episodic import EpisodicStore, _unpack

db = pathlib.Path(tempfile.mktemp(suffix=".db"))
s = EpisodicStore(db_path=db)

# --- T2: embeddings are stored as 384-dim BLOBs ---
rid = s.add_episode("Decided to use PostgreSQL for auth.", ["PostgreSQL"], 0.8)
blob = s._conn.execute("SELECT embedding FROM episodes WHERE id=?", (rid,)).fetchone()[0]
assert blob is not None, "embedding is None — sentence-transformers not working"
vec = _unpack(blob)
assert len(vec) == 384, f"expected 384 dims, got {len(vec)}"
print("T2 embeddings: OK")

# --- T3a: semantic ranking ---
s.add_episode("Agreed Jarvis should respond in a concise tone.", ["Jarvis"], 0.7)
s.add_episode("Chatted briefly about the weekend.", [], 0.1)
s.add_episode("Committed to finishing M4 episodic memory this week.", ["M4"], 0.9)

results = s.search("What database are we using for authentication?", top_k=2)
assert len(results) == 2
assert "PostgreSQL" in results[0]["entities"], f"top result: {results[0]['summary']}"
print("T3a semantic ranking: OK —", results[0]["summary"])

# --- T3b: recency boost (newer episode of equal relevance ranks higher) ---
s.add_episode("We agreed to use SQLite for local storage.", ["SQLite"], 0.7)
time.sleep(0.1)
s.add_episode("We confirmed SQLite is the right choice for local storage.", ["SQLite"], 0.7)

r = s.search("local storage decision", top_k=2)
assert "confirmed" in r[0]["summary"].lower(), f"recency boost failed; top: {r[0]['summary']}"
print("T3b recency boost: OK —", r[0]["summary"])

# --- T3c: access_count increments ---
before = {
    row[0]: row[1]
    for row in s._conn.execute("SELECT id, access_count FROM episodes").fetchall()
}
returned_ids = set()
for hit in results:
    matched = s._conn.execute(
        "SELECT id FROM episodes WHERE summary=?", (hit["summary"],)
    ).fetchone()
    if matched:
        returned_ids.add(matched[0])

s.search("database", top_k=2)
after = {
    row[0]: row[1]
    for row in s._conn.execute("SELECT id, access_count FROM episodes").fetchall()
}
incremented = [eid for eid in after if after[eid] > before.get(eid, 0)]
assert len(incremented) == 2, f"expected 2 access_count increments, got {incremented}"
print("T3c access_count: OK")

# --- T3d: null-embedding rows are skipped without crashing ---
s._conn.execute(
    "INSERT INTO episodes (timestamp, summary, entities, importance) VALUES (0, 'old row no embedding', '[]', 0.5)"
)
s._conn.commit()
results2 = s.search("anything", top_k=5)
summaries = [r["summary"] for r in results2]
assert "old row no embedding" not in summaries, "null-embedding row leaked into results"
print("T3d null-embedding skip: OK")

s.close()
os.unlink(db)
print("\nAll UAT checks passed.")
