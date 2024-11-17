import pytest
from unittest.mock import MagicMock
import falcon
from falcon_oas.problems import (
    Problem,
    serialize_problem,
    http_error_handler,
    unmarshal_error_handler,
)
from falcon_oas.oas.exceptions import UnmarshalError


def test_problem_initialization():
    problem = Problem(
        status=falcon.HTTP_400,
        title="Bad Request",
        description="Invalid input",
        headers={"X-Test": "Header"},
        code=123,
        additional_members={"extra": "info"},
    )

    assert problem.status == falcon.HTTP_400
    assert problem.title == "Bad Request"
    assert problem.description == "Invalid input"
    assert problem.headers == {"X-Test": "Header"}
    assert problem.code == 123
    assert problem.additional_members == {"extra": "info"}


def test_problem_from_http_error():
    error = falcon.HTTPError(
        status=falcon.HTTP_404,
        title="Not Found",
        description="Resource not found",
        headers={"X-Header": "Test"},
        code=404,
    )
    problem = Problem.from_http_error(error)

    assert problem.status == falcon.HTTP_404
    assert problem.title == "Not Found"
    assert problem.description == "Resource not found"
    assert problem.headers == {"X-Header": "Test"}
    assert problem.code == 404


def test_problem_to_dict():
    problem = Problem(
        status=falcon.HTTP_400,
        title="Bad Request",
        description="Invalid input",
        code=400,
        additional_members={"extra": "data"},
    )
    result = problem.to_dict()

    assert result["title"] == "Bad Request"
    assert result["status"] == 400
    assert result["detail"] == "Invalid input"
    assert result["code"] == 400
    assert result["extra"] == "data"


def test_serialize_problem():
    req = MagicMock(spec=falcon.Request)
    resp = MagicMock(spec=falcon.Response)
    req.client_prefers.return_value = "application/json"

    error = Problem(
        status=falcon.HTTP_400, title="Bad Request", description="Invalid input"
    )

    serialize_problem(req, resp, error)

    req.client_prefers.assert_called_once_with(
        ("application/json", "application/problem+json")
    )
    assert resp.data == str(error.to_json()).encode("utf-8")
    assert resp.content_type == "application/json"
    resp.append_header.assert_called_once_with("Vary", "Accept")


def test_http_error_handler():
    req = MagicMock(spec=falcon.Request)
    resp = MagicMock(spec=falcon.Response)
    error = falcon.HTTPError(
        status=falcon.HTTP_404, title="Not Found", description="Resource not found"
    )

    with pytest.raises(Problem) as excinfo:
        http_error_handler(req, resp, error, {})

    assert excinfo.value.status == falcon.HTTP_404
    assert excinfo.value.title == "Not Found"
    assert excinfo.value.description == "Resource not found"


def test_unmarshal_error_handler():
    req = MagicMock(spec=falcon.Request)
    resp = MagicMock(spec=falcon.Response)
    error = UnmarshalError(
        parameters_error=MagicMock(
            to_dict=lambda obj_type: {"parameters_error": "Invalid parameters"}
        ),
        request_body_error=MagicMock(
            to_dict=lambda obj_type: {"request_body_error": "Invalid request body"}
        ),
    )

    with pytest.raises(Problem) as excinfo:
        unmarshal_error_handler(req, resp, error, {})

    assert excinfo.value.status == falcon.HTTP_BAD_REQUEST
    assert excinfo.value.title == "Unmarshal Error"
    assert excinfo.value.additional_members == {
        "parameters_error": "Invalid parameters",
        "request_body_error": "Invalid request body",
    }
