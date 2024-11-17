import logging
import falcon
from typing import Any, Callable, Generic, TypeVar, Optional, Dict

from ..oas.exceptions import UndocumentedMediaType, UndocumentedRequest
from ..oas.request import Request
from ..oas.spec import Spec
from ..utils import cached_property

logger = logging.getLogger(__name__)

T = TypeVar("T")


class _Indexer(Generic[T]):
    def __init__(self, getter: Callable[[str, Optional[bool]], Optional[T]]):
        self.getter: Callable[[str, Optional[bool]], Optional[T]] = getter

    def __getitem__(self, key: str) -> T:
        result = self.getter(key, True)
        if result is None:
            raise KeyError(key)
        return result

    def get(self, key: str, default: Optional[T] = None) -> Optional[T]:
        return self.getter(key) or default


class _RequestAdapter(Request):
    def __init__(self, req: falcon.Request, params: Dict[str, Any]):
        self.req: falcon.Request = req
        self.params: Dict[str, Any] = params

    @property
    def uri_template(self) -> Optional[str]:
        return self.req.uri_template

    @property
    def method(self) -> str:
        return self.req.method.lower()

    @cached_property
    def parameters(self) -> Dict[str, Any]:
        return {
            "query": self.req.params,
            "header": _Indexer(self.req.get_header),
            "path": self.params,
            "cookie": self.req.cookies,
        }

    @property
    def media_type(self) -> Optional[str]:
        content_type = self.req.content_type
        return content_type.split(";", 1)[0] if content_type else None

    def get_media(self) -> Any:
        return self.req.media


class OperationMiddleware:
    def __init__(self, spec: Spec):
        self.spec: Spec = spec

    def process_resource(
        self,
        req: falcon.Request,
        resp: falcon.Response,
        resource: Any,
        params: Dict[str, Any],
    ) -> None:
        oas_req = _RequestAdapter(req, params)

        try:
            operation = self.spec.get_operation(
                oas_req.uri_template, oas_req.method, oas_req.media_type
            )
        except UndocumentedMediaType:
            logger.warning(
                "Undocumented media type: %s %s (%s)",
                req.method,
                req.path,
                req.content_type,
            )
            raise falcon.HTTPBadRequest()
        except UndocumentedRequest:
            logger.info(
                "Undocumented request: %s %s (%s)",
                req.method,
                req.path,
                req.content_type,
            )
            operation = None

        req.context["oas._operation"] = operation
        req.context["oas._request"] = oas_req
