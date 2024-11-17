import pytest
from unittest.mock import MagicMock
import falcon
from falcon_oas.middlewares.security import SecurityMiddleware


@pytest.fixture
def security_schemes():
    return {
        "api_key": (
            {"type": "apiKey", "in": "header", "name": "X-API-Key"},
            lambda value, scopes, req: "user1" if value == "valid_key" else None,
        ),
        "session": (
            {"type": "apiKey", "in": "cookie", "name": "session"},
            lambda value, scopes, req: "user2" if value == "valid_session" else None,
        ),
    }


@pytest.fixture
def middleware(security_schemes):
    return SecurityMiddleware(security_schemes)


@pytest.fixture
def mock_request():
    req = MagicMock(spec=falcon.Request)
    req.context = {
        "oas._operation": {"security": [{"api_key": []}, {"session": []}]},
        "oas._request": MagicMock(
            parameters={
                "header": {"X-API-Key": "valid_key"},
                "cookie": {"session": "invalid_session"},
            }
        ),
    }
    return req


def test_process_resource_security_success(middleware, mock_request):
    req = mock_request
    resp = MagicMock(spec=falcon.Response)
    params = {}

    # 実行
    middleware.process_resource(req, resp, None, params)

    # 検証
    assert "oas.users" in req.context
    assert req.context["oas.users"] == ["user1"]


def test_process_resource_security_fallback(middleware, mock_request):
    req = mock_request
    req.context["oas._request"].parameters["header"]["X-API-Key"] = None
    req.context["oas._request"].parameters["cookie"]["session"] = "valid_session"
    resp = MagicMock(spec=falcon.Response)
    params = {}

    # 実行
    middleware.process_resource(req, resp, None, params)

    # 検証
    assert "oas.users" in req.context
    assert req.context["oas.users"] == ["user2"]


def test_process_resource_security_failure(middleware, mock_request):
    req = mock_request
    req.context["oas._request"].parameters["header"]["X-API-Key"] = "invalid_key"
    req.context["oas._request"].parameters["cookie"]["session"] = "invalid_session"
    resp = MagicMock(spec=falcon.Response)
    params = {}

    # 実行と検証
    with pytest.raises(falcon.HTTPForbidden):
        middleware.process_resource(req, resp, None, params)


def test_process_resource_no_operation(middleware):
    req = MagicMock(spec=falcon.Request)
    req.context = {"oas._operation": None}
    resp = MagicMock(spec=falcon.Response)
    params = {}

    # 実行
    middleware.process_resource(req, resp, None, params)

    # 検証: エラーは発生せず
    assert "oas.users" not in req.context
