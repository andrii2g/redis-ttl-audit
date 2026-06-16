from redis_ttl_audit.formatting import format_int, format_percent, format_seconds


def test_format_int() -> None:
    assert format_int(8200000) == "8,200,000"


def test_format_percent() -> None:
    assert format_percent(65.856) == "65.86%"


def test_format_seconds() -> None:
    assert format_seconds(891) == "891s"


def test_format_seconds_zero() -> None:
    assert format_seconds(0) == "0s"


def test_format_seconds_none() -> None:
    assert format_seconds(None) == "-"
