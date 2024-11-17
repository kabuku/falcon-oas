from collections import OrderedDict
import falcon
from typing import Callable, MutableMapping, NoReturn, Self

from .oas.exceptions import UnmarshalError


class Problem(falcon.HTTPError):
    def __init__(
        self,
        status: str,
        title: str | None = None,
        description: str | None = None,
        headers: dict | list | None = None,
        code: int | None = None,
        additional_members: dict | list | None = None,
    ) -> None:
        if title == status:
            title = status[4:]

        super().__init__(
            status,
            title=title,
            description=description,
            headers=headers,
            code=code,
        )
        self.additional_members = additional_members

    @classmethod
    def from_http_error(cls, error: falcon.HTTPError) -> Self:
        return cls(
            error.status,
            title=error.title,
            description=error.description,
            headers=error.headers,
            code=error.code,
        )

    def to_dict(self, obj_type: Callable[[], MutableMapping] = dict) -> MutableMapping:
        obj = obj_type()
        obj["title"] = self.title
        obj["status"] = int(self.status[:3])
        if self.description is not None:
            obj["detail"] = self.description
        if self.additional_members is not None:
            obj.update(obj_type(self.additional_members))
        if self.code is not None:
            obj["code"] = self.code
        return obj


def serialize_problem(
    req: falcon.Request, resp: falcon.Response, error: falcon.HTTPError
) -> None:
    """Serialize the given instance of Problem."""
    preferred = req.client_prefers(("application/json", "application/problem+json"))
    if preferred is None:
        preferred = "application/json"

    resp.data = error.to_json()
    resp.content_type = preferred
    resp.append_header("Vary", "Accept")


def http_error_handler(
    req: falcon.Request,
    resp: falcon.Response,
    error: falcon.HTTPError,
    params: dict,
) -> NoReturn:
    raise Problem.from_http_error(error)


def unmarshal_error_handler(
    req: falcon.Request,
    resp: falcon.Response,
    error: UnmarshalError,
    params: dict,
) -> NoReturn:
    raise Problem(
        falcon.HTTP_BAD_REQUEST,
        title="Unmarshal Error",
        additional_members=error.to_dict(obj_type=OrderedDict),
    )
