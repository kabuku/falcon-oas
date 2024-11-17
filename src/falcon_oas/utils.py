import importlib
import inspect

from typing import Callable


def import_class_or_function(name: str, base_module: str = ""):
    if base_module == ".":
        base_module = inspect.stack()[1].frame.f_globals["__name__"]

    if base_module and not base_module.endswith("."):
        base_module += "."

    module_name, object_name = (base_module + name).rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, object_name)


class cached_property(object):
    def __init__(self, func: Callable):
        self.func = func
        self.__doc__ = func.__doc__
        self.__name__ = func.__name__

    def __get__(self, instance, owner):
        # type: (Any, Any) -> Any
        if instance is None:  # pragma: no cover
            return self
        value = instance.__dict__[self.__name__] = self.func(instance)
        return value


_MAP = {
    "y": True,
    "yes": True,
    "t": True,
    "true": True,
    "on": True,
    "1": True,
    "n": False,
    "no": False,
    "f": False,
    "false": False,
    "off": False,
    "0": False,
}


def strtobool(value):
    try:
        return _MAP[str(value).lower()]
    except KeyError:
        raise ValueError('"{}" is not a valid bool value'.format(value))
