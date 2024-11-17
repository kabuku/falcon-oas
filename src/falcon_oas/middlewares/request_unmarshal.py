import falcon
from typing import Any

from ..oas.exceptions import ParametersError, RequestBodyError, UnmarshalError
from ..oas.parameters.unmarshalers import ParametersUnmarshaler
from ..oas.request_body import RequestBodyUnmarshaler
from ..oas.schema.unmarshalers import SchemaUnmarshaller


class RequestUnmarshalMiddleware:
    def __init__(self, schema_unmarshaler: SchemaUnmarshaller):
        self.parameters_unmarshaler = ParametersUnmarshaler(schema_unmarshaler)
        self.request_body_unmarshaler = RequestBodyUnmarshaler(schema_unmarshaler)

    def process_resource(
        self, req: falcon.Request, resp: falcon.Response, resource: Any, params: dict
    ):
        operation = req.context["oas._operation"]
        if operation is None:
            return

        parameters_error = None
        request_body_error = None

        oas_req = req.context["oas._request"]
        try:
            parameters = self.parameters_unmarshaler.unmarshal(
                oas_req.parameters, operation["parameters"]
            )
        except ParametersError as e:
            parameters_error = e
        else:
            req.context["oas.parameters"] = parameters
            if "path" in parameters:
                params.update(parameters["path"])

        if "requestBody" in operation:
            try:
                request_body = self.request_body_unmarshaler.unmarshal(
                    oas_req.get_media,
                    oas_req.media_type,
                    operation["requestBody"],
                )
            except RequestBodyError as e:
                request_body_error = e
            else:
                req.context["oas.request_body"] = request_body

        if parameters_error or request_body_error:
            raise UnmarshalError(parameters_error, request_body_error)
