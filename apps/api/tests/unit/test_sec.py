from datetime import date

from app.providers.sec import latest_fact_as_of


def test_sec_fact_selection_excludes_future_filings_and_prefers_amendment() -> None:
    facts = [
        {"form": "10-Q", "filed": "2024-05-01", "end": "2024-03-31", "accn": "a", "val": 10},
        {"form": "10-Q/A", "filed": "2024-05-15", "end": "2024-03-31", "accn": "b", "val": 12},
        {"form": "10-Q", "filed": "2024-08-01", "end": "2024-06-30", "accn": "c", "val": 99},
    ]
    selected = latest_fact_as_of(facts, date(2024, 6, 1))
    assert selected is not None
    assert selected["val"] == 12
