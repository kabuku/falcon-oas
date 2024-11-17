from falcon_oas import extensions, factories
from falcon_oas.routing import generate_routes


class Resource(object):
    pass


def test_generate_routes(petstore_dict):
    path_item = petstore_dict["paths"]["/v1/pets"]
    path_item[extensions.FALCON_OAS_IMPLEMENTOR] = "test_routing.Resource"

    spec = factories.create_spec_from_dict(petstore_dict)
    routes = list(generate_routes(spec, base_module="tests"))
    assert routes == [("/api/v1/pets", Resource)]
