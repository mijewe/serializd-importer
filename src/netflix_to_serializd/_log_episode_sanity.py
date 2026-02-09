from datetime import datetime
from netflix_to_serializd.serializd_adapter import create_client
from netflix_to_serializd.episode_logger import EpisodeLogger, EpisodeRef


def main() -> None:
    client = create_client()

    logger = EpisodeLogger(client)

    # Hardcoded example:
    # show_id: 114472 (Secret Invasion), season 1, episode 1
    ok = logger.log_episode(EpisodeRef(show_id=1400, season_number=3, episode_number=1), datetime(2024, 6, 1, 20, 0))
    print("logged:", ok)

if __name__ == "__main__":
    main()
