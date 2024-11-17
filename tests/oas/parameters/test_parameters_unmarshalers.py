import pytest
from unittest.mock import MagicMock, patch
from falcon_oas.oas.parameters.unmarshalers import ParametersUnmarshaler
from falcon_oas.oas.exceptions import (
    MissingParameter,
    ParameterError,
    ParametersError,
    ValidationError,
)


@pytest.fixture
def mock_unmarshaler():
    # Mock SchemaUnmarshaller object
    return MagicMock()


@pytest.fixture
def unmarshaler(mock_unmarshaler):
    return ParametersUnmarshaler(unmarshaler=mock_unmarshaler)


@pytest.mark.parametrize(
    "values, parameters, expected",
    [
        (
            {"query": {"param1": "123"}},
            [{"name": "param1", "in": "query", "schema": {"type": "integer"}}],
            {"query": {"param1": 123}},
        ),
        (
            {"header": {"param2": "true"}},
            [{"name": "param2", "in": "header", "schema": {"type": "boolean"}}],
            {"header": {"param2": True}},
        ),
    ],
)
def test_unmarshal_success(unmarshaler, values, parameters, expected):
    # Mock the unmarshal behavior of the SchemaUnmarshaller
    unmarshaler.unmarshaler.unmarshal.side_effect = lambda v, s: v

    # Act
    result = unmarshaler.unmarshal(values, parameters)

    # Assert
    assert result == expected


def test_unmarshal_missing_parameter(unmarshaler):
    parameters = [
        {
            "name": "param1",
            "in": "query",
            "required": True,
            "schema": {"type": "integer"},
        }
    ]
    values = {}

    # Act and Assert
    with patch("falcon_oas.oas.parameters.unmarshalers.logger") as mock_logger:
        with pytest.raises(ParametersError) as excinfo:
            unmarshaler.unmarshal(values, parameters)

        # Check that the error contains MissingParameter
        assert any(isinstance(err, MissingParameter) for err in excinfo.value.errors)
        mock_logger.warning.assert_called_once_with(
            "Missing parameter %r in %r", "param1", "query"
        )


def test_unmarshal_validation_error(unmarshaler):
    # Mock a validation error in the SchemaUnmarshaller
    parameters = [{"name": "param1", "in": "query", "schema": {"type": "integer"}}]
    values = {"query": {"param1": "not_an_integer"}}
    unmarshaler.unmarshaler.unmarshal.side_effect = ValidationError("Invalid integer")

    # Act and Assert
    with patch("falcon_oas.oas.parameters.unmarshalers.logger") as mock_logger:
        with pytest.raises(ParametersError) as excinfo:
            unmarshaler.unmarshal(values, parameters)

        # Check that the error contains ParameterError
        assert any(isinstance(err, ParameterError) for err in excinfo.value.errors)
        mock_logger.warning.assert_called_once_with(
            "Failed to unmarshal parameter %r with %r",
            "not_an_integer",
            {"type": "integer"},
            exc_info=True,
        )


def test_unmarshal_with_default_value(unmarshaler):
    # Test when schema has a default value
    parameters = [
        {"name": "param1", "in": "query", "schema": {"type": "integer", "default": 42}}
    ]
    values = {}

    # Mock unmarshal behavior to return the value as is
    unmarshaler.unmarshaler.unmarshal.side_effect = lambda v, s: v

    # Act
    result = unmarshaler.unmarshal(values, parameters)

    # Assert
    assert result["query"]["param1"] == 42
