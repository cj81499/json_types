"""Tests for flatten_json function."""

import pytest

import json_types


@pytest.mark.parametrize(
    ("obj", "separator", "expected"),
    (
        # Basic cases
        pytest.param(
            {"a": 1, "b": 2},
            ".",
            {"a": 1, "b": 2},
            id="simple_object",
        ),
        pytest.param(
            {
                "user": {
                    "name": "Alice",
                    "address": {
                        "city": "NYC",
                        "zip": 10001,
                    },
                }
            },
            ".",
            {
                "user.name": "Alice",
                "user.address.city": "NYC",
                "user.address.zip": 10001,
            },
            id="nested_object",
        ),
        # Primitive types
        pytest.param(
            {
                "string": "hello",
                "int": 42,
                "float": 3.14,
                "bool": True,
                "null": None,
            },
            ".",
            {
                "string": "hello",
                "int": 42,
                "float": 3.14,
                "bool": True,
                "null": None,
            },
            id="primitives_flat",
        ),
        pytest.param(
            {
                "data": {
                    "count": 5,
                    "ratio": 0.5,
                    "active": False,
                    "description": None,
                }
            },
            ".",
            {
                "data.count": 5,
                "data.ratio": 0.5,
                "data.active": False,
                "data.description": None,
            },
            id="primitives_nested",
        ),
        # Arrays
        pytest.param(
            {"items": [1, 2, 3]},
            ".",
            {
                "items[0]": 1,
                "items[1]": 2,
                "items[2]": 3,
            },
            id="simple_array",
        ),
        pytest.param(
            {
                "users": [
                    {"name": "Alice", "age": 30},
                    {"name": "Bob", "age": 25},
                ]
            },
            ".",
            {
                "users[0].name": "Alice",
                "users[0].age": 30,
                "users[1].name": "Bob",
                "users[1].age": 25,
            },
            id="array_of_objects",
        ),
        pytest.param(
            {"matrix": [[1, 2], [3, 4]]},
            ".",
            {
                "matrix[0][0]": 1,
                "matrix[0][1]": 2,
                "matrix[1][0]": 3,
                "matrix[1][1]": 4,
            },
            id="nested_arrays",
        ),
        pytest.param(
            {"data": [1, {"key": "value"}, [1, 2]]},
            ".",
            {
                "data[0]": 1,
                "data[1].key": "value",
                "data[2][0]": 1,
                "data[2][1]": 2,
            },
            id="mixed_array_objects",
        ),
        # Empty containers
        pytest.param(
            {"empty": []},
            ".",
            {"empty[]": []},
            id="empty_array",
        ),
        pytest.param(
            {"empty": {}},
            ".",
            {"empty{}": {}},
            id="empty_object",
        ),
        pytest.param(
            {
                "empty_list": [],
                "empty_dict": {},
                "values": [1, 2, 3],
            },
            ".",
            {
                "empty_list[]": [],
                "empty_dict{}": {},
                "values[0]": 1,
                "values[1]": 2,
                "values[2]": 3,
            },
            id="mixed_empty_containers",
        ),
        # None and booleans
        pytest.param(
            {"a": None, "b": {"c": None}},
            ".",
            {"a": None, "b.c": None},
            id="none_values",
        ),
        pytest.param(
            {"flag": False, "nested": {"enabled": True}},
            ".",
            {
                "flag": False,
                "nested.enabled": True,
            },
            id="boolean_values",
        ),
        # Number precision
        pytest.param(
            {
                "price": 19.99,
                "large": 1.23e-10,
            },
            ".",
            {
                "price": 19.99,
                "large": 1.23e-10,
            },
            id="number_precision",
        ),
        # Unicode
        pytest.param(
            {
                "🔑": {"🎯": "value"},
                "café": {"naïve": "text"},
            },
            ".",
            {
                "🔑.🎯": "value",
                "café.naïve": "text",
            },
            id="unicode_keys",
        ),
        # Custom separators
        pytest.param(
            {
                "user": {
                    "name": "Alice",
                    "address": {"city": "NYC"},
                }
            },
            "::",
            {
                "user::name": "Alice",
                "user::address::city": "NYC",
            },
            id="custom_separator",
        ),
        pytest.param(
            {"users": [{"name": "Alice"}]},
            "::",
            {"users[0]::name": "Alice"},
            id="custom_separator_arrays",
        ),
        # Empty key components
        pytest.param(
            {"": 1, "a": {"": 2, "b": 3}},
            ".",
            {
                "": 1,
                "a.": 2,
                "a.b": 3,
            },
            id="empty_key_component",
        ),
        # Primitive values
        pytest.param(
            "hello",
            ".",
            {},
            id="primitive_string",
        ),
        pytest.param(
            42,
            ".",
            {},
            id="primitive_int",
        ),
        pytest.param(
            None,
            ".",
            {},
            id="primitive_none",
        ),
        # Deep nesting
        pytest.param(
            {"complex": {"nested": {"deep": {"data": "value"}}}},
            ".",
            {"complex.nested.deep.data": "value"},
            id="deeply_nested",
        ),
        pytest.param(
            {"level0": {"level1": {"level2": {"level3": {"level4": {"level5": "deep"}}}}}},
            ".",
            {"level0.level1.level2.level3.level4.level5": "deep"},
            id="large_structure",
        ),
    ),
)
def test_flatten(obj: json_types.ImmutableJson, separator: str, expected: dict[str, json_types.JsonPrimitive]) -> None:
    """Test flattening JSON objects with various inputs and separators."""
    result = json_types.flatten_json(obj, separator=separator)
    assert result == expected


# Error cases


def test_flatten_ambiguous_paths_dot_in_key() -> None:
    """Test that ambiguous paths raise ValueError."""
    obj: json_types.ImmutableJson = {"a.b": 1, "a": {"b": 2}}
    with pytest.raises(ValueError):
        json_types.flatten_json(obj)


def test_flatten_ambiguous_paths_reverse_order() -> None:
    """Test that ambiguous paths in reverse order raise ValueError."""
    obj: json_types.ImmutableJson = {"a": {"b": 1}, "a.b": 2}
    with pytest.raises(ValueError):
        json_types.flatten_json(obj)


def test_flatten_special_characters_in_keys() -> None:
    """Test that special characters in keys raise ValueError when they match the separator."""
    obj: json_types.ImmutableJson = {"a.b": {"c.d": 1}}
    with pytest.raises(ValueError):
        json_types.flatten_json(obj, separator=".")


def test_flatten_circular_reference() -> None:
    """Test that circular references raise ValueError."""
    obj: dict[str, int | json_types.ImmutableJsonObject] = {"a": 1}
    obj["self"] = obj
    with pytest.raises(ValueError):
        json_types.flatten_json(obj)


def test_flatten_key_ordering_preserved() -> None:
    """Test that key insertion order is preserved."""
    obj: json_types.ImmutableJson = {
        "z": {"a": 1, "b": 2},
        "a": {"z": 3},
    }
    result = json_types.flatten_json(obj)
    keys = list(result.keys())
    assert keys == ["z.a", "z.b", "a.z"]
