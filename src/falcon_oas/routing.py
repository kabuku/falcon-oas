from typing import Any, Iterable

from .extensions import FALCON_OAS_IMPLEMENTOR
from .oas.spec import Spec
from .utils import import_class_or_function


def generate_routes(spec: Spec, base_module: str = "") -> Iterable[tuple[str, Any]]:
    for path, path_item in spec.spec_dict["paths"].items():
        try:
            resource_name = path_item[FALCON_OAS_IMPLEMENTOR]
        except KeyError:
            pass
        else:
            resource_class = import_class_or_function(
                resource_name, base_module=base_module
            )
            yield spec.base_path + path, resource_class
