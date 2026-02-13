"""
Generic importer for any source (Netflix, Plex, Trakt, etc.).

This module contains source-agnostic import logic that works with normalized
WatchEvent objects from any source parser.
"""

from __future__ import annotations

import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from serializd_importer.common.episode_logger import EpisodeLogger, EpisodeRef
from serializd_importer.common.serializd_adapter import create_client
from serializd_importer.common.tmdb_client import TmdbClient, TmdbShow
from serializd_importer.sources.base import WatchEvent


def deduplicate_watch_events(
    events: list[WatchEvent],
    window_days: int = 3
) -> tuple[list[WatchEvent], int]:
    """
    Deduplicate watch events by keeping only the latest viewing
    when the same episode is watched multiple times within a window.

    This handles cases like:
    - Starting to watch an episode but falling asleep
    - Rewatching the next day to finish it

    Args:
        events: List of WatchEvent objects (any order)
        window_days: Number of days to consider as "duplicate window"

    Returns:
        Tuple of (deduplicated events, number of duplicates removed)
    """
    # Group events by (show_name, season, episode)
    # Key: (show_name, season_number, episode_number)
    # Value: list of (datetime, WatchEvent)
    episode_groups: dict[tuple[str, int, int], list[tuple[datetime, WatchEvent]]] = defaultdict(list)

    for event in events:
        # Skip movies (we only import TV episodes)
        if event.is_movie:
            continue

        key = (event.show_name, event.season_number, event.episode_number)
        episode_groups[key].append((event.watched_at, event))

    # Deduplicate each group
    deduplicated = []
    duplicates_removed = 0

    for key, viewings in episode_groups.items():
        # Sort by date descending (most recent first)
        viewings.sort(key=lambda x: x[0], reverse=True)

        # Keep the latest viewing
        latest_date, latest_event = viewings[0]
        deduplicated.append(latest_event)

        # Count duplicates within the window
        for viewing_date, _ in viewings[1:]:
            days_diff = abs((latest_date - viewing_date).days)
            if days_diff <= window_days:
                duplicates_removed += 1

    return deduplicated, duplicates_removed


class GenericImporter:
    """
    Generic importer that works with any source.

    Takes normalized WatchEvent objects from source parsers and imports
    them into Serializd with TMDB lookup and deduplication.
    """

    def __init__(self, source_tag: str = "#import"):
        """
        Initialize the generic importer.

        Args:
            source_tag: Tag to add to all imported episodes (e.g., "#netfliximport")
        """
        self.tmdb_client = TmdbClient()
        self.serializd_client = create_client()
        self.logger = EpisodeLogger(self.serializd_client, import_tag=source_tag)

        # Cache TMDB show lookups to avoid repeated API calls
        self.show_cache: dict[str, Optional[TmdbShow]] = {}

        # Statistics
        self.stats = {
            'total_events': 0,
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

        Args:
            show_name: Name of the TV show

        Returns:
            TmdbShow if found, None if not found
        """
        if show_name in self.show_cache:
            return self.show_cache[show_name]

        # Search TMDB for the show
        shows = self.tmdb_client.search_shows(show_name)
        result = shows[0] if shows else None
        self.show_cache[show_name] = result
        return result

    def import_events(
        self,
        events: list[WatchEvent],
        dry_run: bool = False,
        dedup_window_days: int = 3,
        order: str = "oldest"
    ) -> None:
        """
        Import watch events into Serializd.

        Args:
            events: List of WatchEvent objects from source parser
            dry_run: If True, only parse and display what would be imported
            dedup_window_days: Days within which duplicate viewings are merged (default: 3)
            order: Import order - "oldest" (chronological, default) or "newest" (reverse chronological)
        """
        print(f"Found {len(events)} total events")

        # Deduplicate events
        events, duplicates_removed = deduplicate_watch_events(events, window_days=dedup_window_days)
        self.stats['duplicates_removed'] = duplicates_removed

        # Sort events based on order preference
        if order == "oldest":
            # Oldest first (chronological order)
            events.sort(key=lambda e: e.watched_at)
            order_msg = "oldest to newest (chronological)"
        else:
            # Newest first (reverse chronological)
            events.sort(key=lambda e: e.watched_at, reverse=True)
            order_msg = "newest to oldest (reverse chronological)"

        if duplicates_removed > 0:
            print(f"Removed {duplicates_removed} duplicate viewings (within {dedup_window_days}-day window)")
        print(f"Processing {len(events)} unique events ({order_msg})\n")

        if dry_run:
            print("DRY RUN MODE - No episodes will be logged\n")

        # Process events
        for i, event in enumerate(events, 1):
            self.stats['total_events'] += 1

            # Skip movies
            if event.is_movie:
                self.stats['movies_skipped'] += 1
                continue

            self.stats['tv_episodes'] += 1

            # Get TMDB show
            show = self.get_tmdb_show(event.show_name)
            if not show:
                print(f"[{i}/{len(events)}] ⚠ TMDB not found: {event.show_name}")
                self.stats['tmdb_not_found'] += 1
                continue

            # Display what we're processing
            print(f"[{i}/{len(events)}] {event.show_name} S{event.season_number}E{event.episode_number} - {event.watched_at.date()}")

            if dry_run:
                print(f"           → Would log to Serializd (TMDB ID: {show.id})")
                self.stats['logged_successfully'] += 1
                continue

            # Actually log the episode
            episode_ref = EpisodeRef(
                show_id=show.id,
                season_number=event.season_number,
                episode_number=event.episode_number
            )

            try:
                success = self.logger.log_episode(episode_ref, event.watched_at)
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
        self._print_summary(dry_run)

    def _print_summary(self, dry_run: bool) -> None:
        """Print import statistics summary."""
        print("\n" + "=" * 70)
        print("Import Summary")
        print("=" * 70)
        print(f"Total events processed: {self.stats['total_events']}")
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
