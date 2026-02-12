from netflix_to_serializd.tmdb_client import TmdbClient

def main() -> None:
    # Initialize TMDB client (will read TMDB_API_KEY from environment)
    client = TmdbClient()

    # Test 1: Search for Seinfeld
    print("Searching for 'Seinfeld'...")
    shows = client.search_shows("Seinfeld")

    if not shows:
        print("No results found!")
        return

    print(f"\nFound {len(shows)} results:\n")
    for i, show in enumerate(shows[:5], 1):  # Show top 5 results
        print(f"{i}. {show.name}")
        print(f"   ID: {show.id}")
        print(f"   First Air Date: {show.first_air_date or 'Unknown'}")
        print(f"   Overview: {show.overview[:100] if show.overview else 'N/A'}...")
        print()

    # Verify we got the expected show
    seinfeld = shows[0]
    if seinfeld.id == 1400:
        print(f"✓ Success! Found Seinfeld with correct ID: {seinfeld.id}")
    else:
        print(f"⚠ Warning: Expected ID 1400, got {seinfeld.id}")

    # Test 2: Try another show
    print("\n" + "="*60)
    print("Searching for 'Breaking Bad'...")
    shows2 = client.search_shows("Breaking Bad")
    if shows2:
        print(f"\nFound: {shows2[0].name} (ID: {shows2[0].id})")
    else:
        print("No results found!")


if __name__ == "__main__":
    main()
