import logging

from typing import Any, Callable

from ..exceptions import ValidationError
from ..spec import Spec
from .parsers import DEFAULT_PARSERS
from .validators import SchemaValidator

logger = logging.getLogger(__name__)


class SchemaUnmarshaller:
    def __init__(
        self, spec: Spec, parsers: dict[str, Callable[[Any], Any]] | None = None
    ):
        if parsers is None:
            self.parsers = DEFAULT_PARSERS
        else:
            self.parsers = parsers

        self._validator = SchemaValidator(parsers=self.parsers)
        self._unmarshalers = {
            "array": self._unmarshal_array,
            "object": self._unmarshal_object,
        }

    def unmarshal(self, value: Any, schema: dict) -> Any:
        self._validator.validate(value, schema)
        return self._unmarshal(value, schema)

    def _unmarshal(self, value: Any, schema: dict) -> Any:
        if value is None:
            # Support nullable value
            return value

        if "allOf" in schema:
            # `value` should be a dict
            result = value.copy()  # shallow copy
            for sub_schema in schema["allOf"]:
                # Each sub schema type should be a object,
                # and `unmarshaled` should be a dict.
                #
                # If multiple sub schemas define same property, latter wins.
                unmarshaled = self._unmarshal(value, sub_schema)
                result.update(unmarshaled)
            return result

        for sub_schema in schema.get("oneOf") or schema.get("anyOf") or []:
            try:
                # TODO: Remove duplicate validation
                return self.unmarshal(value, sub_schema)
            except ValidationError:
                pass

        try:
            handler = self._unmarshalers[schema["type"]]
        except KeyError:
            handler = self._unmarshal_atom
        return handler(value, schema)

    def _unmarshal_array(self, value: list, schema: dict) -> list:
        return [self._unmarshal(x, schema["items"]) for x in value]

    def _unmarshal_object(self, value: dict, schema: dict) -> dict:
        result = {}
        if "properties" in schema:
            for k, sub_schema in schema["properties"].items():
                if k in value:
                    sub_value = value[k]
                elif "default" in sub_schema:
                    sub_value = sub_schema["default"]
                else:
                    continue  # pragma: no cover
                result[k] = self._unmarshal(sub_value, sub_schema)
        return result

    def _unmarshal_atom(self, value: Any, schema: dict) -> Any:
        try:
            parser = self.parsers[schema["format"]]
        except KeyError:
            return value
        else:
            return parser(value)
