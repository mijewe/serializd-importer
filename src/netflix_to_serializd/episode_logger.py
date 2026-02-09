from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional

from serializd import SerializdClient


class SeasonNotFoundError(RuntimeError):
    pass


@dataclass(frozen=True)
class EpisodeRef:
    show_id: int          # TMDB show id
    season_number: int    # human-friendly season number (e.g. 1)
    episode_number: int   # human-friendly episode number (e.g. 3)


class EpisodeLogger:
    """
    Small wrapper around SerializdClient for logging episodes as watched.

    SerializdClient.log_episodes requires:
      - show_id (TMDB show ID)
      - season_id (TMDB season ID)
      - episode_numbers (list of episode numbers)
    :contentReference[oaicite:2]{index=2}
    """

    def __init__(self, client: SerializdClient) -> None:
        self.client = client

    def resolve_season_id(self, show_id: int, season_number: int) -> int:
        """
        Fetch the show and find the TMDB season ID for the given season number.
        """
        show = self.client.get_show(show_id)

        # print(show)

        # show.seasons contains items with fields like id, seasonNumber, etc.
        for s in getattr(show, "seasons", []) or []:
            if getattr(s, "seasonNumber", None) == season_number:
                return int(s.id)
        raise SeasonNotFoundError(f"Season {season_number} not found for show_id={show_id}")

    def log_episode(self, ref: EpisodeRef, watched_at: datetime) -> bool:
        """
        Log a single episode as watched with a specific datetime.

        Args:
            ref: Episode reference with show_id, season_number, and episode_number
            watched_at: Datetime when the episode was watched
        """
        season_id = self.resolve_season_id(ref.show_id, ref.season_number)
        
        return self.client.review_episode(
            show_id=ref.show_id,
            season_id=season_id,
            episode_number=str(ref.episode_number),
            backdate=watched_at.isoformat()
        )

    # def log_episodes(self, show_id: int, season_number: int, episode_numbers: Iterable[int]) -> bool:
    #     """
    #     Log multiple episode numbers in the same season.
    #     """
    #     season_id = self.resolve_season_id(show_id, season_number)
    #     return bool(self.client.log_episodes(show_id, season_id, list(episode_numbers)))
