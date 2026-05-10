# Semantic Entity Schema

Each entity file lives in `memory/semantic/people/<name>.json` or `memory/semantic/projects/<name>.json`.

## Structure

```json
{
  "_schema": "documentation comment — strip before injecting into context",
  "name": "Display Name",
  "type": "person | project",
  "facts": {
    "fact_key": {
      "value": "The fact as a plain sentence or short phrase.",
      "confidence": 0.9,
      "updated": "2026-05-10T00:00:00",
      "source": "user-cli | auto | imported"
    }
  }
}
```

## Fields

- **name** — display name used for matching and context injection
- **type** — `person` or `project`
- **facts** — dict of fact_key → fact object
  - **value** — the fact itself
  - **confidence** — float 0.0–1.0; facts with confidence ≥ 0.7 require confirmation before overwrite
  - **updated** — ISO 8601 timestamp of last write
  - **source** — where the fact came from

## preferences.json

`memory/semantic/preferences.json` follows the same facts schema but has no `name` or `type` field — it stores general user preferences not tied to a specific entity.

## Conflict Resolution

- confidence < 0.7 → overwrite silently, log to stderr
- confidence ≥ 0.7 → prompt user before overwriting
