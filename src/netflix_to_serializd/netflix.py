from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable


@dataclass(frozen=True)
class ViewingEntry:
    title: str
    watched_on: date


def parse_viewing_activity_csv(rows: Iterable[dict[str, str]]) -> list[ViewingEntry]:
    out: list[ViewingEntry] = []
    for r in rows:
        title = (r.get("Title") or "").strip()

        # Netflix CSV has "Start Time" column with format "YYYY-MM-DD HH:MM:SS"
        # Older exports might have "Date" column with format "YYYY-MM-DD"
        date_str = (r.get("Start Time") or r.get("Date") or "").strip()

        if not title or not date_str:
            continue

        # Parse datetime and extract date
        # Handle both "YYYY-MM-DD HH:MM:SS" and "YYYY-MM-DD" formats
        if " " in date_str:
            # Has time component
            watched_on = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").date()
        else:
            # Date only
            watched_on = date.fromisoformat(date_str)

        out.append(ViewingEntry(title=title, watched_on=watched_on))
    return out


def read_viewing_activity_csv(path: str) -> list[ViewingEntry]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return parse_viewing_activity_csv(reader)
