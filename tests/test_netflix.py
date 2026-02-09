from netflix_to_serializd.netflix import parse_viewing_activity_csv


def test_parses_basic_rows():
    rows = [
        {"Title": "Breaking Bad: Season 1: Pilot", "Date": "2025-01-02"},
        {"Title": "Some Film", "Date": "2025-01-03"},
    ]
    entries = parse_viewing_activity_csv(rows)

    assert len(entries) == 2
    assert entries[0].title.startswith("Breaking Bad")
    assert entries[0].watched_on.isoformat() == "2025-01-02"
