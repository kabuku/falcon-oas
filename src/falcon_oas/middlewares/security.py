import logging

import falcon
from typing import Any

from .. import oas
from ..extensions import FALCON_OAS_IMPLEMENTOR
from ..utils import import_class_or_function

logger = logging.getLogger(__name__)


class SecurityMiddleware:
    def __init__(self, security_schemes: dict):
        self.security_schemes = security_schemes

    def process_resource(
        self, req: falcon.Request, resp: falcon.Response, resource: Any, params: dict
    ):
        operation = req.context["oas._operation"]
        if operation is None:
            return

        if self.security_schemes and operation["security"]:
            oas_req = req.context["oas._request"]

            for requirement in operation["security"]:
                users = self._satisfy_requirement(oas_req, requirement)
                if users is not None:
                    if users:
                        req.context["oas.users"] = users
                    return

            logger.warning(
                "No security requirement was satisfied: %r",
                operation["security"],
            )
            # TODO: distinguish unauthorized error from forbidden error
            raise falcon.HTTPForbidden()

    def _satisfy_requirement(
        self, oas_req: oas.Request, requirement: dict
    ) -> list[Any]:
        results = []
        for key, scopes in requirement.items():
            user = self._satisfy_scheme(oas_req, key, scopes)
            if not user:
                return None
            elif user is not True:
                results.append(user)
        return results

    def _satisfy_scheme(self, oas_req: oas.Request, key: str, scopes: list[str]) -> Any:
        try:
            security_scheme, satisfy = self.security_schemes[key]
        except KeyError:
            return True

        if security_scheme["type"] == "apiKey":
            location = security_scheme["in"]
            name = security_scheme["name"]
            value = oas_req.parameters[location].get(name)
            return satisfy(value, scopes, oas_req)

        logger.warning("Unsupported security scheme type: %r", security_scheme["type"])
        return True


def get_security_schemes(spec, base_module: str = "") -> dict:
    security_schemes = spec.get_security_schemes() or {}
    return security_schemes and {
        key: (
            security_scheme,
            import_class_or_function(
                security_scheme[FALCON_OAS_IMPLEMENTOR],
                base_module=base_module,
            ),
        )
        for key, security_scheme in security_schemes.items()
        if FALCON_OAS_IMPLEMENTOR in security_scheme
    }
