# Migration Guide: v0.1.0 → v0.2.0

This guide helps you migrate from the Netflix-only version (v0.1.0) to the multi-source importer (v0.2.0).

## What Changed

### Package Rename

- **Old:** `netflix-to-serializd`
- **New:** `serializd-importer`

### New CLI Interface

The package now supports multiple sources (Netflix, Plex) through a unified CLI.

**Old command:**
```bash
PYTHONPATH=src python -m netflix_to_serializd.importer ViewingActivity.csv --profile=Michael
```

**New command:**
```bash
serializd-importer netflix ViewingActivity.csv --profile=Michael
```

### Project Structure Changes

```
OLD:
src/netflix_to_serializd/
├── importer.py
├── episode_logger.py
├── netflix.py
├── title_parser.py
├── tmdb_client.py
└── serializd_adapter.py

NEW:
src/serializd_importer/
├── cli.py
├── common/
│   ├── importer.py
│   ├── episode_logger.py
│   ├── tmdb_client.py
│   └── serializd_adapter.py
└── sources/
    ├── base.py
    ├── netflix.py
    └── plex.py
```

## Migration Steps

### 1. Update Your Installation

```bash
# Activate your virtual environment
source .venv/bin/activate

# Reinstall the package
pip install -e .
```

The new CLI command `serializd-importer` will be installed automatically.

### 2. Update Your Commands

Replace your old commands with the new CLI format:

**Dry-run:**
```bash
# Old
PYTHONPATH=src python -m netflix_to_serializd.importer ViewingActivity.csv --dry-run

# New
serializd-importer netflix ViewingActivity.csv --dry-run
```

**With profile filtering:**
```bash
# Old
PYTHONPATH=src python -m netflix_to_serializd.importer ViewingActivity.csv --profile=Michael

# New
serializd-importer netflix ViewingActivity.csv --profile=Michael
```

**With exclude file:**
```bash
# Old
PYTHONPATH=src python -m netflix_to_serializd.importer ViewingActivity.csv \
  --profile=Michael \
  --exclude-file=.exclude-shows.txt

# New
serializd-importer netflix ViewingActivity.csv \
  --profile=Michael \
  --exclude-file=.exclude-shows.txt
```

### 3. Update TMDB Overrides

If you added custom TMDB ID overrides, they've moved:

**Old location:** `src/netflix_to_serializd/title_parser.py`

**New location:** `src/serializd_importer/sources/netflix.py`

The `TMDB_ID_OVERRIDES` dictionary is in the same format:
```python
TMDB_ID_OVERRIDES = {
    "The Office (U.K.)": 2996,
    "The Office (U.S.)": 2316,
    # Your custom overrides...
}
```

### 4. Update Cleanup Scripts

If you have scripts that call the cleanup utility:

```bash
# Old
PYTHONPATH=src python src/netflix_to_serializd/_clear_all_reviews.py netfliximport

# New
PYTHONPATH=src python src/serializd_importer/_clear_all_reviews.py netfliximport
```

### 5. Update CSV Filter Scripts (if used)

If you use the CSV filtering utility:

```bash
# Old
PYTHONPATH=src python src/netflix_to_serializd/_filter_recent_csv.py \
  ViewingActivity.csv ViewingActivity_recent.csv 30

# New
PYTHONPATH=src python src/serializd_importer/_filter_recent_csv.py \
  ViewingActivity.csv ViewingActivity_recent.csv 30
```

## New Features in v0.2.0

### Multi-Source Support

You can now import from:
- **Netflix** (CSV export)
- **Plex** (SQLite database)

```bash
# Netflix
serializd-importer netflix ViewingActivity.csv --profile=Michael

# Plex
serializd-importer plex plex.db --profile=mwest56
```

### Custom Tags

Override the default import tag:

```bash
serializd-importer netflix ViewingActivity.csv --tag=#netflix2024
```

### Source-Specific Tags

Each source has its own default tag:
- Netflix: `#netfliximport`
- Plex: `#pleximport`

This makes it easier to identify and clean up imports by source.

## Compatibility

### Already-Imported Episodes

Episodes imported with v0.1.0 will **NOT** be re-imported. The importer checks for existing episodes and skips them (idempotency).

You can safely run the new version on the same data.

### Tags

Existing Netflix imports have the `#netfliximport` tag. This tag is unchanged in v0.2.0, so your existing imports remain identifiable.

## Troubleshooting

### "Command not found: serializd-importer"

Make sure you reinstalled the package after pulling the latest changes:

```bash
pip install -e .
```

If that doesn't work, try:

```bash
pip uninstall serializd-importer
pip install -e .
```

### "No module named 'netflix_to_serializd'"

This means you're trying to use the old command format. Update to the new CLI:

```bash
serializd-importer netflix ViewingActivity.csv
```

### Old scripts still reference old paths

Update all references from:
- `netflix_to_serializd` → `serializd_importer`
- `src/netflix_to_serializd/` → `src/serializd_importer/`

## Questions?

For issues or questions about migration, please open an issue on GitHub.
