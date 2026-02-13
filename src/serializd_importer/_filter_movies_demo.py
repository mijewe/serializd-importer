from netflix_to_serializd.title_parser import parse_netflix_title


def main() -> None:
    # Sample Netflix titles (mix of TV shows and movies)
    titles = [
        "Seinfeld: Season 4: The Bubble Boy (Episode 6)",
        "Glass Onion: A Knives Out Mystery",
        "Outnumbered: Series 1: The City Farm (Episode 3)",
        "Knives Out",
        "Adolescence: Limited Series: Episode 4 (Episode 4)",
        "The Truman Show",
        "Peep Show: Series 9: Are We Going to Be Alright? (Episode 6)",
    ]

    print("=" * 70)
    print("All Titles")
    print("=" * 70)
    for title in titles:
        parsed = parse_netflix_title(title)
        type_label = "MOVIE" if parsed.is_movie else "TV SHOW"
        print(f"[{type_label:8}] {title}")

    print("\n" + "=" * 70)
    print("TV Shows Only (Filtered for Serializd)")
    print("=" * 70)

    tv_shows = [
        parse_netflix_title(title)
        for title in titles
        if not parse_netflix_title(title).is_movie
    ]

    for show in tv_shows:
        print(f"  {show.show_name}")
        print(f"    Season {show.season_number}, Episode {show.episode_number}")
        print(f"    \"{show.episode_title}\"")
        print()

    print(f"Summary: {len(tv_shows)} TV episodes, {len(titles) - len(tv_shows)} movies (filtered out)")


if __name__ == "__main__":
    main()
