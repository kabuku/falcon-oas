import pytest
from unittest.mock import MagicMock
import falcon
from falcon_oas.middlewares.operation import OperationMiddleware
from falcon_oas.oas.spec import create_spec_from_dict


@pytest.fixture
def openapi_spec(petstore_dict):
    return create_spec_from_dict(petstore_dict)


@pytest.fixture
def middleware(openapi_spec):
    return OperationMiddleware(spec=openapi_spec)


@pytest.fixture
def mock_get_request():
    req = MagicMock(spec=falcon.Request)
    req.method = "GET"
    req.path = "/api/v1/pets"
    req.uri_template = "/api/v1/pets"
    req.content_type = "application/json"
    req.params = {"limit": "10"}
    req.get_header = MagicMock(
        side_effect=lambda key, _: {"X-API-Key": "dummy_key"}.get(key)
    )
    req.cookies = {}
    req.context = {}
    req.media = None
    return req


@pytest.fixture
def mock_post_request():
    req = MagicMock(spec=falcon.Request)
    req.method = "POST"
    req.path = "/api/v1/pets"
    req.uri_template = "/api/v1/pets"
    req.content_type = "application/json"
    req.body = b'{"name": "dummy"}'
    req.get_header = MagicMock(
        side_effect=lambda key, _: {"X-API-Key": "dummy_key"}.get(key)
    )
    req.cookies = {}
    req.context = {}
    req.media = None
    return req


def test_process_resource_success(middleware, mock_get_request):
    req = mock_get_request
    resp = MagicMock(spec=falcon.Response)
    params = {}

    middleware.process_resource(req, resp, None, params)

    assert "oas._operation" in req.context
    assert "oas._request" in req.context
    operation = req.context["oas._operation"]
    assert operation is not None


def test_process_resource_undocumented_media_type(middleware, mock_post_request):
    req = mock_post_request
    req.content_type = "application/xml"  # 未サポートのContent-Type
    resp = MagicMock(spec=falcon.Response)
    params = {}

    with pytest.raises(falcon.HTTPBadRequest):
        middleware.process_resource(req, resp, None, params)


def test_process_resource_undocumented_request(middleware, mock_get_request):
    req = mock_get_request
    req.uri_template = "/unknown"
    resp = MagicMock(spec=falcon.Response)
    params = {}

    middleware.process_resource(req, resp, None, params)

    assert "oas._operation" in req.context
    assert "oas._request" in req.context
    operation = req.context["oas._operation"]
    oas_req = req.context["oas._request"]
    assert operation is None
    assert oas_req is not None
