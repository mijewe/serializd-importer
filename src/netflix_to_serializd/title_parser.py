from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


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
