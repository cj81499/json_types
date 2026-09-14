from collections.abc import Sequence

import pytest

import json_types

json_object: json_types.ImmutableJsonObject = {
    "a": 1,
    "b": 2.1,
    "c": True,
    "d": "Hello, world!",
    "e": None,
    "f": [1, 2, 3],
    "g": {
        "h": 2,
        "i": {
            "j": "deeply nested",
        },
    },
}


@pytest.mark.parametrize(
    ("path", "expected"),
    (
        pytest.param(("a",), 1),
        pytest.param(("b",), 2.1),
        pytest.param(("c",), True),
        pytest.param(("d",), "Hello, world!"),
        pytest.param(("e",), None),
        pytest.param(("f",), [1, 2, 3]),
        pytest.param(("g", "h"), 2),
        pytest.param(("g", "i", "j"), "deeply nested"),
    ),
)
def test_deep_get(path: Sequence[str], expected: json_types.ImmutableJson) -> None:
    assert json_types.get_path(json_object, path) == expected


@pytest.mark.parametrize(
    ("path", "default", "expected"),
    (
        # default is ignored when a valid path is provided
        pytest.param(("a",), "DEFAULT", 1),
        pytest.param(("b",), "DEFAULT", 2.1),
        pytest.param(("c",), None, True),
        pytest.param(("d",), "DEFAULT", "Hello, world!"),
        pytest.param(("e",), "DEFAULT", None),
        pytest.param(("f",), "DEFAULT", [1, 2, 3]),
        pytest.param(("g", "h"), "DEFAULT RETURN VALUE", 2),
        pytest.param(("g", "i", "j"), "DEFAULT RETURN VALUE", "deeply nested"),
        # default is returned when an invalid path is provided
        pytest.param(("a", "z"), "DEFAULT", "DEFAULT"),
        pytest.param(("b", "z"), "DEFAULT", "DEFAULT"),
        pytest.param(("c", "z"), None, None),
        pytest.param(("d", "z"), "DEFAULT", "DEFAULT"),
        pytest.param(("e", "z"), "DEFAULT", "DEFAULT"),
        pytest.param(("f", "z"), [], []),
        pytest.param(("g", "h", "z"), "DEFAULT RETURN VALUE", "DEFAULT RETURN VALUE"),
        pytest.param(("g", "i", "j", "z"), "DEFAULT RETURN VALUE", "DEFAULT RETURN VALUE"),
    ),
)
def test_deep_get_with_default(path: Sequence[str], default: object, expected: json_types.ImmutableJson) -> None:
    assert json_types.get_path(json_object, path, default) == expected


def test_deep_get_raises_str_path() -> None:
    with pytest.raises(TypeError):
        json_types.get_path(json_object, "a")


def test_deep_get_raises_bad_path() -> None:
    with pytest.raises(ValueError):
        json_types.get_path(json_object, ("a", "b"))
