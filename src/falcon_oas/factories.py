import falcon
from typing import Type

from .middlewares.operation import OperationMiddleware
from .middlewares.request_unmarshal import RequestUnmarshalMiddleware
from .middlewares.security import SecurityMiddleware, get_security_schemes
from .oas.exceptions import UnmarshalError
from .oas.schema.unmarshalers import SchemaUnmarshaller
from .oas.spec import Spec, create_spec_from_dict
from .problems import (
    http_error_handler,
    serialize_problem,
    unmarshal_error_handler,
)
from .request import Request
from .routing import generate_routes


def create_api(
    spec_dict: dict,
    base_uri: str | None = None,
    middlewares: list | None = None,
    parsers: dict | None = None,
    base_module: str = "",
    base_path: str | None = None,
    request_type: Type[falcon.Request] = Request,
) -> falcon.App:
    spec = create_spec_from_dict(spec_dict, base_uri=base_uri, base_path=base_path)

    default_middlewares = create_default_middlewares(
        spec, parsers=parsers, base_module=base_module
    )
    if middlewares is not None:
        default_middlewares.extend(middlewares)

    api = falcon.App(middleware=default_middlewares, request_type=request_type)
    api.req_options.auto_parse_qs_csv = False
    api.add_error_handler(falcon.HTTPError, http_error_handler)
    api.add_error_handler(UnmarshalError, unmarshal_error_handler)
    api.set_error_serializer(serialize_problem)

    for uri_template, resource_class in generate_routes(spec, base_module=base_module):
        api.add_route(uri_template, resource_class())
    return api


def create_default_middlewares(
    spec: Spec, parsers: dict | None = None, base_module: str = ""
) -> list:
    return [
        OperationMiddleware(spec),
        create_security_middleware(spec, base_module=base_module),
        create_request_unmarshal_middleware(spec, parsers=parsers),
    ]


def create_security_middleware(spec: Spec, base_module: str = "") -> SecurityMiddleware:
    security_schemes = get_security_schemes(spec, base_module=base_module)
    return SecurityMiddleware(security_schemes)


def create_request_unmarshal_middleware(
    spec: Spec, parsers: dict | None = None
) -> RequestUnmarshalMiddleware:
    schema_unmarshaler = SchemaUnmarshaller(spec, parsers=parsers)
    return RequestUnmarshalMiddleware(schema_unmarshaler)
