#!/usr/bin/env python3
"""
Quick test script to verify the new package structure works.
"""

import sys
sys.path.insert(0, 'src')

print("Testing new serializd-importer structure...")
print()

# Test 1: Import base classes
print("1. Testing base imports...")
try:
    from serializd_importer.sources.base import WatchEvent, SourceParser
    print("   ✓ Successfully imported WatchEvent and SourceParser")
except ImportError as e:
    print(f"   ✗ Failed to import base classes: {e}")
    sys.exit(1)

# Test 2: Import Netflix parser
print("2. Testing Netflix parser import...")
try:
    from serializd_importer.sources.netflix import NetflixParser
    parser = NetflixParser()
    print(f"   ✓ Successfully imported NetflixParser")
    print(f"   ✓ Parser name: {parser.name}")
    print(f"   ✓ Default tag: {parser.default_tag}")
except ImportError as e:
    print(f"   ✗ Failed to import Netflix parser: {e}")
    sys.exit(1)

# Test 3: Import Plex parser
print("3. Testing Plex parser import...")
try:
    from serializd_importer.sources.plex import PlexParser
    parser = PlexParser()
    print(f"   ✓ Successfully imported PlexParser")
    print(f"   ✓ Parser name: {parser.name}")
    print(f"   ✓ Default tag: {parser.default_tag}")
except ImportError as e:
    print(f"   ✗ Failed to import Plex parser: {e}")
    sys.exit(1)

# Test 4: Import common modules
print("4. Testing common module imports...")
try:
    from serializd_importer.common.episode_logger import EpisodeLogger
    from serializd_importer.common.tmdb_client import TmdbClient
    from serializd_importer.common.serializd_adapter import create_client
    print("   ✓ Successfully imported all common modules")
except ImportError as e:
    if "serializd" in str(e):
        print(f"   ⚠ Skipping common modules (serializd-py not installed)")
        print("   → This is expected - install with: pip install -e ../serializd-py")
    else:
        print(f"   ✗ Failed to import common modules: {e}")
        sys.exit(1)

# Test 5: Create a sample WatchEvent
print("5. Testing WatchEvent creation...")
try:
    from datetime import datetime
    event = WatchEvent(
        show_name="Seinfeld",
        season_number=4,
        episode_number=6,
        watched_at=datetime(2024, 6, 10, 19, 30),
        profile_name="Michael"
    )
    print(f"   ✓ Created WatchEvent: {event.show_name} S{event.season_number}E{event.episode_number}")
except Exception as e:
    print(f"   ✗ Failed to create WatchEvent: {e}")
    sys.exit(1)

print()
print("=" * 60)
print("✅ All structure tests passed!")
print("=" * 60)
print()
print("Package structure is working correctly.")
print("Ready for Phase 3: Generic importer implementation")
