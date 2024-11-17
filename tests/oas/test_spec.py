import pytest
from falcon_oas.oas.spec import (
    Spec,
    create_spec_from_dict,
    get_base_path,
    get_security,
    UndocumentedMediaType,
    UndocumentedRequest,
)


@pytest.fixture
def spec_dict():
    return {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "servers": [{"url": "/api"}],
        "paths": {
            "/example": {
                "get": {
                    "responses": {"200": {"description": "Successful response"}},
                    "parameters": [{"in": "query", "name": "param1", "required": True}],
                },
                "post": {
                    "requestBody": {
                        "content": {"application/json": {"schema": {"type": "object"}}}
                    },
                    "responses": {
                        "201": {
                            "description": "Successful creation",
                            "content": {
                                "application/json": {"schema": {"type": "object"}}
                            },
                        },
                        "400": {"description": "Bad request"},
                    },
                },
            }
        },
        "components": {
            "securitySchemes": {
                "apiKeyAuth": {"type": "apiKey", "in": "header", "name": "X-API-Key"}
            }
        },
        "security": [{"apiKeyAuth": []}],
    }


def test_get_base_path(petstore_dict):
    assert get_base_path(petstore_dict) == "/api"
    assert get_base_path({"servers": []}) == "/"
    assert get_base_path({}) == "/"


def test_get_security(spec_dict):
    assert get_security(spec_dict) == [{"apiKeyAuth": []}]
    assert get_security({}, base_security=[{"basicAuth": []}]) == [{"basicAuth": []}]
    assert get_security({}) is None


def test_create_spec_from_dict(petstore_dict):
    spec = create_spec_from_dict(petstore_dict)
    assert isinstance(spec, Spec)
    assert spec.base_path == "/api"


def test_spec_get_operation_success(spec_dict):
    spec = Spec(spec_dict)
    operation = spec.get_operation("/api/example", "get", "application/json")
    assert operation is not None
    assert "parameters" in operation
    assert operation["parameters"][0]["name"] == "param1"
    assert operation["security"] == [{"apiKeyAuth": []}]


def test_spec_get_operation_undocumented_request(spec_dict):
    spec = Spec(spec_dict)
    with pytest.raises(UndocumentedRequest):
        spec.get_operation("/unknown/path", "get", "application/json")


def test_spec_get_operation_undocumented_media_type(spec_dict):
    spec = Spec(spec_dict)

    with pytest.raises(UndocumentedMediaType):
        spec.get_operation("/api/example", "post", "unsupported/media-type")


def test_spec_get_security_schemes(spec_dict):
    spec = Spec(spec_dict)
    security_schemes = spec.get_security_schemes()
    assert security_schemes is not None
    assert "apiKeyAuth" in security_schemes
    assert security_schemes["apiKeyAuth"]["type"] == "apiKey"


def test_spec_iter_parameters(spec_dict):
    spec = Spec(spec_dict)
    path_item = spec_dict["paths"]["/example"]
    operation = path_item["get"]

    parameters = list(spec._iter_parameters(path_item, operation))
    assert len(parameters) == 1
    assert parameters[0]["name"] == "param1"
    assert parameters[0]["in"] == "query"
