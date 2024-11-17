from collections.abc import Callable, MutableMapping, Sequence
from typing import List, Optional, Union
import jsonschema


class _Error(Exception):
    pass


class UndocumentedRequest(_Error):
    pass


class UndocumentedMediaType(UndocumentedRequest):
    pass


class ValidationError(_Error):
    def __init__(self, errors: List[jsonschema.ValidationError]) -> None:
        self.errors = errors
        super().__init__(repr(self))

    def __repr__(self) -> str:
        return repr([repr(error) for error in self.errors])


class ParametersError(_Error):
    def __init__(self, errors: Sequence["ParameterError"]) -> None:
        super().__init__()
        self.errors = errors

    def to_dict(self, obj_type: Callable[[], MutableMapping] = dict) -> MutableMapping:
        parameters = obj_type()
        for error in self.errors:
            error_dict = error.to_dict(obj_type=obj_type)
            if error.location not in parameters:
                parameters.update(error_dict)
            else:
                parameters[error.location].extend(error_dict[error.location])
        obj = obj_type()
        obj["parameters"] = parameters
        return obj


class ParameterError(_Error):
    def __init__(
        self,
        name: str,
        location: str,
        errors: Sequence[Union["_ValidationError", jsonschema.ValidationError]],
    ) -> None:
        super().__init__()
        self.name = name
        self.location = location
        self.errors = errors

    def to_dict(self, obj_type: Callable[[], MutableMapping] = dict) -> MutableMapping:
        obj = obj_type()
        obj[self.location] = [
            self._error_to_dict(error, obj_type) for error in self.errors
        ]
        return obj

    def _error_to_dict(
        self,
        error: Union["_ValidationError", jsonschema.ValidationError],
        obj_type: Callable[[], MutableMapping],
    ) -> MutableMapping:
        obj = obj_type()
        obj["name"] = self.name
        obj.update(_error_to_dict(error, obj_type))
        return obj


class RequestBodyError(_Error):
    def __init__(
        self, errors: Sequence[Union["_ValidationError", jsonschema.ValidationError]]
    ) -> None:
        super().__init__()
        self.errors = errors

    def to_dict(self, obj_type: Callable[[], MutableMapping] = dict) -> MutableMapping:
        obj = obj_type()
        obj["request_body"] = [_error_to_dict(error, obj_type) for error in self.errors]
        return obj


class UnmarshalError(_Error):
    def __init__(
        self,
        parameters_error: Optional[ParametersError] = None,
        request_body_error: Optional[RequestBodyError] = None,
    ) -> None:
        super().__init__()
        self.parameters_error = parameters_error
        self.request_body_error = request_body_error

    def to_dict(self, obj_type: Callable[[], MutableMapping] = dict) -> MutableMapping:
        obj = obj_type()
        if self.parameters_error is not None:
            obj.update(self.parameters_error.to_dict(obj_type=obj_type))
        if self.request_body_error is not None:
            obj.update(self.request_body_error.to_dict(obj_type=obj_type))
        return obj


class _ValidationError:
    path: List[str] = []
    validator: Optional[str] = None
    message: Optional[str] = None


class MissingParameter(ParameterError):
    def __init__(self, name: str, location: str) -> None:
        class _MissingParameter(_ValidationError):
            validator = "required"
            message = "parameter is required"

        errors = [_MissingParameter()]
        super().__init__(name, location, errors)


class MissingRequestBody(RequestBodyError):
    def __init__(self, media_type: str) -> None:
        class _MissingRequestBody(_ValidationError):
            validator = "required"
            message = "request body is required"

        super().__init__([_MissingRequestBody()])
        self.media_type = media_type


def _error_to_dict(
    error: Union[_ValidationError, jsonschema.ValidationError],
    obj_type: Callable[[], MutableMapping] = dict,
) -> MutableMapping:
    obj = obj_type()
    obj["path"] = list(error.path)
    obj["validator"] = error.validator
    obj["message"] = error.message
    return obj
