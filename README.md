# Serializd Importer

Import your viewing history from multiple sources into [Serializd](https://serializd.com) with full episode tracking, custom watch dates, and automatic deduplication.

## Supported Sources

- **Netflix** — Import from `ViewingActivity.csv` export
- **Plex** — Import from Plex database
- **CSV** — Import from a custom `.csv` file

## Features

- **Profile filtering** — Import only your profile's viewing history
- **Show exclusion** — Filter out shows you don't want imported
- **Automatic deduplication** — Handles "fell asleep and rewatched" scenarios
- **Source tagging** — Imports tagged by source (`#netfliximport`, `#pleximport`) for easy cleanup
- **Idempotent** — Safe to re-run; skips already-logged episodes
- **Dry-run mode** — Preview what will be imported before committing
- **Movies filtered** — Movies are automatically excluded (Serializd is TV-only)

## Prerequisites

- Python 3.10+
- Serializd account
- TMDB API key (free at [themoviedb.org](https://www.themoviedb.org/settings/api))
- **Netflix:** Viewing history export (see [below](#netflix))
- **Plex:** Plex Media Server database

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd netflix-to-serialized
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install packages**
   ```bash
   pip install -e .

   # Also install the serializd-py API client
   cd ../serializd-py && pip install -e . && cd -
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your credentials:
   ```env
   SERIALIZD_USERNAME=your_username
   SERIALIZD_PASSWORD=your_password
   TMDB_API_KEY=your_tmdb_api_key
   ```

## Getting Your Viewing History

### Netflix

1. Go to https://www.netflix.com/account/getmyinfo
2. Submit the data request
3. Wait for the email with a download link (can take 24–48 hours)
4. Download and extract `ViewingActivity.csv`

### Plex

1. Open Plex Media Server
2. Download the database file

## Usage

```
serializd-importer <source> <path> [OPTIONS]

Sources:
  netflix    Import from Netflix ViewingActivity.csv
  plex       Import from Plex SQLite database

Options:
  --dry-run              Preview without logging episodes
  --profile=NAME         Filter by profile name
  --exclude=SHOWS        Exclude shows (comma-separated)
  --exclude-file=PATH    Exclude shows listed in a file (one per line)
  --tag=TAG              Custom import tag (default: source-specific)
```

### `--dry-run`

Preview what would be imported without making any changes.

```bash
serializd-importer netflix ViewingActivity.csv --dry-run
```

### `--profile`

Netflix and Plex store viewing history for all profiles on an account. Use `--profile` to import only yours.

```bash
serializd-importer netflix ViewingActivity.csv --profile=Troy
```

### `--exclude-file`

Exclude shows listed in a file (one per line). See `.exclude-shows.example` for the format.

```bash
serializd-importer netflix ViewingActivity.csv --exclude-file=.exclude-shows.txt
```

### `--tag`

Logs are tagged `#netfliximport` or `#pleximport` by default. Override with `--tag`. Tagging is useful for bulk cleanup if something goes wrong.

```bash
serializd-importer netflix ViewingActivity.csv --tag=#customtag
```

## How It Works

### Deduplication

Duplicate entries within 3 days of each other are automatically merged. This handles "fell asleep and rewatched" scenarios while still preserving legitimate rewatches.

### Performance

Import speed is roughly 0.5–1 second per episode due to rate limiting.

## Cleanup

Remove imported episodes by tag if something goes wrong:

```bash
# Remove Netflix imports
PYTHONPATH=src python src/serializd_importer/_clear_all_reviews.py netfliximport

# Remove Plex imports
PYTHONPATH=src python src/serializd_importer/_clear_all_reviews.py pleximport

# Remove ALL diary entries (dangerous!)
PYTHONPATH=src python src/serializd_importer/_clear_all_reviews.py
```

## Credits

Completely unofficial and not affiliated with [Serializd](https://serializd.com).

Uses a fork of the [serializd-py library](https://github.com/Velocidensity/serializd-py) under the hood.

Shamelessly vibecoded.
