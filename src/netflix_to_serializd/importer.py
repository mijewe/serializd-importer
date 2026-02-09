from __future__ import annotations
from typing import TYPE_CHECKING

from .netflix import ViewingEntry

if TYPE_CHECKING:
    from serializd import SerializdClient


def import_entries(client: "SerializdClient", entries: list[ViewingEntry]) -> int:
    count = 0
    for e in entries:
        _ = e.title
        count += 1
    return count
