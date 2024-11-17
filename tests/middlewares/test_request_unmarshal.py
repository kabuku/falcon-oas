import pytest
from unittest.mock import MagicMock, patch
import falcon
from falcon_oas.middlewares.request_unmarshal import RequestUnmarshalMiddleware
from falcon_oas.oas.exceptions import ParametersError, RequestBodyError, UnmarshalError
from falcon_oas.oas.schema.unmarshalers import SchemaUnmarshaller
from falcon_oas.oas.parameters.unmarshalers import ParametersUnmarshaler
from falcon_oas.oas.request_body import RequestBodyUnmarshaler


@pytest.fixture
def mock_schema_unmarshaler():
    return MagicMock(spec=SchemaUnmarshaller)


@pytest.fixture
def middleware(mock_schema_unmarshaler):
    return RequestUnmarshalMiddleware(schema_unmarshaler=mock_schema_unmarshaler)


@pytest.fixture
def mock_request():
    req = MagicMock(spec=falcon.Request)
    req.context = {
        "oas._operation": {
            "parameters": [{"name": "id", "in": "path", "schema": {"type": "integer"}}],
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {"name": {"type": "string"}},
                        }
                    }
                }
            },
        },
        "oas._request": MagicMock(
            parameters={"path": {"id": 123}},
            media_type="application/json",
            get_media=MagicMock(return_value={"name": "test"}),
        ),
    }
    return req


def test_process_resource_success(middleware, mock_request):
    req = mock_request
    resp = MagicMock(spec=falcon.Response)
    params = {}

    with patch.object(
        ParametersUnmarshaler, "unmarshal", return_value={"path": {"id": 123}}
    ):
        with patch.object(
            RequestBodyUnmarshaler, "unmarshal", return_value={"name": "test"}
        ):
            middleware.process_resource(req, resp, None, params)

    # 検証
    assert "oas.parameters" in req.context
    assert "oas.request_body" in req.context
    assert req.context["oas.parameters"] == {"path": {"id": 123}}
    assert req.context["oas.request_body"] == {"name": "test"}
    assert params == {"id": 123}


def test_process_resource_parameters_error(middleware, mock_request):
    req = mock_request
    resp = MagicMock(spec=falcon.Response)
    params = {}

    with patch.object(
        ParametersUnmarshaler,
        "unmarshal",
        side_effect=ParametersError("Invalid parameters"),
    ):
        with pytest.raises(UnmarshalError) as excinfo:
            middleware.process_resource(req, resp, None, params)

    # 検証
    assert isinstance(excinfo.value.parameters_error, ParametersError)
    assert excinfo.value.request_body_error is None


def test_process_resource_request_body_error(middleware, mock_request):
    req = mock_request
    resp = MagicMock(spec=falcon.Response)
    params = {}

    with patch.object(
        ParametersUnmarshaler, "unmarshal", return_value={"path": {"id": 123}}
    ):
        with patch.object(
            RequestBodyUnmarshaler,
            "unmarshal",
            side_effect=RequestBodyError("Invalid body"),
        ):
            with pytest.raises(UnmarshalError) as excinfo:
                middleware.process_resource(req, resp, None, params)

    # 検証
    assert excinfo.value.parameters_error is None
    assert isinstance(excinfo.value.request_body_error, RequestBodyError)


def test_process_resource_no_operation(middleware):
    req = MagicMock(spec=falcon.Request)
    req.context = {"oas._operation": None}
    resp = MagicMock(spec=falcon.Response)
    params = {}

    # 実行
    middleware.process_resource(req, resp, None, params)

    # 検証: 処理がスキップされる
    assert "oas.parameters" not in req.context
    assert "oas.request_body" not in req.context


def test_process_resource_no_request_body(middleware, mock_request):
    req = mock_request
    resp = MagicMock(spec=falcon.Response)
    params = {}

    # `requestBody` を持たないオペレーションをモック
    req.context["oas._operation"].pop("requestBody")

    with patch.object(
        ParametersUnmarshaler, "unmarshal", return_value={"path": {"id": 123}}
    ):
        middleware.process_resource(req, resp, None, params)

    # 検証
    assert "oas.parameters" in req.context
    assert "oas.request_body" not in req.context
    assert req.context["oas.parameters"] == {"path": {"id": 123}}
