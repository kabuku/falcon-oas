import pytest
from unittest.mock import patch
from falcon_oas.oas.parameters.deserializers import (
    deserialize_parameter,
    _deserialize_boolean,
)


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        (False, False),
        ("true", True),
        ("false", False),
        ("1", True),
        ("0", False),
        (1, True),
        (0, False),
    ],
)
def test__deserialize_boolean(value, expected):
    # Test the `_deserialize_boolean` function directly
    assert _deserialize_boolean(value) == expected


@pytest.mark.parametrize(
    "value, schema, expected",
    [
        ("123", {"type": "integer"}, 123),
        ("123.45", {"type": "number"}, 123.45),
        ("true", {"type": "boolean"}, True),
        ("false", {"type": "boolean"}, False),
        ("hello", {"type": "string"}, "hello"),
    ],
)
def test_deserialize_parameter_valid_types(value, schema, expected):
    # Test deserialization with valid schema types
    assert deserialize_parameter(value, schema) == expected


@pytest.mark.parametrize(
    "value, schema",
    [
        ("invalid_int", {"type": "integer"}),
        ("invalid_float", {"type": "number"}),
    ],
)
def test_deserialize_parameter_invalid_values(value, schema):
    # Test deserialization when value does not match the schema type
    assert (
        deserialize_parameter(value, schema) == value
    )  # Expect the original value returned


def test_deserialize_parameter_missing_type():
    # Test behavior when schema has no 'type' key
    with patch("falcon_oas.oas.parameters.deserializers.logger") as mock_logger:
        result = deserialize_parameter("value", {})
        assert result == "value"
        mock_logger.warning.assert_called_once_with("Missing parameter schema type")


def test_deserialize_parameter_unsupported_type():
    # Test behavior with unsupported schema type
    with patch("falcon_oas.oas.parameters.deserializers.logger") as mock_logger:
        result = deserialize_parameter("value", {"type": "unsupported"})
        assert result == "value"
        mock_logger.warning.assert_called_once_with(
            "Unsupported parameter schema type: %r", "unsupported"
        )
