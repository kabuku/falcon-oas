import pytest
from jsonschema.exceptions import FormatError
from falcon_oas.oas.schema.validators import (
    SchemaValidator,
    _create_format_checker_from_parsers,
    _to_checker,
)
from falcon_oas.oas.exceptions import ValidationError
from falcon_oas.oas.schema.parsers import DEFAULT_PARSERS


# Test the SchemaValidator class with nullable type handling
@pytest.mark.parametrize(
    "instance, schema, should_raise",
    [
        (None, {"type": "string", "nullable": True}, False),
        ("valid", {"type": "string", "nullable": True}, False),
        (123, {"type": "string", "nullable": True}, True),  # Not a string
        (None, {"type": "string", "nullable": False}, True),  # Null not allowed
    ],
)
def test_schema_validator_nullable(instance, schema, should_raise):
    validator = SchemaValidator(parsers=DEFAULT_PARSERS)
    if should_raise:
        with pytest.raises(ValidationError):
            validator.validate(instance, schema)
    else:
        validator.validate(instance, schema)  # Should not raise an error


# Test schema validation with format checking
def test_schema_validator_with_format_checker():
    schema = {"type": "string", "format": "date"}
    validator = SchemaValidator(parsers=DEFAULT_PARSERS)

    # Test valid date format
    validator.validate("2023-01-01", schema)  # Should not raise

    # Test invalid date format
    with pytest.raises(ValidationError):
        validator.validate("not-a-date", schema)


# Test _create_format_checker_from_parsers with custom parsers
def test_create_format_checker_with_custom_parser():
    # Create a mock parser
    custom_parsers = {"custom-format": lambda x: x == "valid"}
    format_checker = _create_format_checker_from_parsers(custom_parsers)

    assert format_checker.checks("custom-format")(lambda x: x == "valid")
    # Should not raise for "valid"
    format_checker.check("valid", "custom-format")

    # Invalid format should raise ValueError
    with pytest.raises(FormatError):
        format_checker.check("invalid", "custom-format")


# Test SchemaValidator with extended type validator (e.g., int and nullable)
def test_schema_validator_extended_type():
    schema = {"type": "integer", "nullable": True}
    validator = SchemaValidator(parsers=DEFAULT_PARSERS)

    # Valid cases
    validator.validate(123, schema)  # Integer
    validator.validate(None, schema)  # Nullable

    # Invalid case
    with pytest.raises(ValidationError):
        validator.validate("not-an-integer", schema)


# Test the _to_checker function with various inputs
@pytest.mark.parametrize(
    "input_value, parser, expected",
    [
        ("valid", lambda x: x == "valid", True),
        ("invalid", lambda x: x == "valid", False),
        (123, lambda x: x == "valid", True),  # Non-string values should return True
    ],
)
def test_to_checker(input_value, parser, expected):
    checker = _to_checker(parser)
    assert checker(input_value) == expected
