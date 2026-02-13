# Serializd Importer

Import your viewing history from multiple sources into [Serializd](https://serializd.com) with full episode tracking, custom watch dates, and automatic deduplication.

## Supported Sources

- 🎬 **Netflix** - Import from ViewingActivity.csv export
- 📺 **Plex** - Import from Plex SQLite database

## Features

- ✅ **Multi-source support** - Import from Netflix, Plex, and more
- ✅ **Complete viewing history** - Import all your TV show viewing history
- ✅ **Chronological ordering** - Episodes appear in watch order (oldest to newest by default)
- ✅ **Profile filtering** - Import only your profile's viewing history
- ✅ **Show exclusion** - Filter out shows you didn't watch (ex-girlfriend's shows, etc.)
- ✅ **Automatic deduplication** - Handles "fell asleep and rewatched" scenarios
- ✅ **TMDB integration** - Automatic show lookup with manual override support
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

1. Go to [Netflix Account Settings](https://www.netflix.com/account)
2. Navigate to **Profile & Parental Controls** → **Viewing Activity**
3. Scroll to bottom and click **Download all**
4. Wait for email with download link (can take 24-48 hours)
5. Download and extract `ViewingActivity.csv`

### Plex Database

The Plex database location varies by operating system:

**macOS:**
```bash
~/Library/Application Support/Plex Media Server/Plug-in Support/Databases/com.plexapp.plugins.library.db
```

**Linux:**
```bash
/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Plug-in Support/Databases/com.plexapp.plugins.library.db
```

**Windows:**
```
%LOCALAPPDATA%\Plex Media Server\Plug-in Support\Databases\com.plexapp.plugins.library.db
```

**Recommended:** Copy the database file to your working directory before importing (don't modify the live database).

## Usage

### Quick Start

```bash
# Activate virtual environment
source .venv/bin/activate

# Netflix: Test with dry-run (recommended first step)
serializd-importer netflix path/to/ViewingActivity.csv \
  --profile=YourName \
  --dry-run

# Netflix: Import for real
serializd-importer netflix path/to/ViewingActivity.csv \
  --profile=YourName

# Plex: Test with dry-run
serializd-importer plex path/to/plex.db \
  --profile=username \
  --dry-run

# Plex: Import for real
serializd-importer plex path/to/plex.db \
  --profile=username
```

### Command-Line Interface

```
serializd-importer <source> <path> [OPTIONS]

Sources:
  netflix    Import from Netflix ViewingActivity.csv
  plex       Import from Plex SQLite database

Options:
  --dry-run              Run without actually logging episodes
  --order=oldest         Import oldest to newest (chronological, default)
  --order=newest         Import newest to oldest (reverse chronological)
  --profile=NAME         Filter by profile name
  --exclude=SHOWS        Exclude shows (comma-separated)
  --exclude-file=PATH    Exclude shows from file (one per line)
  --tag=TAG              Custom import tag (default: source-specific)
```

### Netflix Examples

**Dry-run test (recommended first):**
```bash
serializd-importer netflix ViewingActivity.csv \
  --profile=Michael \
  --dry-run
```

**Import with exclusions:**
```bash
serializd-importer netflix ViewingActivity.csv \
  --profile=Michael \
  --exclude="Schitt's Creek,Parks and Recreation"
```

**Import using exclude file:**
```bash
# Create exclude file
cat > .exclude-shows.txt << 'EOF'
# Shows I didn't watch
Schitt's Creek
Parks and Recreation
The Good Place
EOF

# Import
serializd-importer netflix ViewingActivity.csv \
  --profile=Michael \
  --exclude-file=.exclude-shows.txt
```

**Import with custom tag:**
```bash
serializd-importer netflix ViewingActivity.csv \
  --profile=Michael \
  --tag=#netflix2024
```

### Plex Examples

**Dry-run test (recommended first):**
```bash
serializd-importer plex plex.db \
  --profile=mwest56 \
  --dry-run
```

**Import with exclusions:**
```bash
serializd-importer plex plex.db \
  --profile=mwest56 \
  --exclude-file=.exclude-shows.txt
```

**Import newest first (reverse chronological):**
```bash
serializd-importer plex plex.db \
  --profile=mwest56 \
  --order=newest
```

**Import with custom tag:**
```bash
serializd-importer plex plex.db \
  --profile=mwest56 \
  --tag=#plex2024
```

## Features Explained

### Profile Filtering

Both Netflix and Plex store viewing history for **all profiles** on your account. Use `--profile` to import only your viewing history.

**Netflix:**
```bash
serializd-importer netflix ViewingActivity.csv --profile=Michael
```

To see which profiles exist in your Netflix CSV:
```bash
cut -d',' -f3 ViewingActivity.csv | tail -n +2 | sort -u
```

**Plex:**
```bash
serializd-importer plex plex.db --profile=mwest56
```

To see which profiles exist in your Plex database:
```bash
sqlite3 plex.db "SELECT name FROM accounts;"
```

### Show Exclusion

Exclude shows you didn't watch (e.g., watched by ex-girlfriend, family members, etc.):

**Method 1: Command-line flag**
```bash
--exclude="Show Name 1,Show Name 2,Show Name 3"
```

**Method 2: Exclude file** (recommended for many shows)
```bash
# .exclude-shows.txt
# One show per line, comments supported

Schitt's Creek
Parks and Recreation

# Shows watched by ex-girlfriend
The Good Place
Gilmore Girls
```

Then: `--exclude-file=.exclude-shows.txt`

You can combine both methods - shows from both sources will be excluded.

### Import Ordering

**Default (chronological):** Episodes appear oldest-to-newest
```bash
--order=oldest  # or omit (default)
```

**Reverse chronological:** Episodes appear newest-to-oldest
```bash
--order=newest
```

### Deduplication

Automatically handles "fell asleep and rewatched" scenarios:

- Watches same episode multiple times within 3 days → keeps latest viewing
- Legitimate re-watches (months apart) → keeps both viewings
- Configurable window (default: 3 days)

### Tagging

Imported episodes are tagged by source:
- Netflix: `#netfliximport`
- Plex: `#pleximport`

This allows you to:

- Identify which source imported each episode
- Easily clean up if something goes wrong
- Filter imported episodes from manual entries
- Use custom tags with `--tag=#yourtag`

### TMDB Show Matching

Shows are automatically looked up in TMDB by name. If a show doesn't match correctly, you can add a manual override for Netflix imports:

Edit `src/serializd_importer/sources/netflix.py`:
```python
TMDB_ID_OVERRIDES = {
    "The Office (U.K.)": 2996,  # The Office UK (2001)
    "The Office (U.S.)": 2316,  # The Office US (2005)
    "Your Show Name": 12345,    # Add your override here
}
```

Find TMDB IDs at [themoviedb.org](https://www.themoviedb.org).

**Note:** Plex lookups rely on show name matching. If Plex show names don't match TMDB, you may need to correct the show names in Plex first.

## Cleanup

If you need to remove imported episodes (e.g., botched import):

```bash
# Remove only Netflix imports (recommended)
PYTHONPATH=src python src/serializd_importer/_clear_all_reviews.py netfliximport

# Remove only Plex imports (recommended)
PYTHONPATH=src python src/serializd_importer/_clear_all_reviews.py pleximport

# Remove ALL Serializd diary entries (⚠️ dangerous!)
PYTHONPATH=src python src/serializd_importer/_clear_all_reviews.py
```

## Staged Rollout (Recommended)

For safety, test with dry-run before full import:

**Step 1: Dry-run test**
```bash
# Netflix
serializd-importer netflix ViewingActivity.csv \
  --profile=Michael \
  --exclude-file=.exclude-shows.txt \
  --dry-run

# Plex
serializd-importer plex plex.db \
  --profile=mwest56 \
  --exclude-file=.exclude-shows.txt \
  --dry-run
```

**Step 2: Review dry-run output**
- Check for TMDB lookup failures
- Verify episode counts look reasonable
- Confirm profile filtering worked

**Step 3: Run real import**
```bash
# Netflix
serializd-importer netflix ViewingActivity.csv \
  --profile=Michael \
  --exclude-file=.exclude-shows.txt

# Plex
serializd-importer plex plex.db \
  --profile=mwest56 \
  --exclude-file=.exclude-shows.txt
```

**Step 4: Verify in Serializd**
- Check episodes appear correctly
- Verify dates match source
- Confirm tags are present (`#netfliximport` or `#pleximport`)

**Step 5: If issues, rollback**
```bash
# Netflix
PYTHONPATH=src python src/serializd_importer/_clear_all_reviews.py netfliximport

# Plex
PYTHONPATH=src python src/serializd_importer/_clear_all_reviews.py pleximport
```

## Performance

- **Import speed:** ~0.5-1 second per episode (rate limiting to avoid API throttling)
- **Typical Netflix import:** 2,000-3,000 episodes = 20-50 minutes
- **Typical Plex import:** Varies by library size
- **First run:** Slower due to TMDB lookups; subsequent runs faster (idempotency)

## Troubleshooting

### "TMDB not found" errors

Some shows may not match TMDB's database. Solutions:

1. Check dry-run output for failed matches
2. For Netflix: Add manual overrides in `src/serializd_importer/sources/netflix.py` (see TMDB Show Matching above)
3. For Plex: Verify show names in Plex match TMDB naming conventions
4. Re-run import (already-logged episodes will be skipped)

### Duplicate episodes

If you see unexpected duplicates:

- **Same episode, different dates:** This is correct - treated as re-watch
- **Same episode, same date:** Should be auto-skipped (idempotency check)
- If issues persist, check Serializd web UI for existing entries

### Rate limiting

If you get rate limit errors:

- Default sleep is 0.5s per episode
- Edit `src/serializd_importer/common/importer.py` line 212 to increase: `time.sleep(1.0)`

### Environment issues

```bash
# Verify .env is loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('SERIALIZD_USERNAME'))"

# Should print your username, not None
```

## Project Structure

```
serializd-importer/
├── src/serializd_importer/
│   ├── cli.py                   # Multi-source CLI dispatcher
│   ├── common/
│   │   ├── importer.py          # Generic import logic
│   │   ├── episode_logger.py   # Serializd episode logging
│   │   ├── tmdb_client.py       # TMDB API client
│   │   └── serializd_adapter.py # Serializd client factory
│   ├── sources/
│   │   ├── base.py              # Abstract source interface
│   │   ├── netflix.py           # Netflix CSV parser
│   │   └── plex.py              # Plex SQLite parser
│   ├── _filter_recent_csv.py   # CSV filtering utility (Netflix)
│   └── _clear_all_reviews.py   # Cleanup utility
├── .env.example                 # Environment template
├── .exclude-shows.example       # Exclude file template
├── pyproject.toml               # Package configuration
└── README.md                    # This file
```

## Edge Cases & Known Issues

### Multiple viewings on different dates

If you watched the same episode on different dates (intentional re-watch), both entries will be logged. This is by design.

To change this behavior (skip any episode that exists, regardless of date), modify `src/serializd_importer/common/episode_logger.py` around line 109-111:

```python
else:
    # Episode exists (any date) - skip
    return True
```

### Movies

Movies are automatically filtered out during import (Serializd is TV shows only).

### Season/Episode numbering

If Netflix and TMDB use different numbering schemes:
- Check dry-run output
- Verify in Serializd after import
- Add manual corrections if needed

## Contributing

Contributions welcome! Please:

1. Test changes with `--dry-run` first
2. Update README if adding features
3. Follow existing code style
4. Add examples for new flags/options

## License

MIT License - see LICENSE file for details

## Credits

Built for importing viewing history from multiple sources into [Serializd](https://serializd.com), a TV show tracking service.

Uses:
- [TMDB API](https://www.themoviedb.org) for show metadata
- [serializd-py](../serializd-py) Python client for Serializd API

## Migration from v0.1.0

If you're upgrading from the Netflix-only version (v0.1.0), see [MIGRATION.md](MIGRATION.md) for details on the new CLI interface.

---

**Note:** This is an unofficial tool and is not affiliated with Netflix, Plex, or Serializd.
