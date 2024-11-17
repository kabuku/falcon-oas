import pytest
from falcon_oas.oas.schema.parsers import parse_int, parse_date, DEFAULT_PARSERS, raises
import datetime


# Tests for `parse_int`
@pytest.mark.parametrize(
    "value, min_int, max_int, expected",
    [
        ("123", 0, 200, 123),
        ("0", -10, 10, 0),
        ("-5", -10, 10, -5),
    ],
)
def test_parse_int_valid(value, min_int, max_int, expected):
    assert parse_int(value, min_int, max_int) == expected


@pytest.mark.parametrize(
    "value, min_int, max_int",
    [
        ("123", 0, 100),
        ("-11", -10, 10),
        ("201", 0, 200),
    ],
)
def test_parse_int_out_of_range(value, min_int, max_int):
    with pytest.raises(ValueError, match=r"Must be between"):
        parse_int(value, min_int, max_int)


# Tests for `parse_date`
@pytest.mark.parametrize(
    "value, expected",
    [
        ("2023-01-01", datetime.date(2023, 1, 1)),
        ("1999-12-31", datetime.date(1999, 12, 31)),
    ],
)
def test_parse_date(value, expected):
    assert parse_date(value) == expected


def test_parse_date_invalid():
    with pytest.raises(ValueError):
        parse_date("invalid-date")


# Tests for `raises` decorator
def test_raises_decorator():
    @raises(ValueError)
    def test_func():
        raise ValueError("Test error")

    with pytest.raises(ValueError, match="Test error"):
        test_func()

    @raises(KeyError)
    def test_func_keyerror():
        raise KeyError("Key error")

    with pytest.raises(ValueError, match="Key error"):
        test_func_keyerror()


# Tests for DEFAULT_PARSERS
def test_default_parsers_int32():
    parser = DEFAULT_PARSERS["int32"]
    assert parser("2147483647") == 2147483647  # max int32
    with pytest.raises(ValueError):
        parser("2147483648")  # out of int32 range


def test_default_parsers_int64():
    parser = DEFAULT_PARSERS["int64"]
    assert parser("9223372036854775807") == 9223372036854775807  # max int64
    with pytest.raises(ValueError):
        parser("9223372036854775808")  # out of int64 range


def test_default_parsers_date():
    parser = DEFAULT_PARSERS["date"]
    assert parser("2023-01-01") == datetime.date(2023, 1, 1)
    with pytest.raises(ValueError):
        parser("not-a-date")


# Conditional tests for `date-time` and `uri` parsers if available
def test_default_parsers_datetime():
    if "date-time" in DEFAULT_PARSERS:
        parser = DEFAULT_PARSERS["date-time"]
        assert parser("2023-01-01T12:00:00Z") == datetime.datetime(2023, 1, 1, 12, 0, 0)
        with pytest.raises(ValueError):
            parser("not-a-datetime")


def test_default_parsers_uri():
    if "uri" in DEFAULT_PARSERS:
        parser = DEFAULT_PARSERS["uri"]
        assert parser("http://example.com") == "http://example.com"
        with pytest.raises(ValueError):
            parser("not-a-uri")
