"""
Plex database parser.

Parses Plex SQLite database exports and returns normalized WatchEvent objects.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime

from serializd_importer.sources.base import SourceParser, WatchEvent


class PlexParser(SourceParser):
    """Parser for Plex SQLite database backups"""

    @property
    def name(self) -> str:
        return "Plex"

    @property
    def default_tag(self) -> str:
        return "#pleximport"

    def parse(self, source_path: str, profile: str | None = None, exclude: list[str] | None = None) -> list[WatchEvent]:
        """
        Parse Plex SQLite database and return normalized watch events.

        The Plex database has a hierarchical structure:
        - metadata_items table contains shows, seasons, and episodes
        - Relationships are defined via parent_id
        - metadata_item_views tracks when content was watched
        - accounts table has user/profile information

        Args:
            source_path: Path to Plex database file
            profile: Optional profile name to filter by (e.g., "mwest56")
            exclude: Optional list of show names to exclude

        Returns:
            List of WatchEvent objects for TV episodes (movies are filtered out)

        Example:
            >>> parser = PlexParser()
            >>> events = parser.parse("plex-database.db", profile="mwest56")
        """
        conn = sqlite3.connect(source_path)
        cursor = conn.cursor()

        # The metadata_item_views table has denormalized viewing data
        # grandparent_title = show name
        # parent_index = season number
        # index = episode number
        # metadata_type: 1=movie, 2=show, 3=season, 4=episode
        # Note: "index" is a reserved keyword, so we quote it
        query = """
        SELECT
            views.grandparent_title as show_name,
            views.parent_index as season_number,
            views.`index` as episode_number,
            views.viewed_at as timestamp,
            accounts.name as profile_name
        FROM metadata_item_views views
        JOIN accounts ON views.account_id = accounts.id
        WHERE views.metadata_type = 4  -- Type 4 = Episodes (not movies)
        """

        # Add profile filtering if specified
        params = []
        if profile:
            query += " AND accounts.name = ?"
            params.append(profile)

        # Execute query
        if params:
            cursor.execute(query, tuple(params))
        else:
            cursor.execute(query)

        # Parse results into WatchEvent objects
        events = []
        for row in cursor.fetchall():
            show_name, season_num, episode_num, timestamp, profile_name = row

            # Skip excluded shows (case-insensitive matching)
            if exclude and any(show_name.lower() == s.lower() for s in exclude):
                continue

            # Skip if season or episode number is None (data quality issue)
            if season_num is None or episode_num is None:
                continue

            # Convert Unix timestamp to datetime
            # Plex stores timestamps as Unix epoch (seconds since 1970-01-01)
            watched_at = datetime.fromtimestamp(timestamp)

            events.append(WatchEvent(
                show_name=show_name,
                season_number=season_num,
                episode_number=episode_num,
                watched_at=watched_at,
                profile_name=profile_name or "",
                is_movie=False
            ))

        conn.close()
        return events
