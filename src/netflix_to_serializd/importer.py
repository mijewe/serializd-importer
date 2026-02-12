from __future__ import annotations

import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from netflix_to_serializd.episode_logger import EpisodeLogger, EpisodeRef
from netflix_to_serializd.netflix import ViewingEntry, read_viewing_activity_csv
from netflix_to_serializd.serializd_adapter import create_client
from netflix_to_serializd.title_parser import parse_netflix_title, normalize_show_name_for_tmdb, get_tmdb_id_override
from netflix_to_serializd.tmdb_client import TmdbClient, TmdbShow


def deduplicate_viewing_entries(
    entries: list[ViewingEntry],
    window_days: int = 3
) -> tuple[list[ViewingEntry], int]:
    """
    Deduplicate viewing entries by keeping only the latest viewing
    when the same episode is watched multiple times within a window.

    This handles cases like:
    - Starting to watch an episode but falling asleep
    - Rewatching the next day to finish it

    Args:
        entries: List of viewing entries (assumed sorted by date descending)
        window_days: Number of days to consider as "duplicate window"

    Returns:
        Tuple of (deduplicated entries, number of duplicates removed)
    """
    from netflix_to_serializd.title_parser import parse_netflix_title

    # Group entries by (show_name, season, episode)
    # Key: (show_name, season_number, episode_number)
    # Value: list of (date, ViewingEntry)
    episode_groups: dict[tuple[str, int, int], list[tuple[datetime, ViewingEntry]]] = defaultdict(list)

    for entry in entries:
        parsed = parse_netflix_title(entry.title)

        # Skip movies
        if parsed.is_movie:
            continue

        key = (parsed.show_name, parsed.season_number, parsed.episode_number)
        episode_groups[key].append((datetime.combine(entry.watched_on, datetime.min.time()), entry))

    # Deduplicate each group
    deduplicated = []
    duplicates_removed = 0

    for key, viewings in episode_groups.items():
        # Sort by date descending (most recent first)
        viewings.sort(key=lambda x: x[0], reverse=True)

        # Keep the latest viewing
        latest_date, latest_entry = viewings[0]
        deduplicated.append(latest_entry)

        # Check if there are duplicates within the window
        for viewing_date, _ in viewings[1:]:
            days_diff = abs((latest_date - viewing_date).days)
            if days_diff <= window_days:
                duplicates_removed += 1

    # Also include all movies (which we skipped above)
    for entry in entries:
        parsed = parse_netflix_title(entry.title)
        if parsed.is_movie:
            deduplicated.append(entry)

    # Sort by date descending to maintain original order
    deduplicated.sort(key=lambda e: e.watched_on, reverse=True)

    return deduplicated, duplicates_removed


class NetflixImporter:
    """Imports Netflix viewing history to Serializd"""

    def __init__(self):
        self.tmdb_client = TmdbClient()
        self.serializd_client = create_client()
        self.logger = EpisodeLogger(self.serializd_client)

        # Cache TMDB show lookups to avoid repeated API calls
        self.show_cache: dict[str, Optional[TmdbShow]] = {}

        # Statistics
        self.stats = {
            'total_entries': 0,
            'duplicates_removed': 0,
            'movies_skipped': 0,
            'tv_episodes': 0,
            'tmdb_not_found': 0,
            'already_logged': 0,
            'logged_successfully': 0,
            'errors': 0,
        }

    def get_tmdb_show(self, show_name: str) -> Optional[TmdbShow]:
        """
        Get TMDB show with caching to avoid repeated API calls.

        Returns:
            TmdbShow if found, None if not found
        """
        if show_name in self.show_cache:
            return self.show_cache[show_name]

        # Check for manual TMDB ID override first
        override_id = get_tmdb_id_override(show_name)
        if override_id:
            # Create minimal TmdbShow with just the override ID
            result = TmdbShow(id=override_id, name=show_name)
            self.show_cache[show_name] = result
            return result

        # Normalize show name for TMDB search (e.g., "The Office (U.K.)" → "The Office UK")
        normalized_name = normalize_show_name_for_tmdb(show_name)

        shows = self.tmdb_client.search_shows(normalized_name)
        result = shows[0] if shows else None
        self.show_cache[show_name] = result
        return result

    def import_csv(self, csv_path: str, dry_run: bool = False, dedup_window_days: int = 3) -> None:
        """
        Import Netflix viewing history from CSV file.

        Args:
            csv_path: Path to Netflix ViewingActivity.csv
            dry_run: If True, only parse and display what would be imported
            dedup_window_days: Days within which duplicate viewings are merged (default: 3)
        """
        print(f"Reading Netflix viewing history from: {csv_path}")
        all_entries = read_viewing_activity_csv(csv_path)
        print(f"Found {len(all_entries)} total entries")

        # Deduplicate entries
        entries, duplicates_removed = deduplicate_viewing_entries(all_entries, window_days=dedup_window_days)
        self.stats['duplicates_removed'] = duplicates_removed

        if duplicates_removed > 0:
            print(f"Removed {duplicates_removed} duplicate viewings (within {dedup_window_days}-day window)")
        print(f"Processing {len(entries)} unique entries\n")

        if dry_run:
            print("DRY RUN MODE - No episodes will be logged\n")

        # Process entries
        for i, entry in enumerate(entries, 1):
            parsed = parse_netflix_title(entry.title)

            # Skip movies silently in dry run
            if parsed.is_movie:
                self.stats['total_entries'] += 1
                self.stats['movies_skipped'] += 1
                continue

            self.stats['total_entries'] += 1
            self.stats['tv_episodes'] += 1

            # Get TMDB show
            show = self.get_tmdb_show(parsed.show_name)
            if not show:
                print(f"[{i}/{len(entries)}] ⚠ TMDB not found: {parsed.show_name}")
                self.stats['tmdb_not_found'] += 1
                continue

            # Display what we're processing
            print(f"[{i}/{len(entries)}] {parsed.show_name} S{parsed.season_number}E{parsed.episode_number} - {entry.watched_on}")

            if dry_run:
                print(f"           → Would log to Serializd (TMDB ID: {show.id})")
                self.stats['logged_successfully'] += 1
                continue

            # Actually log the episode
            episode_ref = EpisodeRef(
                show_id=show.id,
                season_number=parsed.season_number,
                episode_number=parsed.episode_number
            )
            watched_at = datetime.combine(entry.watched_on, datetime.min.time())

            try:
                success = self.logger.log_episode(episode_ref, watched_at)
                if success:
                    print(f"           ✓ Logged to Serializd")
                    self.stats['logged_successfully'] += 1
                else:
                    print(f"           ⊘ Already logged (skipped)")
                    self.stats['already_logged'] += 1
            except Exception as e:
                print(f"           ✗ Error: {e}")
                self.stats['errors'] += 1

            # Small delay to avoid rate limiting
            time.sleep(0.5)

        # Print summary
        print("\n" + "=" * 70)
        print("Import Summary")
        print("=" * 70)
        print(f"Total entries processed: {self.stats['total_entries']}")
        print(f"Duplicates removed: {self.stats['duplicates_removed']}")
        print(f"Movies (skipped): {self.stats['movies_skipped']}")
        print(f"TV episodes found: {self.stats['tv_episodes']}")
        print(f"TMDB not found: {self.stats['tmdb_not_found']}")
        if not dry_run:
            print(f"Already logged (skipped): {self.stats['already_logged']}")
            print(f"Successfully logged: {self.stats['logged_successfully']}")
            print(f"Errors: {self.stats['errors']}")
        else:
            print(f"Would log: {self.stats['logged_successfully']}")
        print(f"\nUnique shows cached: {len(self.show_cache)}")


def main() -> None:
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m netflix_to_serializd.importer <path-to-ViewingActivity.csv> [--dry-run]")
        sys.exit(1)

    csv_path = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    importer = NetflixImporter()
    importer.import_csv(csv_path, dry_run=dry_run)


if __name__ == "__main__":
    main()
