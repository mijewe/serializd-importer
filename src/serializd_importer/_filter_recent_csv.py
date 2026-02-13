"""
Filter Netflix viewing activity CSV to only include recent entries.

This allows for staged rollout by testing imports on recent data first.

Usage:
    python _filter_recent_csv.py input.csv output.csv [days]

Examples:
    # Filter to last 30 days
    python _filter_recent_csv.py ViewingActivity.csv ViewingActivity_recent30.csv 30

    # Filter to last 7 days
    python _filter_recent_csv.py ViewingActivity.csv ViewingActivity_recent7.csv 7
"""

import csv
import sys
from datetime import date, timedelta
from pathlib import Path

from netflix_to_serializd.netflix import read_viewing_activity_csv, ViewingEntry


def filter_recent_entries(entries: list[ViewingEntry], days: int = 30) -> list[ViewingEntry]:
    """
    Filter viewing entries to only include those within the last N days.

    Args:
        entries: List of viewing entries
        days: Number of days to include (default: 30)

    Returns:
        Filtered list of entries
    """
    cutoff_date = date.today() - timedelta(days=days)
    return [e for e in entries if e.watched_on >= cutoff_date]


def write_filtered_csv(entries: list[ViewingEntry], output_path: str) -> None:
    """
    Write filtered entries to a CSV file in Netflix format.

    Args:
        entries: List of viewing entries to write
        output_path: Path to output CSV file
    """
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        # Match Netflix CSV format with "Start Time" and "Title" columns
        writer = csv.DictWriter(f, fieldnames=['Title', 'Start Time'])
        writer.writeheader()

        for entry in entries:
            # Format date as "YYYY-MM-DD HH:MM:SS" (use midnight for time)
            start_time = f"{entry.watched_on} 00:00:00"
            writer.writerow({
                'Title': entry.title,
                'Start Time': start_time
            })


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python _filter_recent_csv.py <input.csv> <output.csv> [days] [--profile=NAME]")
        print()
        print("Examples:")
        print("  python _filter_recent_csv.py ViewingActivity.csv ViewingActivity_recent30.csv 30")
        print("  python _filter_recent_csv.py ViewingActivity.csv ViewingActivity_recent7.csv 7 --profile=Michael")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    days = 30
    profile_name = None

    # Parse optional arguments
    for i, arg in enumerate(sys.argv[3:], start=3):
        if arg.startswith("--profile="):
            profile_name = arg.split("=", 1)[1]
        elif arg.isdigit():
            days = int(arg)

    print(f"Reading viewing history from: {input_path}")
    if profile_name:
        print(f"Filtering by profile: {profile_name}")
    all_entries = read_viewing_activity_csv(input_path, profile_name=profile_name)
    print(f"Found {len(all_entries)} total entries")

    print(f"\nFiltering to entries within last {days} days...")
    cutoff_date = date.today() - timedelta(days=days)
    print(f"Cutoff date: {cutoff_date}")

    recent_entries = filter_recent_entries(all_entries, days=days)
    print(f"Found {len(recent_entries)} recent entries")

    if not recent_entries:
        print("\nNo recent entries found. Not creating output file.")
        return

    print(f"\nWriting filtered entries to: {output_path}")
    write_filtered_csv(recent_entries, output_path)

    print(f"\n✓ Created filtered CSV with {len(recent_entries)} entries")
    print(f"\nYou can now run the import on this file:")
    print(f"  python -m netflix_to_serializd.importer {output_path}")


if __name__ == "__main__":
    main()
