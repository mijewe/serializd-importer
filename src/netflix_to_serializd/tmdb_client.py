from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv
import tmdbsimple as tmdb


@dataclass(frozen=True)
class TmdbShow:
    """Represents a TMDB TV show search result"""
    id: int
    name: str
    first_air_date: Optional[str] = None
    overview: Optional[str] = None
    original_language: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> TmdbShow:
        """Create TmdbShow from TMDB API response"""
        return cls(
            id=data['id'],
            name=data['name'],
            first_air_date=data.get('first_air_date'),
            overview=data.get('overview'),
            original_language=data.get('original_language'),
        )


class TmdbClient:
    """Wrapper around tmdbsimple for searching TV shows"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize TMDB client.

        Args:
            api_key: TMDB API key. If not provided, reads from TMDB_API_KEY env var.

        Raises:
            ValueError: If API key is not provided and not in environment
        """
        load_dotenv()
        self.api_key = api_key or os.getenv('TMDB_API_KEY')
        if not self.api_key:
            raise ValueError(
                'TMDB API key required. Set TMDB_API_KEY environment variable '
                'or pass api_key parameter.'
            )
        tmdb.API_KEY = self.api_key

    def search_shows(self, query: str) -> list[TmdbShow]:
        """
        Search for TV shows by title.

        Args:
            query: Show title to search for (e.g., "Seinfeld")

        Returns:
            List of matching shows, ordered by relevance.

        Example:
            >>> client = TmdbClient()
            >>> shows = client.search_shows("Seinfeld")
            >>> print(shows[0].id, shows[0].name)
            1400 Seinfeld
        """
        search = tmdb.Search()
        response = search.tv(query=query)

        # Parse results into TmdbShow objects
        results = response.get('results', [])
        return [TmdbShow.from_dict(result) for result in results]
