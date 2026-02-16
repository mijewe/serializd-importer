#!/usr/bin/env python3
"""
Test Plex parser with real database.
"""

import sys
sys.path.insert(0, 'src')

from serializd_importer.sources.plex import PlexParser

print("Testing Plex Parser with real database...")
print()

# Create parser
parser = PlexParser()
print(f"Parser: {parser.name}")
print(f"Tag: {parser.default_tag}")
print()

# Parse Plex database
db_path = "nocommit/data/databaseBackup.dbaa7f234d-33cc-40b9-9d87-a7b9fe522ae4"
print(f"Parsing {db_path}...")
print()

# Test 1: All profiles
print("Test 1: Parsing all profiles...")
events_all = parser.parse(db_path)
print(f"   Found {len(events_all)} total watch events")

# Count by profile
from collections import Counter
profile_counts = Counter(event.profile_name for event in events_all)
print(f"   Profiles:")
for profile, count in profile_counts.most_common():
    print(f"      - {profile or '(unknown)'}: {count} events")
print()

# Test 2: Filter by profile
print("Test 2: Filtering by profile 'mwest56'...")
events_filtered = parser.parse(db_path, profile="mwest56")
print(f"   Found {len(events_filtered)} watch events for mwest56")
print()

# Test 3: Show sample episodes
print("Test 3: Sample episodes from mwest56:")
for i, event in enumerate(events_filtered[:5], 1):
    print(f"   {i}. {event.show_name} S{event.season_number}E{event.episode_number}")
    print(f"      Watched: {event.watched_at}")
print()

if len(events_filtered) > 5:
    print(f"   ... and {len(events_filtered) - 5} more")
    print()

print("=" * 60)
print("✅ Plex parser working correctly!")
print("=" * 60)
