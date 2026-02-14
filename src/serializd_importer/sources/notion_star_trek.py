"""
Notion Star Trek import.

Parses a Notion CSV export + per-episode markdown review files and imports
them into Serializd with genre tags, emoji ratings, and review text.

Handles merging with existing logs:
- Existing log WITH review text → add a new log (don't touch the old one)
- Existing log WITHOUT review text → delete and re-create with new data
- No existing log → create new diary entry
"""

from __future__ import annotations

import csv
import time
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any

from serializd import SerializdClient

from serializd_importer.common.serializd_adapter import create_client


TMDB_OVERRIDES: dict[str, int] = {
    "Deep Space Nine": 580,   # Star Trek: Deep Space Nine
    "Voyager": 1855,          # Star Trek: Voyager
}

RATING_EMOJI: dict[str, str] = {
    "Love": "❤️",
    "Like": "👍",
    "Meh": "🤷‍♂️",
    "👎 Dislike": "👎",
}

IMPORT_TAG = "#startrekimport"


@dataclass(frozen=True)
class NotionEpisode:
    show_name: str
    season_number: int
    episode_number: int
    title: str
    watched_at: datetime | None
    rating: str
    genres: list[str]
    review_text: str = ""


def parse_csv(csv_path: str) -> list[NotionEpisode]:
    """Parse the Notion Star Trek CSV export."""
    episodes: list[NotionEpisode] = []

    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            show_name = row.get("Show", "").strip()
            title = row.get("Title", "").strip()

            try:
                season = int(row.get("Season", "0"))
                episode = int(row.get("Episode", "0"))
            except ValueError:
                continue

            if not show_name or season == 0 or episode == 0:
                continue

            # Parse date — format is "April 15, 2024" or empty
            date_str = row.get("Consumption Date", "").strip()
            watched_at = None
            if date_str:
                try:
                    watched_at = datetime.strptime(date_str, "%B %d, %Y")
                except ValueError:
                    pass

            rating = row.get("Rating", "").strip()

            # Parse genres from comma-separated string
            genre_str = row.get("Genre", "").strip()
            genres = [g.strip() for g in genre_str.split(",") if g.strip()] if genre_str else []

            episodes.append(NotionEpisode(
                show_name=show_name,
                season_number=season,
                episode_number=episode,
                title=title,
                watched_at=watched_at,
                rating=rating,
                genres=genres,
            ))

    return episodes


def parse_review_files(reviews_dir: str) -> dict[tuple[str, int, int, str], str]:
    """
    Parse markdown review files from Notion export.

    Returns a dict keyed by (show_name, season, episode, title) → review text body.
    Title is included in the key because some episode numbers are shared
    (e.g. S06E17 has two different episodes in the CSV).
    """
    reviews: dict[tuple[str, int, int, str], str] = {}
    review_path = Path(reviews_dir)

    for md_file in review_path.rglob("*.md"):
        text = md_file.read_text(encoding="utf-8")
        lines = text.split("\n")

        # Parse header fields
        show = ""
        season = 0
        episode = 0
        title = ""
        body_start = 0

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("Show:"):
                show = stripped[len("Show:"):].strip()
            elif stripped.startswith("Season:"):
                try:
                    season = int(stripped[len("Season:"):].strip())
                except ValueError:
                    pass
            elif stripped.startswith("Episode:"):
                try:
                    episode = int(stripped[len("Episode:"):].strip())
                except ValueError:
                    pass
            elif stripped.startswith("Title:"):
                title = stripped[len("Title:"):].strip()
            elif stripped == "" and i > 0 and body_start == 0:
                # First blank line after header block — everything after is body
                # But only count it if we've seen at least one header field
                if show or season or episode:
                    body_start = i + 1

        if not show or season == 0 or episode == 0:
            continue

        # Extract review body (skip the blank line separator)
        body_lines = lines[body_start:] if body_start > 0 else []
        review_body = "\n".join(body_lines).strip()

        if review_body:
            reviews[(show, season, episode, title)] = review_body

    return reviews


def merge_reviews(
    episodes: list[NotionEpisode],
    reviews: dict[tuple[str, int, int, str], str],
) -> list[NotionEpisode]:
    """Attach review text from markdown files to matching episodes."""
    merged = []
    for ep in episodes:
        key = (ep.show_name, ep.season_number, ep.episode_number, ep.title)
        review_text = reviews.get(key, "")
        merged.append(replace(ep, review_text=review_text))
    return merged


def build_review_text(ep: NotionEpisode) -> str:
    """
    Build the review body text in the format:
        {rating_emoji}

        {review_text}
    """
    emoji = RATING_EMOJI.get(ep.rating, "")
    parts = []
    if emoji:
        parts.append(emoji)
    if ep.review_text:
        parts.append("")  # blank line separator
        parts.append(ep.review_text)
    return "\n".join(parts)


def build_tags(ep: NotionEpisode) -> list[str]:
    """Build the tag list: import tag + genre tags."""
    tags = [IMPORT_TAG]
    tags.extend(ep.genres)
    return tags


class NotionStarTrekImporter:
    """Imports Notion Star Trek data into Serializd with merge logic."""

    def __init__(self) -> None:
        self.client: SerializdClient = create_client()
        self._season_cache: dict[tuple[int, int], int] = {}  # (show_id, season_num) → season_id
        self._show_cache: dict[int, Any] = {}  # show_id → show response
        self._user_reviews: list[dict[str, Any]] | None = None

    def _get_user_reviews(self) -> list[dict[str, Any]]:
        if self._user_reviews is None:
            self._user_reviews = self.client.get_user_reviews()
        return self._user_reviews

    def _invalidate_reviews_cache(self) -> None:
        """Force re-fetch of user reviews after mutations."""
        self._user_reviews = None

    def _resolve_season_id(self, show_id: int, season_number: int) -> int | None:
        cache_key = (show_id, season_number)
        if cache_key in self._season_cache:
            return self._season_cache[cache_key]

        if show_id not in self._show_cache:
            self._show_cache[show_id] = self.client.get_show(show_id)

        show = self._show_cache[show_id]
        for s in getattr(show, "seasons", []) or []:
            if getattr(s, "seasonNumber", None) == season_number:
                season_id = int(s.id)
                self._season_cache[cache_key] = season_id
                return season_id

        return None

    def _find_existing_review(
        self, show_id: int, season_id: int, episode_number: int
    ) -> dict[str, Any] | None:
        """Find an existing diary entry for this episode (any date)."""
        for review in self._get_user_reviews():
            if (review.get("showId") == show_id
                    and review.get("seasonId") == season_id
                    and review.get("episodeNumber") == episode_number):
                return review
        return None

    def import_episodes(
        self,
        episodes: list[NotionEpisode],
        dry_run: bool = False,
        order: str = "oldest",
    ) -> None:
        # Sort
        dated = [e for e in episodes if e.watched_at is not None]
        undated = [e for e in episodes if e.watched_at is None]

        if order == "oldest":
            dated.sort(key=lambda e: e.watched_at)  # type: ignore[arg-type]
        else:
            dated.sort(key=lambda e: e.watched_at, reverse=True)  # type: ignore[arg-type]

        # Process dated episodes first, then undated (which need existing log dates)
        all_episodes = dated + undated

        print(f"Found {len(all_episodes)} episodes ({len(dated)} with dates, {len(undated)} without)")
        if dry_run:
            print("DRY RUN MODE - No changes will be made\n")

        stats = {
            "created": 0,
            "replaced": 0,
            "added_new_log": 0,
            "skipped_no_date": 0,
            "skipped_season_not_found": 0,
            "skipped_show_not_found": 0,
            "errors": 0,
        }
        skipped_episodes: list[str] = []

        for i, ep in enumerate(all_episodes, 1):
            show_id = TMDB_OVERRIDES.get(ep.show_name)
            if show_id is None:
                print(f"[{i}/{len(all_episodes)}] !! Show not in TMDB overrides: {ep.show_name}")
                stats["skipped_show_not_found"] += 1
                continue

            season_id = self._resolve_season_id(show_id, ep.season_number)
            if season_id is None:
                print(f"[{i}/{len(all_episodes)}] !! Season {ep.season_number} not found for {ep.show_name}")
                stats["skipped_season_not_found"] += 1
                continue

            existing = self._find_existing_review(show_id, season_id, ep.episode_number)

            # Determine the date to use
            watched_at = ep.watched_at
            if watched_at is None and existing:
                backdate_str = existing.get("backdate", "")
                if backdate_str:
                    try:
                        backdate_str = backdate_str.replace("Z", "+00:00")
                        watched_at = datetime.fromisoformat(backdate_str)
                    except (ValueError, TypeError):
                        pass

            if watched_at is None:
                desc = f"{ep.show_name} S{ep.season_number:02d}E{ep.episode_number:02d} - {ep.title}"
                print(f"[{i}/{len(all_episodes)}] -- Skipped (no date): {desc}")
                skipped_episodes.append(desc)
                stats["skipped_no_date"] += 1
                continue

            review_text = build_review_text(ep)
            tags = build_tags(ep)
            label = f"{ep.show_name} S{ep.season_number:02d}E{ep.episode_number:02d} - {ep.title}"

            if existing:
                existing_has_text = bool(existing.get("reviewText", "").strip())
                review_id = existing.get("id")

                if existing_has_text:
                    # Existing review has text — add a new log alongside it
                    action = "ADD NEW LOG"
                    print(f"[{i}/{len(all_episodes)}] + {label} ({action})")
                    if not dry_run:
                        try:
                            self.client.log_episode_to_diary(
                                show_id=show_id,
                                season_id=season_id,
                                episode_number=ep.episode_number,
                                watched_at=watched_at.isoformat(),
                                review_text=review_text,
                                tags=tags,
                                mark_as_watched=False,
                            )
                            self._invalidate_reviews_cache()
                            stats["added_new_log"] += 1
                        except Exception as e:
                            print(f"           !! Error: {e}")
                            stats["errors"] += 1
                else:
                    # Existing review has no text — delete and re-create
                    action = "REPLACE"
                    print(f"[{i}/{len(all_episodes)}] ~ {label} ({action})")
                    if not dry_run:
                        try:
                            if review_id:
                                self.client.delete_diary_entry(review_id)
                            self.client.log_episode_to_diary(
                                show_id=show_id,
                                season_id=season_id,
                                episode_number=ep.episode_number,
                                watched_at=watched_at.isoformat(),
                                review_text=review_text,
                                tags=tags,
                            )
                            self._invalidate_reviews_cache()
                            stats["replaced"] += 1
                        except Exception as e:
                            print(f"           !! Error: {e}")
                            stats["errors"] += 1
            else:
                # No existing log — create new
                action = "CREATE"
                print(f"[{i}/{len(all_episodes)}] + {label} ({action})")
                if not dry_run:
                    try:
                        self.client.log_episode_to_diary(
                            show_id=show_id,
                            season_id=season_id,
                            episode_number=ep.episode_number,
                            watched_at=watched_at.isoformat(),
                            review_text=review_text,
                            tags=tags,
                        )
                        self._invalidate_reviews_cache()
                        stats["created"] += 1
                    except Exception as e:
                        print(f"           !! Error: {e}")
                        stats["errors"] += 1

            if not dry_run:
                time.sleep(0.5)

        # Summary
        print("\n" + "=" * 70)
        print("Import Summary")
        print("=" * 70)
        print(f"Total episodes: {len(all_episodes)}")
        if dry_run:
            print("(Dry run — no changes made)")
        else:
            print(f"Created (new):       {stats['created']}")
            print(f"Replaced (no text):  {stats['replaced']}")
            print(f"Added new log:       {stats['added_new_log']}")
            print(f"Errors:              {stats['errors']}")
        print(f"Skipped (no date):   {stats['skipped_no_date']}")
        print(f"Skipped (no season): {stats['skipped_season_not_found']}")
        print(f"Skipped (no show):   {stats['skipped_show_not_found']}")

        if skipped_episodes:
            print(f"\nEpisodes skipped (no date and no existing log):")
            for desc in skipped_episodes:
                print(f"  - {desc}")


def run_import(
    csv_path: str,
    reviews_dirs: list[str] | None = None,
    dry_run: bool = False,
    order: str = "oldest",
) -> None:
    """Entry point for the Notion Star Trek import."""
    print("Source: Notion Star Trek")
    print(f"Tag: {IMPORT_TAG}")
    print()

    # Parse CSV
    print(f"Parsing {csv_path}...")
    episodes = parse_csv(csv_path)
    print(f"Parsed {len(episodes)} episodes from CSV")

    # Parse review files from all provided directories
    if reviews_dirs:
        all_reviews: dict[tuple[str, int, int, str], str] = {}
        for reviews_dir in reviews_dirs:
            print(f"Parsing review files from {reviews_dir}...")
            reviews = parse_review_files(reviews_dir)
            print(f"  Found {len(reviews)} review files with text")
            all_reviews.update(reviews)
        print(f"Total review files with text: {len(all_reviews)}")
        episodes = merge_reviews(episodes, all_reviews)
        with_reviews = sum(1 for e in episodes if e.review_text)
        print(f"Matched {with_reviews} episodes with review text")

    print()

    # Import
    importer = NotionStarTrekImporter()
    importer.import_episodes(episodes, dry_run=dry_run, order=order)
