"""
General-purpose CSV importer.

Users format their data into a simple CSV with standardised columns and this
importer handles TMDB lookup, existing-log merging, review text, and tags.

Required CSV columns: show, season, episode
Optional CSV columns: date, review, tags

Handles merging with existing Serializd logs:
- Existing log WITH review text → add a new log (don't touch the old one)
- Existing log WITHOUT review text → delete and re-create with new data
- No existing log → create new diary entry
"""

from __future__ import annotations

import csv
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from serializd import SerializdClient

from serializd_importer.common.serializd_adapter import create_client
from serializd_importer.common.tmdb_client import TmdbClient, TmdbShow

IMPORT_TAG = "#csvimport"

DATE_FORMATS = [
    "%Y-%m-%d",           # 2024-04-15
    "%Y-%m-%dT%H:%M:%S",  # 2024-04-15T12:00:00
    "%B %d, %Y",          # April 15, 2024
    "%B %d %Y",           # April 15 2024
    "%d/%m/%Y",           # 15/04/2024
    "%m/%d/%Y",           # 04/15/2024
]


@dataclass(frozen=True)
class CsvEpisode:
    show_name: str
    season_number: int
    episode_number: int
    watched_at: datetime | None
    review_text: str
    tags: list[str]


def parse_date(date_str: str) -> datetime | None:
    """Try multiple date formats, return first match or None."""
    date_str = date_str.strip()
    if not date_str:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def parse_tmdb_map(map_path: str) -> dict[str, int] | None:
    """Parse a .tmdbmap file mapping show names to TMDB IDs.

    Format: one entry per line as `Show Name:TMDB_ID`. Lines starting with #
    are comments. Returns None if the file doesn't exist.
    """
    try:
        with open(map_path, encoding="utf-8") as f:
            overrides: dict[str, int] = {}
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" not in line:
                    print(f"Warning: skipping invalid line {line_num} in {map_path}: {line}")
                    continue
                name, id_str = line.rsplit(":", 1)
                name = name.strip()
                id_str = id_str.strip()
                try:
                    overrides[name] = int(id_str)
                except ValueError:
                    print(f"Warning: invalid TMDB ID on line {line_num} in {map_path}: {id_str}")
            return overrides if overrides else None
    except FileNotFoundError:
        return None


def parse_csv(csv_path: str) -> list[CsvEpisode]:
    """Parse a user-provided CSV into episodes."""
    episodes: list[CsvEpisode] = []

    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        # Validate required columns
        fields = set(reader.fieldnames or [])
        missing = {"show", "season", "episode"} - fields
        if missing:
            raise ValueError(
                f"CSV missing required columns: {', '.join(sorted(missing))}. "
                f"Found: {', '.join(sorted(fields))}"
            )

        for row in reader:
            show_name = row.get("show", "").strip()

            try:
                season = int(row.get("season", "0"))
                episode = int(row.get("episode", "0"))
            except ValueError:
                continue

            if not show_name or season == 0 or episode == 0:
                continue

            watched_at = parse_date(row.get("date", ""))
            review_text = row.get("review", "").strip()

            tag_str = row.get("tags", "").strip()
            tags = [t.strip() for t in tag_str.split(",") if t.strip()] if tag_str else []

            episodes.append(CsvEpisode(
                show_name=show_name,
                season_number=season,
                episode_number=episode,
                watched_at=watched_at,
                review_text=review_text,
                tags=tags,
            ))

    return episodes


class CsvImporter:
    """Imports CSV episode data into Serializd with merge logic."""

    def __init__(
        self,
        import_tag: str = IMPORT_TAG,
        tmdb_overrides: dict[str, int] | None = None,
    ) -> None:
        self.client: SerializdClient = create_client()
        self.tmdb_client = TmdbClient()
        self.import_tag = import_tag
        self.tmdb_overrides = tmdb_overrides or {}
        self._season_cache: dict[tuple[int, int], int] = {}
        self._show_cache: dict[int, Any] = {}
        self._tmdb_search_cache: dict[str, int | None] = {}
        self._user_reviews: list[dict[str, Any]] | None = None

    def _get_user_reviews(self) -> list[dict[str, Any]]:
        if self._user_reviews is None:
            self._user_reviews = self.client.get_user_reviews()
        return self._user_reviews

    def _invalidate_reviews_cache(self) -> None:
        self._user_reviews = None

    def _resolve_show_id(self, show_name: str) -> int | None:
        """Resolve show name to TMDB ID via overrides or search."""
        if show_name in self.tmdb_overrides:
            return self.tmdb_overrides[show_name]

        if show_name in self._tmdb_search_cache:
            return self._tmdb_search_cache[show_name]

        shows = self.tmdb_client.search_shows(show_name)
        result = shows[0].id if shows else None
        self._tmdb_search_cache[show_name] = result
        return result

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
        for review in self._get_user_reviews():
            if (review.get("showId") == show_id
                    and review.get("seasonId") == season_id
                    and review.get("episodeNumber") == episode_number):
                return review
        return None

    def _build_tags(self, ep: CsvEpisode) -> list[str]:
        tags = [self.import_tag] if self.import_tag else []
        tags.extend(ep.tags)
        return tags

    def import_episodes(
        self,
        episodes: list[CsvEpisode],
        dry_run: bool = False,
        order: str = "oldest",
    ) -> None:
        dated = [e for e in episodes if e.watched_at is not None]
        undated = [e for e in episodes if e.watched_at is None]

        if order == "oldest":
            dated.sort(key=lambda e: e.watched_at)  # type: ignore[arg-type]
        else:
            dated.sort(key=lambda e: e.watched_at, reverse=True)  # type: ignore[arg-type]

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
            show_id = self._resolve_show_id(ep.show_name)
            if show_id is None:
                print(f"[{i}/{len(all_episodes)}] !! TMDB not found: {ep.show_name}")
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
                desc = f"{ep.show_name} S{ep.season_number:02d}E{ep.episode_number:02d}"
                print(f"[{i}/{len(all_episodes)}] -- Skipped (no date): {desc}")
                skipped_episodes.append(desc)
                stats["skipped_no_date"] += 1
                continue

            tags = self._build_tags(ep)
            label = f"{ep.show_name} S{ep.season_number:02d}E{ep.episode_number:02d}"

            if existing:
                existing_has_text = bool(existing.get("reviewText", "").strip())
                review_id = existing.get("id")

                if existing_has_text:
                    action = "ADD NEW LOG"
                    print(f"[{i}/{len(all_episodes)}] + {label} ({action})")
                    if not dry_run:
                        try:
                            self.client.log_episode_to_diary(
                                show_id=show_id,
                                season_id=season_id,
                                episode_number=ep.episode_number,
                                watched_at=watched_at.isoformat(),
                                review_text=ep.review_text,
                                tags=tags,
                                mark_as_watched=False,
                            )
                            self._invalidate_reviews_cache()
                            stats["added_new_log"] += 1
                        except Exception as e:
                            print(f"           !! Error: {e}")
                            stats["errors"] += 1
                else:
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
                                review_text=ep.review_text,
                                tags=tags,
                            )
                            self._invalidate_reviews_cache()
                            stats["replaced"] += 1
                        except Exception as e:
                            print(f"           !! Error: {e}")
                            stats["errors"] += 1
            else:
                action = "CREATE"
                print(f"[{i}/{len(all_episodes)}] + {label} ({action})")
                if not dry_run:
                    try:
                        self.client.log_episode_to_diary(
                            show_id=show_id,
                            season_id=season_id,
                            episode_number=ep.episode_number,
                            watched_at=watched_at.isoformat(),
                            review_text=ep.review_text,
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
    tmdb_overrides: dict[str, int] | None = None,
    dry_run: bool = False,
    order: str = "oldest",
    tag: str = IMPORT_TAG,
) -> None:
    """Entry point for the CSV import."""
    print("Source: CSV")
    print(f"Tag: {tag}")
    if tmdb_overrides:
        print(f"TMDB overrides: {tmdb_overrides}")
    print()

    print(f"Parsing {csv_path}...")
    episodes = parse_csv(csv_path)
    print(f"Parsed {len(episodes)} episodes")
    print()

    importer = CsvImporter(import_tag=tag, tmdb_overrides=tmdb_overrides)
    importer.import_episodes(episodes, dry_run=dry_run, order=order)
