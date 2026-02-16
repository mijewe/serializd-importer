# Serializd Importer

Import your viewing history from multiple sources into [Serializd](https://serializd.com) with full episode tracking, custom watch dates, and automatic deduplication.

## Supported Sources

- **Netflix** - Import from ViewingActivity.csv export
- **Plex** - Import from Plex database
- **CSV** - Import from a custom .csv file

## Features

- ✅ **Profile filtering** - Import only your profile's viewing history
- ✅ **Show exclusion** - Filter out shows you didn't watch (ex-girlfriend's shows, etc.)
- ✅ **Automatic deduplication** - Handles "fell asleep and rewatched" scenarios
- ✅ **Source tagging** - Imports tagged by source (`#netfliximport`, `#pleximport`) for easy cleanup
- ✅ **Idempotent** - Safe to re-run; skips already-logged episodes
- ✅ **Dry-run mode** - Test before importing

## Prerequisites

- Python 3.10+
- Serializd account
- TMDB API key (free at [themoviedb.org](https://www.themoviedb.org/settings/api))
- **For Netflix:** Netflix account with viewing history export
- **For Plex:** Plex Media Server with viewing history

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd netflix-to-serialized  # Note: directory name will be updated in future release
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install package**
   ```bash
   pip install -e .

   # Also install serializd-py (API client)
   cd ../serializd-py
   pip install -e .
   cd ../netflix-to-serialized
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your credentials:
   ```env
   SERIALIZD_USERNAME=your_username
   SERIALIZD_PASSWORD=your_password
   TMDB_API_KEY=your_tmdb_api_key
   ```

## Getting Your Viewing History

### Netflix Viewing History

1. Go to https://www.netflix.com/account/getmyinfo
2. Hit "Submit Request"
4. Wait for email with download link (can take 24-48 hours)
5. Download and extract `ViewingActivity.csv`

### Plex Database

1. Open Plex
2. Download database

## How to use

```
serializd-importer <source> <path> [OPTIONS]

Sources:
  netflix    Import from Netflix ViewingActivity.csv
  plex       Import from Plex SQLite database

Options:
  --dry-run              Run without actually logging episodes
  --profile=NAME         Filter by profile name
  --exclude=SHOWS        Exclude shows (comma-separated)
  --exclude-file=PATH    Exclude shows from file (one per line)
  --tag=TAG              Custom import tag (default: source-specific)
```

### Options

#### --dry-run

Don't actually import anything; just report what would be imported. This is useful for verifying before the real import.

```bash
  serializd-importer netflix ViewingActivity.csv --dry-run
```

#### --profile

Both Netflix and Plex store viewing history for **all profiles** on your account. Use `--profile` to import only your viewing history.

```bash
  serializd-importer netflix ViewingActivity.csv --profile=Troy
```

#### --exclude-file

Exclude shows by including the path to a file with a list of shows to exclude. See .exclude-shows.example.

```bash
  serializd-importer netflix ViewingActivity.csv --exclude-file=.exclude-shows.txt
```

#### --tag

By default, logs will be tagged #netfliximport or #pleximport accordingly. But you can overwrite that with `--tag`. It's useful to tag the import just in case something goes wrong, so that entries can be deleted by tag.

```bash
  serializd-importer netflix ViewingActivity.csv --tag=#customtag
```

## Features Explained

### Deduplication

The importer automatically removes duplicate entries that are within 3 days of each other. This is to handle "fell asleep and rewatched" scenarios, but will still import legitimate rewatches.

### Performance

- **Import speed:** ~0.5-1 second per episode (rate limiting to avoid API throttling)

### Movies aren't imported

Movies are automatically filtered out during import (Serializd is TV shows only).

## Cleanup

If you need to remove imported episodes (eg botched import), you can run this script to delete entries by tag.

```bash
# Remove only Netflix imports (recommended)
PYTHONPATH=src python src/serializd_importer/_clear_all_reviews.py netfliximport

# Remove only Plex imports (recommended)
PYTHONPATH=src python src/serializd_importer/_clear_all_reviews.py pleximport

# Remove ALL Serializd diary entries (⚠️ dangerous!)
PYTHONPATH=src python src/serializd_importer/_clear_all_reviews.py
```

## Credits

This is completely unofficial and not affiliated with [Serializd](https://serializd.com) in any way.

Under the hood it uses a fork of the [serializd-py library](https://github.com/Velocidensity/serializd-py).
