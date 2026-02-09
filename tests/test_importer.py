from datetime import date
from netflix_to_serializd.importer import import_entries
from netflix_to_serializd.netflix import ViewingEntry


def test_import_entries_counts_without_network():
    class FakeClient:
        pass

    entries = [ViewingEntry("Test Show", date(2025, 1, 1))]
    assert import_entries(FakeClient(), entries) == 1
