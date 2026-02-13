#!/usr/bin/env python3
"""
Test Netflix parser with sample CSV data.
"""

import sys
sys.path.insert(0, 'src')

from serializd_importer.sources.netflix import NetflixParser

print("Testing Netflix Parser with sample data...")
print()

# Create parser
parser = NetflixParser()
print(f"Parser: {parser.name}")
print(f"Tag: {parser.default_tag}")
print()

# Parse test CSV
print("Parsing test_data.csv...")
events = parser.parse("test_data.csv", profile="Michael")

print(f"Found {len(events)} watch events")
print()

# Display parsed events
for i, event in enumerate(events, 1):
    print(f"{i}. {event.show_name}")
    print(f"   Season {event.season_number}, Episode {event.episode_number}")
    print(f"   Watched: {event.watched_at}")
    print(f"   Profile: {event.profile_name}")
    print(f"   Movie: {event.is_movie}")
    print()

print("=" * 60)
print("Expected: 3 TV episodes (movie should be filtered out)")
print(f"Actual: {len(events)} episodes")

if len(events) == 3:
    print("✅ Netflix parser working correctly!")
else:
    print(f"⚠ Expected 3 episodes but got {len(events)}")
