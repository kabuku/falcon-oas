import logging
from collections import defaultdict

from typing import Any

from ..exceptions import (
    MissingParameter,
    ParameterError,
    ParametersError,
    ValidationError,
)
from ..schema.unmarshalers import SchemaUnmarshaller
from .deserializers import deserialize_parameter

logger = logging.getLogger(__name__)


class ParametersUnmarshaler:
    def __init__(self, unmarshaler: SchemaUnmarshaller):
        self.unmarshaler = unmarshaler

    def unmarshal(self, values: dict, parameters: list[dict]) -> Any:
        unmarshaled = defaultdict(dict)
        errors: list[ParameterError] = []

        for parameter_spec_dict in parameters:
            name = parameter_spec_dict["name"]
            location = parameter_spec_dict["in"]
            schema = parameter_spec_dict.get("schema", {})

            try:
                value = self._get_value(values, location, name, schema)
            except KeyError:
                if parameter_spec_dict.get("required", False):
                    logger.warning("Missing parameter %r in %r", name, location)
                    errors.append(MissingParameter(name, location))
            else:
                try:
                    value = self._unmarshal(value, schema)
                except ValidationError as e:
                    logger.warning(
                        "Failed to unmarshal parameter %r with %r",
                        value,
                        schema,
                        exc_info=True,
                    )
                    errors.append(ParameterError(name, location, e.errors))
                else:
                    unmarshaled[location][name] = value

        if errors:
            raise ParametersError(errors)
        return unmarshaled

    def _unmarshal(self, value: Any, schema: dict) -> Any:
        value = deserialize_parameter(value, schema)
        value = self.unmarshaler.unmarshal(value, schema)
        return value

    def _get_value(self, values: dict, location: str, name: str, schema: dict) -> Any:
        try:
            return values[location][name]
        except KeyError:
            # TODO: Support allOf, anyOf and oneOf
            return schema["default"]
