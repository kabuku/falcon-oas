from datetime import date

import pytest
from falcon_oas.oas.schema.unmarshalers import SchemaUnmarshaller
from falcon_oas.oas.exceptions import ValidationError
from falcon_oas.oas.spec import Spec
from falcon_oas.oas.schema.parsers import DEFAULT_PARSERS


@pytest.fixture
def mock_spec():
    return Spec({}, ".")


@pytest.fixture
def unmarshaller(mock_spec):
    return SchemaUnmarshaller(spec=mock_spec, parsers=DEFAULT_PARSERS)


@pytest.mark.parametrize(
    "value, schema, expected",
    [
        (123, {"type": "integer", "format": "int32"}, 123),
        ("2023-01-01", {"type": "string", "format": "date"}, date(2023, 1, 1)),
    ],
)
def test_unmarshal_atom_with_parsers(unmarshaller, value, schema, expected):
    assert unmarshaller.unmarshal(value, schema) == expected


def test_unmarshal_array(unmarshaller):
    value = [123, 456]
    schema = {"type": "array", "items": {"type": "integer", "format": "int32"}}
    assert unmarshaller.unmarshal(value, schema) == [123, 456]


def test_unmarshal_object_with_properties(unmarshaller):
    value = {"name": "Alice"}
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer", "default": 30},
        },
    }
    result = unmarshaller.unmarshal(value, schema)
    assert result == {"name": "Alice", "age": 30}


def test_unmarshal_allof(unmarshaller):
    value = {"name": "Alice", "age": 25}
    schema = {
        "allOf": [
            {"type": "object", "properties": {"name": {"type": "string"}}},
            {"type": "object", "properties": {"age": {"type": "integer"}}},
        ]
    }
    result = unmarshaller.unmarshal(value, schema)
    assert result == {"name": "Alice", "age": 25}


# `oneOf` を使用したアンマーシャリングをテスト
def test_unmarshal_oneof(unmarshaller):
    value = 123
    schema = {
        "oneOf": [
            {"type": "string", "format": "uuid"},
            {"type": "integer", "format": "int32"},
        ]
    }
    result = unmarshaller.unmarshal(value, schema)
    assert result == 123


def test_unmarshal_anyof(unmarshaller):
    value = 1
    schema = {"anyOf": [{"type": "integer"}, {"type": "boolean"}]}
    result = unmarshaller.unmarshal(value, schema)
    assert result == 1


# def test_unmarshal_fallback_to_atom(unmarshaller):
#     value = "123"
#     schema = {"type": "unknown"}
#     result = unmarshaller.unmarshal(value, schema)
#     assert result == value  # 値はそのまま返される


def test_unmarshal_nullable_value(unmarshaller):
    value = None
    schema = {"type": "integer", "nullable": True}
    result = unmarshaller.unmarshal(value, schema)
    assert result is None


# 無効な値のバリデーションエラーハンドリングをテスト
def test_unmarshal_validation_error(unmarshaller):
    value = "invalid"
    schema = {"type": "integer"}
    with pytest.raises(ValidationError):
        unmarshaller.unmarshal(value, schema)
