import logging
from ...utils import strtobool

from typing import Any, Callable

logger = logging.getLogger(__name__)


def _deserialize_boolean(value: any) -> bool:
    if isinstance(value, bool):
        # bool value may be given as a default property value
        return value
    return bool(strtobool(value))


parameter_deserializers: dict[str, Callable[[Any], Any]] = {
    "integer": int,
    "number": float,
    "boolean": _deserialize_boolean,
    "string": lambda x: x,
}


def deserialize_parameter(value: Any, schema: dict) -> Any:
    try:
        schema_type = schema["type"]
    except KeyError:
        logger.warning("Missing parameter schema type")
        return value

    try:
        deserialize = parameter_deserializers[schema_type]
    except KeyError:
        logger.warning("Unsupported parameter schema type: %r", schema_type)
        return value

    try:
        return deserialize(value)
    except ValueError:
        # Let the validator to handle the type error
        return value
