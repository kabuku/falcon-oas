import datetime
import functools

from typing import Any, Callable


def parse_int(value: str, min_int: int, max_int: int) -> int:
    n = int(value)
    if not (min_int <= n <= max_int):
        raise ValueError(
            "Must be between {} and {}: {!r}".format(min_int, max_int, value)
        )
    return n


def parse_date(value: str) -> datetime.date:
    return datetime.datetime.strptime(value, "%Y-%m-%d").date()


DEFAULT_PARSERS: dict[str, Callable[[Any], Any]] = {
    "int32": functools.partial(parse_int, min_int=-(2**31), max_int=2**31 - 1),
    "int64": functools.partial(parse_int, min_int=-(2**63), max_int=2**63 - 1),
    "date": parse_date,
}


def raises(error: Any) -> Callable[[Callable], Callable]:
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            # type: (*Any, **Any) -> Any
            try:
                return f(*args, **kwargs)
            except error as e:
                raise ValueError(e)

        return wrapper

    return decorator


try:
    import pyrfc3339
except ImportError:  # pragma: no cover
    pyrfc3339 = None
else:

    def _parse_date_time(value: str) -> datetime.datetime:
        return pyrfc3339.parse(value, utc=True).replace(tzinfo=None)

    DEFAULT_PARSERS["date-time"] = _parse_date_time

try:
    import rfc3986
except ImportError:  # pragma: no cover
    rfc3986 = None
else:

    @raises(rfc3986.exceptions.RFC3986Exception)
    def parse_uri(value: str) -> str:
        uri = rfc3986.uri_reference(value)
        validator = rfc3986.validators.Validator().require_presence_of("scheme", "host")
        validator.validate(uri)
        return value

    DEFAULT_PARSERS["uri"] = parse_uri
