# Semantic Memory — Entity Schema

## Directory Layout

```
memory/semantic/
  _schema.md           ← this file
  hot.json             ← always-loaded key facts (see M2)
  preferences.json     ← cross-cutting user preferences
  people/
    {name}.json        ← one file per person
  projects/
    {slug}.json        ← one file per project
```

## Entity File Format

```json
{
  "facts": {
    "{key}": {
      "value": "<string or structured value>",
      "confidence": 0.9,
      "updated": "2026-05-10",
      "source": "user"
    }
  }
}
```

### Field definitions

| Field | Type | Description |
|-------|------|-------------|
| `key` | string | Snake-case fact identifier, e.g. `comms_style`, `role`, `timezone` |
| `value` | any | The fact's value — string, number, list, or object |
| `confidence` | float 0.0–1.0 | How certain we are this is still true |
| `updated` | ISO date | Last time this fact was written or confirmed |
| `source` | string | `"user"` (explicit), `"inferred"` (extracted from conversation), `"agent"` (Jarvis-generated) |

## Confidence Thresholds

| Confidence | Write behavior |
|------------|---------------|
| < 0.7 | New value overwrites silently |
| >= 0.7 | Existing value differs → print old/new and prompt user to confirm before overwriting |

## Naming Conventions

- **People:** lowercase first name or handle, e.g. `priya.json`, `alex.json`
- **Projects:** lowercase slug, e.g. `jarvis.json`, `auth-refactor.json`
- **Preference keys:** descriptive snake_case, e.g. `response_length`, `notification_style`
