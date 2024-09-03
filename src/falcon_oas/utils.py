
import importlib

import six


def import_string(name, base_module=''):
    if not isinstance(name, six.string_types):
        return name

    if base_module and not base_module.endswith('.'):
        base_module += '.'

    module_name, object_name = (base_module + name).rsplit('.', 1)
    module = importlib.import_module(module_name)
    return getattr(module, object_name)
