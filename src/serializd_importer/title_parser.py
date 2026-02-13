from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# Manual TMDB ID overrides for shows that don't match well in search
# Format: Netflix show name → TMDB show ID
TMDB_ID_OVERRIDES = {
    "The Office (U.K.)": 2996,  # The Office UK (2001)
    "The Office (U.S.)": 2316,  # The Office US (2005)
}


@dataclass(frozen=True)
class ParsedTitle:
    """Represents a parsed Netflix title"""
    show_name: str
    season_number: Optional[int] = None
    episode_number: Optional[int] = None
    episode_title: Optional[str] = None
    is_movie: bool = False


def parse_netflix_title(title: str) -> ParsedTitle:
    """
    Parse a Netflix title string to extract show name, season, and episode info.

    Handles various Netflix title formats:
    - "Seinfeld: Season 4: The Bubble Boy (Episode 6)"
    - "Outnumbered: Series 1: The City Farm (Episode 3)"
    - "Adolescence: Limited Series: Episode 4 (Episode 4)"
    - "Glass Onion: A Knives Out Mystery" (movie)

    Args:
        title: Raw title string from Netflix CSV

    Returns:
        ParsedTitle with extracted information

    Example:
        >>> parsed = parse_netflix_title("Seinfeld: Season 3: The Pen (Episode 5)")
        >>> print(parsed.show_name, parsed.season_number, parsed.episode_number)
        Seinfeld 3 5
    """
    # Try to match episodic content patterns
    # Pattern 1: "{Show Name}: Season/Series {N}: {Episode Title} (Episode {N})"
    episode_pattern = r'^(.+?):\s+(?:Season|Series)\s+(\d+):\s+(.+?)\s+\(Episode\s+(\d+)\)$'
    match = re.match(episode_pattern, title, re.IGNORECASE)

    if match:
        show_name = match.group(1).strip()
        season_number = int(match.group(2))
        episode_title = match.group(3).strip()
        episode_number = int(match.group(4))

        return ParsedTitle(
            show_name=show_name,
            season_number=season_number,
            episode_number=episode_number,
            episode_title=episode_title,
            is_movie=False
        )

    # Pattern 2: "{Show Name}: Limited Series: {Episode Title} (Episode {N})"
    # Limited series typically treat all episodes as season 1
    limited_series_pattern = r'^(.+?):\s+Limited Series:\s+(.+?)\s+\(Episode\s+(\d+)\)$'
    match = re.match(limited_series_pattern, title, re.IGNORECASE)

    if match:
        show_name = match.group(1).strip()
        episode_title = match.group(2).strip()
        episode_number = int(match.group(3))

        return ParsedTitle(
            show_name=show_name,
            season_number=1,  # Limited series = season 1
            episode_number=episode_number,
            episode_title=episode_title,
            is_movie=False
        )

    # If no match, treat as a movie (no season/episode info)
    return ParsedTitle(
        show_name=title.strip(),
        is_movie=True
    )


def normalize_show_name_for_tmdb(show_name: str) -> str:
    """
    Normalize show name for TMDB search.

    Handles common variations that don't match TMDB's naming:
    - "The Office (U.K.)" → "The Office UK"
    - "Show Name (U.S.)" → "Show Name US"

    Args:
        show_name: Show name extracted from Netflix title

    Returns:
        Normalized show name for TMDB search

    Example:
        >>> normalize_show_name_for_tmdb("The Office (U.K.)")
        'The Office UK'
    """
    # Replace country codes in parentheses with space + abbreviation
    # (U.K.) → UK, (U.S.) → US, etc.
    normalized = re.sub(r'\s*\(U\.K\.\)', ' UK', show_name)
    normalized = re.sub(r'\s*\(U\.S\.\)', ' US', normalized)

    return normalized.strip()


def get_tmdb_id_override(show_name: str) -> Optional[int]:
    """
    Get manual TMDB ID override for shows that don't match well in search.

    Args:
        show_name: Netflix show name

    Returns:
        TMDB show ID if override exists, None otherwise

    Example:
        >>> get_tmdb_id_override("The Office (U.K.)")
        2996
    """
    return TMDB_ID_OVERRIDES.get(show_name)


def extract_show_name(title: str) -> str:
    """
    Extract just the show name from a Netflix title.

    This is a convenience function for when you only need the show name.

    Args:
        title: Raw title string from Netflix CSV

    Returns:
        Show name (e.g., "Seinfeld")

    Example:
        >>> extract_show_name("Seinfeld: Season 3: The Pen (Episode 5)")
        'Seinfeld'
    """
    parsed = parse_netflix_title(title)
    return parsed.show_name
