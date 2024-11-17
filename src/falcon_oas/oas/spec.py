import copy
import json
import os.path
from functools import lru_cache

import jsonref
import yaml
from urllib.parse import urlparse

from .exceptions import UndocumentedMediaType, UndocumentedRequest

DEFAULT_SERVER = {"url": "/"}


def create_spec_from_dict(spec_dict, base_uri=None, base_path=None):
    # type: (Dict, Optional[str], Optional[Text]) -> Spec
    deref_spec_dict = jsonref.JsonRef.replace_refs(
        spec_dict, loader=base_uri and _LocalRefLoader(base_uri)
    )
    return Spec(copy.deepcopy(deref_spec_dict), base_path=base_path)


class _LocalRefLoader(object):
    def __init__(self, base_uri):
        # type: (str) -> None
        self.base_uri = base_uri

    def __call__(self, uri):
        # type: (Text) -> Any
        if uri.endswith(".yaml"):
            loader = yaml.safe_load
        else:
            loader = json.loads  # type: ignore

        with open(os.path.join(self.base_uri, uri)) as f:
            return loader(f.read())  # type: ignore


class Spec(object):
    def __init__(self, spec_dict, base_path=None):
        # type: (Dict, Optional[Text]) -> None
        self.spec_dict = spec_dict
        self.base_path = (
            base_path if base_path is not None else get_base_path(spec_dict)
        )
        self._base_security = get_security(spec_dict)

    @lru_cache(maxsize=None)
    def get_operation(self, uri_template, method, media_type):
        # type: (str, str, Optional[str]) -> Optional[Dict]
        if not uri_template.startswith(self.base_path):
            raise UndocumentedRequest()

        path = uri_template[len(self.base_path) :]
        try:
            path_item = self.spec_dict["paths"][path]
            operation = path_item[method]
        except KeyError:
            raise UndocumentedRequest()

        if "requestBody" in operation:
            # TODO: Support media type range
            if media_type not in operation["requestBody"]["content"]:
                raise UndocumentedMediaType()

        result = operation.copy()
        result["parameters"] = list(self._iter_parameters(path_item, result))
        result["security"] = get_security(result, base_security=self._base_security)
        return result

    def get_security_schemes(self):
        # type: () -> Optional[Dict]
        try:
            security_schemes = self.spec_dict["components"]["securitySchemes"]
        except KeyError:
            return None
        else:
            return security_schemes

    def _iter_parameters(self, path_item, operation):
        # type: (Dict, Dict) -> Iterable[Dict]
        seen = set()  # type: Set[Tuple[Text, Text]]
        for spec_dict in (operation, path_item):
            if "parameters" not in spec_dict:
                continue
            for parameter_spec_dict in spec_dict["parameters"]:
                key = (parameter_spec_dict["in"], parameter_spec_dict["name"])
                if key in seen:
                    continue
                seen.add(key)
                yield parameter_spec_dict


def get_base_path(spec_dict):
    # type: (Dict) -> Text
    try:
        server = spec_dict["servers"][0]
    except (KeyError, IndexError):
        server = DEFAULT_SERVER

    return urlparse(server["url"]).path.rstrip("/") or "/"


def get_security(spec_dict, base_security=None):
    # type: (Dict, Optional[List[Dict]]) -> Optional[List[Dict]]
    try:
        return spec_dict["security"]
    except KeyError:
        return base_security
