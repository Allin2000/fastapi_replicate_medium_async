import datetime

from app.core.date import convert_datetime_to_realworld


def test_convert_datetime_to_realworld_returns_utc_isoformat():
    dt = datetime.datetime(2025, 1, 2, 15, 4, 5)
    result = convert_datetime_to_realworld(dt)
    assert result == "2025-01-02T15:04:05Z"


def test_convert_datetime_preserves_timezone_and_always_utc_format():
    dt = datetime.datetime(2025, 1, 2, 15, 4, 5, tzinfo=datetime.timezone(datetime.timedelta(hours=8)))
    result = convert_datetime_to_realworld(dt)
    assert result == "2025-01-02T15:04:05Z"
