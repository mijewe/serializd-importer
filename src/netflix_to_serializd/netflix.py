from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from typing import Iterable


@dataclass(frozen=True)
class ViewingEntry:
    title: str
    watched_on: date


def parse_viewing_activity_csv(rows: Iterable[dict[str, str]]) -> list[ViewingEntry]:
    out: list[ViewingEntry] = []
    for r in rows:
        title = (r.get("Title") or "").strip()
        d = (r.get("Date") or "").strip()
        if not title or not d:
            continue
        # Netflix export typically uses YYYY-MM-DD (but we’ll keep it strict for now)
        out.append(ViewingEntry(title=title, watched_on=date.fromisoformat(d)))
    return out


def read_viewing_activity_csv(path: str) -> list[ViewingEntry]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return parse_viewing_activity_csv(reader)
