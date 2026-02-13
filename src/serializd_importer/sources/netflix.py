"""
Netflix viewing history parser.

Parses Netflix ViewingActivity.csv exports and returns normalized WatchEvent objects.
"""

from __future__ import annotations

import csv
import re
from datetime import date, datetime
from typing import Optional

from serializd_importer.sources.base import SourceParser, WatchEvent


# Manual TMDB ID overrides for shows that don't match well in search
# Format: Netflix show name → TMDB show ID
TMDB_ID_OVERRIDES = {
    "The Office (U.K.)": 2996,  # The Office UK (2001)
    "The Office (U.S.)": 2316,  # The Office US (2005)
}


class NetflixParser(SourceParser):
    """Parser for Netflix ViewingActivity.csv exports"""

    @property
    def name(self) -> str:
        return "Netflix"

    @property
    def default_tag(self) -> str:
        return "#netfliximport"

    def parse(self, source_path: str, profile: str | None = None, exclude: list[str] | None = None) -> list[WatchEvent]:
        """
        Parse Netflix ViewingActivity.csv and return normalized watch events.

        Args:
            source_path: Path to ViewingActivity.csv file
            profile: Optional profile name to filter by (e.g., "Michael")
            exclude: Optional list of show names to exclude

        Returns:
            List of WatchEvent objects for TV episodes (movies are filtered out)

        Example:
            >>> parser = NetflixParser()
            >>> events = parser.parse("ViewingActivity.csv", profile="Michael")
        """
        events = []

        with open(source_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            for row in reader:
                # Filter by profile name if specified
                if profile is not None:
                    row_profile = (row.get("Profile Name") or "").strip()
                    if row_profile != profile:
                        continue

                title = (row.get("Title") or "").strip()
                if not title:
                    continue

                # Parse Netflix title to extract show name, season, episode
                parsed = self._parse_netflix_title(title)

                # Skip movies (we only import TV episodes)
                if parsed.is_movie:
                    continue

                # Skip excluded shows
                if exclude and parsed.show_name.lower() in [s.lower() for s in exclude]:
                    continue

                # Parse watch date
                date_str = (row.get("Start Time") or row.get("Date") or "").strip()
                if not date_str:
                    continue

                # Handle both "YYYY-MM-DD HH:MM:SS" and "YYYY-MM-DD" formats
                if " " in date_str:
                    watched_at = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                else:
                    watched_on_date = date.fromisoformat(date_str)
                    watched_at = datetime.combine(watched_on_date, datetime.min.time())

                # Create normalized WatchEvent
                events.append(WatchEvent(
                    show_name=parsed.show_name,
                    season_number=parsed.season_number or 0,
                    episode_number=parsed.episode_number or 0,
                    watched_at=watched_at,
                    profile_name=row.get("Profile Name", "").strip(),
                    is_movie=False
                ))

        return events

    def _parse_netflix_title(self, title: str) -> "ParsedTitle":
        """
        Parse a Netflix title string to extract show name, season, and episode info.

        Handles various Netflix title formats:
        - "Seinfeld: Season 4: The Bubble Boy (Episode 6)"
        - "Outnumbered: Series 1: The City Farm (Episode 3)"
        - "Adolescence: Limited Series: Episode 4 (Episode 4)"
        - "Glass Onion: A Knives Out Mystery" (movie)
        """
        # Pattern 1: "{Show Name}: Season/Series {N}: {Episode Title} (Episode {N})"
        episode_pattern = r'^(.+?):\s+(?:Season|Series)\s+(\d+):\s+(.+?)\s+\(Episode\s+(\d+)\)$'
        match = re.match(episode_pattern, title, re.IGNORECASE)

        if match:
            show_name = match.group(1).strip()
            season_number = int(match.group(2))
            episode_number = int(match.group(4))
            return ParsedTitle(
                show_name=show_name,
                season_number=season_number,
                episode_number=episode_number,
                is_movie=False
            )

        # Pattern 2: "{Show Name}: Limited Series: {Episode Title} (Episode {N})"
        limited_series_pattern = r'^(.+?):\s+Limited Series:\s+(.+?)\s+\(Episode\s+(\d+)\)$'
        match = re.match(limited_series_pattern, title, re.IGNORECASE)

        if match:
            show_name = match.group(1).strip()
            episode_number = int(match.group(3))
            return ParsedTitle(
                show_name=show_name,
                season_number=1,  # Limited series = season 1
                episode_number=episode_number,
                is_movie=False
            )

        # If no match, treat as a movie
        return ParsedTitle(
            show_name=title.strip(),
            is_movie=True
        )


class ParsedTitle:
    """Helper class for parsed Netflix titles"""
    def __init__(self, show_name: str, season_number: Optional[int] = None,
                 episode_number: Optional[int] = None, is_movie: bool = False):
        self.show_name = show_name
        self.season_number = season_number
        self.episode_number = episode_number
        self.is_movie = is_movie


def normalize_show_name_for_tmdb(show_name: str) -> str:
    """
    Normalize show name for TMDB search.

    Handles common variations:
    - "The Office (U.K.)" → "The Office UK"
    - "Show Name (U.S.)" → "Show Name US"
    """
    normalized = re.sub(r'\s*\(U\.K\.\)', ' UK', show_name)
    normalized = re.sub(r'\s*\(U\.S\.\)', ' US', normalized)
    return normalized.strip()


def get_tmdb_id_override(show_name: str) -> Optional[int]:
    """Get manual TMDB ID override for shows that don't match well in search."""
    return TMDB_ID_OVERRIDES.get(show_name)
