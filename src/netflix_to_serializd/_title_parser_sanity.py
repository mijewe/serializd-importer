from netflix_to_serializd.title_parser import parse_netflix_title, extract_show_name


def main() -> None:
    # Test cases from real Netflix viewing history
    test_titles = [
        # Regular episodes with Season
        "Seinfeld: Season 4: The Bubble Boy (Episode 6)",
        "Seinfeld: Season 3: The Keys (Episode 22)",

        # Episodes with Series (UK format)
        "Outnumbered: Series 1: The City Farm (Episode 3)",
        "Peep Show: Series 9: Are We Going to Be Alright? (Episode 6)",

        # Limited Series
        "Adolescence: Limited Series: Episode 4 (Episode 4)",

        # Movies (no season/episode)
        "Glass Onion: A Knives Out Mystery",
        "Knives Out",
        "The Truman Show",
    ]

    print("=" * 70)
    print("Netflix Title Parser Test")
    print("=" * 70)

    for title in test_titles:
        print(f"\nOriginal: {title}")
        parsed = parse_netflix_title(title)

        print(f"  Show Name: {parsed.show_name}")

        if parsed.is_movie:
            print(f"  Type: Movie")
        else:
            print(f"  Type: TV Episode")
            print(f"  Season: {parsed.season_number}")
            print(f"  Episode: {parsed.episode_number}")
            print(f"  Episode Title: {parsed.episode_title}")

    # Test the convenience function
    print("\n" + "=" * 70)
    print("Extract Show Name Only")
    print("=" * 70)

    for title in test_titles[:3]:
        show_name = extract_show_name(title)
        print(f"{title[:50]:50} → {show_name}")


if __name__ == "__main__":
    main()
