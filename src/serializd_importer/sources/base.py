"""
Base classes and interfaces for source data parsers.

This module defines the abstract interface that all source parsers must implement,
as well as the normalized data model (WatchEvent) that parsers return.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class WatchEvent:
    """
    Normalized viewing event from any source.

    This is the common data model that all source parsers return.
    It represents a single episode viewing with all the information
    needed to import it into Serializd.

    Attributes:
        show_name: Name of the TV show
        season_number: Season number (e.g., 1 for Season 1)
        episode_number: Episode number within the season (e.g., 3 for Episode 3)
        watched_at: Datetime when the episode was watched
        profile_name: Optional profile/user name who watched it
        is_movie: If True, this is a movie (not a TV episode)
    """
    show_name: str
    season_number: int
    episode_number: int
    watched_at: datetime
    profile_name: str = ""
    is_movie: bool = False


class SourceParser(ABC):
    """
    Abstract base class for source data parsers.

    Each source (Netflix, Plex, Trakt, etc.) implements this interface
    to parse their specific data format and return normalized WatchEvent objects.
    """

    @abstractmethod
    def parse(self, source_path: str, **kwargs) -> list[WatchEvent]:
        """
        Parse source data and return normalized watch events.

        Args:
            source_path: Path to source data (CSV file, database, JSON, etc.)
            **kwargs: Source-specific options (profile, exclude, etc.)

        Returns:
            List of normalized WatchEvent objects

        Raises:
            FileNotFoundError: If source_path doesn't exist
            ValueError: If source data is invalid or corrupted
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable source name (e.g., 'Netflix', 'Plex')"""
        pass

    @property
    @abstractmethod
    def default_tag(self) -> str:
        """Default Serializd tag for imports (e.g., '#netfliximport')"""
        pass
