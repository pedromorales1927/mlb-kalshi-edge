from datetime import date

from mlb_kalshi.db.repository import to_json_safe


def test_to_json_safe_converts_dates_in_nested_payload() -> None:
    payload = {
        "prediction_date": date(2026, 6, 14),
        "nested": [{"metric_date": date(2026, 6, 13)}],
    }

    assert to_json_safe(payload) == {
        "prediction_date": "2026-06-14",
        "nested": [{"metric_date": "2026-06-13"}],
    }

