# Netflix to Serializd Importer

Import your Netflix viewing history into [Serializd](https://serializd.com) with full episode tracking, custom watch dates, and automatic deduplication.

## Features

- ✅ **Complete viewing history import** - Import all your Netflix TV show viewing history
- ✅ **Chronological ordering** - Episodes appear in watch order (oldest to newest by default)
- ✅ **Profile filtering** - Import only your profile's viewing history
- ✅ **Show exclusion** - Filter out shows you didn't watch (ex-girlfriend's shows, etc.)
- ✅ **Automatic deduplication** - Handles "fell asleep and rewatched" scenarios
- ✅ **TMDB integration** - Automatic show lookup with manual override support
- ✅ **Tagging** - All imports tagged with `#netfliximport` for easy cleanup
- ✅ **Idempotent** - Safe to re-run; skips already-logged episodes
- ✅ **Dry-run mode** - Test before importing

## Prerequisites

- Python 3.10+
- Netflix account with viewing history
- Serializd account
- TMDB API key (free at [themoviedb.org](https://www.themoviedb.org/settings/api))

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

3. **Install dependencies**
   ```bash
   pip install -e .
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

## Getting Netflix Viewing History

1. Go to [Netflix Account Settings](https://www.netflix.com/account)
2. Navigate to **Profile & Parental Controls** → **Viewing Activity**
3. Scroll to bottom and click **Download all**
4. Wait for email with download link (can take 24-48 hours)
5. Download and extract `ViewingActivity.csv`

## Usage

### Quick Start

```bash
# Activate virtual environment
source .venv/bin/activate

# Test with dry-run (recommended first step)
PYTHONPATH=src python -m netflix_to_serializd.importer \
  path/to/ViewingActivity.csv \
  --profile=YourName \
  --dry-run

# Import for real
PYTHONPATH=src python -m netflix_to_serializd.importer \
  path/to/ViewingActivity.csv \
  --profile=YourName
```

### Command-Line Options

```
python -m netflix_to_serializd.importer <ViewingActivity.csv> [OPTIONS]

Options:
  --dry-run              Run without actually logging episodes
  --order=oldest         Import oldest to newest (chronological, default)
  --order=newest         Import newest to oldest (reverse chronological)
  --profile=NAME         Filter by Netflix profile name
  --exclude=SHOWS        Exclude shows (comma-separated)
  --exclude-file=PATH    Exclude shows from file (one per line)
```

### Example Commands

**Dry-run test (recommended first):**
```bash
PYTHONPATH=src python -m netflix_to_serializd.importer \
  ViewingActivity.csv \
  --profile=Michael \
  --dry-run
```

**Import with exclusions:**
```bash
PYTHONPATH=src python -m netflix_to_serializd.importer \
  ViewingActivity.csv \
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
PYTHONPATH=src python -m netflix_to_serializd.importer \
  ViewingActivity.csv \
  --profile=Michael \
  --exclude-file=.exclude-shows.txt
```

**Test import (last 30 days only):**
```bash
# Create filtered CSV
PYTHONPATH=src python src/netflix_to_serializd/_filter_recent_csv.py \
  ViewingActivity.csv \
  ViewingActivity_recent30.csv \
  30 \
  --profile=Michael

# Import filtered CSV
PYTHONPATH=src python -m netflix_to_serializd.importer \
  ViewingActivity_recent30.csv
```

## Features Explained

### Profile Filtering

Netflix exports viewing history for **all profiles** on your account. Use `--profile` to import only your viewing history:

```bash
--profile=Michael
```

To see which profiles exist in your CSV:
```bash
cut -d',' -f3 ViewingActivity.csv | tail -n +2 | sort -u
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

All imported episodes are tagged with `#netfliximport`. This allows you to:

- Identify imported episodes in Serializd
- Easily clean up if something goes wrong
- Filter imported episodes from manual entries

### TMDB Show Matching

Shows are automatically looked up in TMDB. If a show doesn't match correctly, add a manual override:

Edit `src/netflix_to_serializd/title_parser.py`:
```python
TMDB_ID_OVERRIDES = {
    "The Office (U.K.)": 2996,  # The Office UK (2001)
    "The Office (U.S.)": 2316,  # The Office US (2005)
    "Your Show Name": 12345,    # Add your override here
}
```

Find TMDB IDs at [themoviedb.org](https://www.themoviedb.org).

## Cleanup

If you need to remove imported episodes (e.g., botched import):

```bash
# Remove ALL Serializd diary entries (⚠️ dangerous!)
PYTHONPATH=src python src/netflix_to_serializd/_clear_all_reviews.py

# Remove only entries with #netfliximport tag (recommended)
PYTHONPATH=src python src/netflix_to_serializd/_clear_all_reviews.py netfliximport
```

## Staged Rollout (Recommended)

For safety, test with recent data before full import:

**Step 1: Create test CSV (last 30 days)**
```bash
PYTHONPATH=src python src/netflix_to_serializd/_filter_recent_csv.py \
  ViewingActivity.csv \
  ViewingActivity_test.csv \
  30 \
  --profile=Michael \
  --exclude-file=.exclude-shows.txt
```

**Step 2: Run test import**
```bash
PYTHONPATH=src python -m netflix_to_serializd.importer ViewingActivity_test.csv
```

**Step 3: Verify in Serializd**
- Check episodes appear correctly
- Verify dates match Netflix
- Confirm tag `#netfliximport` is present

**Step 4: If good, run full import**
```bash
PYTHONPATH=src python -m netflix_to_serializd.importer \
  ViewingActivity.csv \
  --profile=Michael \
  --exclude-file=.exclude-shows.txt
```

**Step 5: If issues, rollback**
```bash
PYTHONPATH=src python src/netflix_to_serializd/_clear_all_reviews.py netfliximport
```

## Performance

- **Import speed:** ~1 second per episode (rate limiting to avoid API throttling)
- **Typical import:** 2,000-3,000 episodes = 30-50 minutes
- **First run:** Slower due to TMDB lookups; subsequent runs faster (idempotency)

## Troubleshooting

### "TMDB not found" errors

Some shows may not match TMDB's database. Solutions:

1. Check dry-run output for failed matches
2. Add manual overrides in `title_parser.py` (see TMDB Show Matching above)
3. Re-run import (already-logged episodes will be skipped)

### Duplicate episodes

If you see unexpected duplicates:

- **Same episode, different dates:** This is correct - treated as re-watch
- **Same episode, same date:** Should be auto-skipped (idempotency check)
- If issues persist, check Serializd web UI for existing entries

### Rate limiting

If you get rate limit errors:

- Default sleep is 0.5s per episode
- Edit `importer.py` line 203 to increase: `time.sleep(1.0)`

### Environment issues

```bash
# Verify .env is loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('SERIALIZD_USERNAME'))"

# Should print your username, not None
```

## Project Structure

```
netflix-to-serialized/
├── src/netflix_to_serializd/
│   ├── importer.py              # Main import logic
│   ├── episode_logger.py        # Serializd episode logging
│   ├── netflix.py               # Netflix CSV parsing
│   ├── title_parser.py          # Netflix title parsing & TMDB overrides
│   ├── tmdb_client.py           # TMDB API client
│   ├── serializd_adapter.py     # Serializd client factory
│   ├── _filter_recent_csv.py   # CSV filtering utility
│   └── _clear_all_reviews.py   # Cleanup utility
├── .env.example                 # Environment template
├── .exclude-shows.example       # Exclude file template
└── README.md                    # This file
```

## Edge Cases & Known Issues

### Multiple viewings on different dates

If you watched the same episode on different dates (intentional re-watch), both entries will be logged. This is by design.

To change this behavior (skip any episode that exists, regardless of date), modify `episode_logger.py:109-111`:

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

Built for importing Netflix viewing history into [Serializd](https://serializd.com), a TV show tracking service.

Uses:
- [TMDB API](https://www.themoviedb.org) for show metadata
- [serializd-py](../serializd-py) Python client for Serializd API

---

**Note:** This is an unofficial tool and is not affiliated with Netflix or Serializd.
