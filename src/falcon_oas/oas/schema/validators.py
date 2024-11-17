from jsonschema import Draft4Validator, FormatChecker, validators
from typing import (
    Any,
    Callable,
    Iterable,
    Mapping,
)

from ..exceptions import ValidationError
from .parsers import DEFAULT_PARSERS

_type_draft4_validator = Draft4Validator.VALIDATORS["type"]


def _type_validator(
    validator: Any, types: Any, instance: Any, schema: dict
) -> Iterable:
    if instance is None and schema.get("nullable"):
        return

    for error in _type_draft4_validator(validator, types, instance, schema):
        yield error


_Validator = validators.extend(Draft4Validator, {"type": _type_validator})


class SchemaValidator:
    def __init__(self, parsers: dict | None = None):
        self.format_checker = _create_format_checker_from_parsers(parsers)

    def validate(self, instance: Any, schema: Mapping) -> None:
        validator = _Validator(schema, format_checker=self.format_checker)
        errors = list(validator.iter_errors(instance))
        if errors:
            raise ValidationError(errors)


def _create_format_checker_from_parsers(
    parsers: dict[str, Callable[[Any], Any]] | None = None,
):
    if parsers is None:
        parsers = DEFAULT_PARSERS

    format_checker = FormatChecker(formats=())
    for format_, parser in parsers.items():
        checker = _to_checker(parser)
        format_checker.checks(format_, raises=ValueError)(checker)

    return format_checker


def _to_checker(parser: Callable[[Any], Any]) -> Callable[[Any], bool | Any]:
    def checker(instance: Any) -> bool | Any:
        if not isinstance(instance, str):
            return True
        return parser(instance)

    return checker
