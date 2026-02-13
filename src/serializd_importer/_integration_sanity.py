from datetime import datetime

from netflix_to_serializd.episode_logger import EpisodeLogger, EpisodeRef
from netflix_to_serializd.serializd_adapter import create_client
from netflix_to_serializd.title_parser import parse_netflix_title
from netflix_to_serializd.tmdb_client import TmdbClient


def main() -> None:
    # Hardcoded Netflix viewing entries (title + watch date)
    # Format: (netflix_title, watched_datetime)
    test_entries = [
        ("Seinfeld: Season 4: The Bubble Boy (Episode 6)", datetime(2024, 6, 10, 20, 0)),
        ("Seinfeld: Season 3: The Keys (Episode 22)", datetime(2024, 6, 9, 19, 30)),
        ("Outnumbered: Series 1: The City Farm (Episode 3)", datetime(2024, 6, 8, 21, 0)),
    ]

    # Initialize clients
    print("Initializing TMDB client and Serializd logger...")
    tmdb_client = TmdbClient()
    serializd_client = create_client()
    logger = EpisodeLogger(serializd_client)
    print()

    # Process each entry
    for netflix_title, watched_at in test_entries:
        print("=" * 70)
        print(f"Netflix Title: {netflix_title}")
        print(f"Watched: {watched_at}")
        print()

        # Step 1: Parse Netflix title
        parsed = parse_netflix_title(netflix_title)

        if parsed.is_movie:
            print("⊘ Skipping - detected as movie (Serializd is TV shows only)")
            print()
            continue

        print(f"Parsed:")
        print(f"  Show Name: {parsed.show_name}")
        print(f"  Season: {parsed.season_number}")
        print(f"  Episode: {parsed.episode_number}")
        print(f"  Episode Title: {parsed.episode_title}")
        print()

        # Step 2: Search TMDB for show ID
        print(f"Searching TMDB for '{parsed.show_name}'...")
        shows = tmdb_client.search_shows(parsed.show_name)

        if not shows:
            print(f"✗ No TMDB results found for '{parsed.show_name}'")
            print()
            continue

        # Use the first (most relevant) result
        show = shows[0]
        print(f"Found: {show.name} (TMDB ID: {show.id})")
        if show.first_air_date:
            print(f"  First aired: {show.first_air_date}")
        print()

        # Step 3: Log to Serializd
        print(f"Logging to Serializd...")
        episode_ref = EpisodeRef(
            show_id=show.id,
            season_number=parsed.season_number,
            episode_number=parsed.episode_number
        )

        try:
            success = logger.log_episode(episode_ref, watched_at)
            if success:
                print(f"✓ Successfully logged S{parsed.season_number}E{parsed.episode_number} to Serializd")
            else:
                print(f"✗ Failed to log episode")
        except Exception as e:
            print(f"✗ Error logging episode: {e}")

        print()

    print("=" * 70)
    print("Integration test complete!")


if __name__ == "__main__":
    main()
