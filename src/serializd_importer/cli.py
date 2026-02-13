"""
Multi-source CLI for serializd-importer.

Main entry point that dispatches to different source parsers (Netflix, Plex, etc.).
"""

import sys

from serializd_importer.sources.netflix import NetflixParser
from serializd_importer.sources.plex import PlexParser
from serializd_importer.common.importer import GenericImporter


# Registry of available source parsers
SOURCES = {
    "netflix": NetflixParser,
    "plex": PlexParser,
}


def main() -> None:
    """Main CLI entry point."""
    if len(sys.argv) < 3:
        print("Usage: serializd-importer <source> <path> [OPTIONS]")
        print()
        print("Sources:")
        print("  netflix    Import from Netflix ViewingActivity.csv")
        print("  plex       Import from Plex SQLite database")
        print()
        print("Options:")
        print("  --dry-run              Test without logging episodes")
        print("  --profile=NAME         Filter by profile name")
        print("  --exclude=SHOWS        Exclude shows (comma-separated)")
        print("  --exclude-file=PATH    Exclude shows from file (one per line)")
        print("  --order=oldest         Import oldest to newest (default)")
        print("  --order=newest         Import newest to oldest")
        print("  --tag=TAG              Custom import tag (default: source-specific)")
        print()
        print("Examples:")
        print("  serializd-importer netflix ViewingActivity.csv --profile=Michael --dry-run")
        print("  serializd-importer plex plex.db --profile=mwest56 --exclude-file=.exclude-shows.txt")
        sys.exit(1)

    source_name = sys.argv[1].lower()
    source_path = sys.argv[2]

    # Validate source
    if source_name not in SOURCES:
        print(f"Error: Unknown source '{source_name}'")
        print(f"Available sources: {', '.join(SOURCES.keys())}")
        sys.exit(1)

    # Parse command-line options
    dry_run = "--dry-run" in sys.argv
    order = "oldest"
    profile = None
    exclude_shows = []
    custom_tag = None

    for arg in sys.argv[3:]:
        if arg.startswith("--order="):
            order = arg.split("=", 1)[1]
            if order not in ["oldest", "newest"]:
                print(f"Error: Invalid order '{order}'. Must be 'oldest' or 'newest'")
                sys.exit(1)
        elif arg.startswith("--profile="):
            profile = arg.split("=", 1)[1]
        elif arg.startswith("--exclude="):
            exclude_str = arg.split("=", 1)[1]
            exclude_shows.extend([s.strip() for s in exclude_str.split(",") if s.strip()])
        elif arg.startswith("--exclude-file="):
            exclude_file = arg.split("=", 1)[1]
            try:
                with open(exclude_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            exclude_shows.append(line)
            except FileNotFoundError:
                print(f"Error: Exclude file not found: {exclude_file}")
                sys.exit(1)
            except Exception as e:
                print(f"Error reading exclude file: {e}")
                sys.exit(1)
        elif arg.startswith("--tag="):
            custom_tag = arg.split("=", 1)[1]

    # Instantiate source parser
    parser_class = SOURCES[source_name]
    parser = parser_class()

    print(f"Source: {parser.name}")
    print(f"Tag: {custom_tag or parser.default_tag}")
    print()

    # Parse source data
    print(f"Parsing {source_path}...")
    try:
        events = parser.parse(
            source_path,
            profile=profile,
            exclude=exclude_shows if exclude_shows else None
        )
    except FileNotFoundError:
        print(f"Error: File not found: {source_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing {source_name} data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Import using generic importer
    importer = GenericImporter(source_tag=custom_tag or parser.default_tag)
    importer.import_events(events, dry_run=dry_run, order=order)


if __name__ == "__main__":
    main()
