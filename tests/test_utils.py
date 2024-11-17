import pytest

from falcon_oas.utils import import_class_or_function, strtobool

OBJECT = object()


def func():
    return


def test_import_string_without_base_module():
    name = "tests.test_utils.OBJECT"
    assert import_class_or_function(name) is OBJECT


def test_import_string_with_base_module():
    name = "test_utils.OBJECT"
    assert import_class_or_function(name, base_module="tests") is OBJECT


def test_import_string_with_base_module_dot():
    name = "test_utils.OBJECT"
    assert import_class_or_function(name, base_module="tests.") is OBJECT


def test_import_string_with_callable():
    assert import_class_or_function('func', base_module=".") is func


@pytest.mark.parametrize(
    "value",
    (
        "y",
        "Y",
        "yes",
        "t",
        "True",
        "ON",
        1,
    ),
)
def test_should_return_true(value):
    assert strtobool(value) is True


@pytest.mark.parametrize(
    "value",
    (
        "n",
        "N",
        "no",
        "f",
        "False",
        "OFF",
        0,
    ),
)
def test_should_return_false(value):
    assert strtobool(value) is False


def test_should_raise_value_error():
    with pytest.raises(ValueError):
        strtobool("VERDADEIRO")
