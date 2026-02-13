from datetime import datetime
from netflix_to_serializd.serializd_adapter import create_client
from netflix_to_serializd.episode_logger import EpisodeLogger, EpisodeRef


def main() -> None:
    client = create_client()

    logger = EpisodeLogger(client)

    show_id = 1400 # Seinfeld
    season_number = 3
    episode_number = 3
    watched_at = datetime(2024, 6, 4, 20, 0)

    ok = logger.log_episode(EpisodeRef(show_id, season_number, episode_number), watched_at)

    print("logged:", ok)

if __name__ == "__main__":
    main()
