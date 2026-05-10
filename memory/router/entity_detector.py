import json
import re
from pathlib import Path

_SEMANTIC_DIR = Path(__file__).parent.parent / "semantic"
_MIN_NAME_LEN = 3


def _index_directory(directory: Path) -> dict[str, Path]:
    """Return {lowercase_name: file_path} for all entity JSON files in a directory."""
    index: dict[str, Path] = {}
    if not directory.exists():
        return index
    for path in directory.glob("*.json"):
        try:
            data = json.loads(path.read_text())
            name = data.get("name", path.stem)
            index[name.lower()] = path
            stem = path.stem.lower()
            if stem not in index:
                index[stem] = path
        except (json.JSONDecodeError, OSError):
            index[path.stem.lower()] = path
    return index


def detect_entities(query: str) -> list[Path]:
    """Return entity file paths whose names appear as whole words in the query."""
    query_lower = query.lower()
    results: list[Path] = []
    seen: set[Path] = set()

    for subdir in ("people", "projects"):
        for name, path in _index_directory(_SEMANTIC_DIR / subdir).items():
            if len(name) < _MIN_NAME_LEN:
                continue
            if path in seen:
                continue
            pattern = r"\b" + re.escape(name) + r"\b"
            if re.search(pattern, query_lower):
                results.append(path)
                seen.add(path)

    return results
