"""Tests for unflatten_json function."""

import pytest

import json_types


@pytest.mark.parametrize(
    ("flat", "separator", "expected"),
    (
        # Basic cases
        pytest.param(
            {"a": 1, "b": 2},
            ".",
            {"a": 1, "b": 2},
            id="simple_dict",
        ),
        pytest.param(
            {
                "user.name": "Alice",
                "user.address.city": "NYC",
                "user.address.zip": 10001,
            },
            ".",
            {
                "user": {
                    "name": "Alice",
                    "address": {
                        "city": "NYC",
                        "zip": 10001,
                    },
                }
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
            id="primitives",
        ),
        # Arrays
        pytest.param(
            {
                "items[0]": 1,
                "items[1]": 2,
                "items[2]": 3,
            },
            ".",
            {"items": [1, 2, 3]},
            id="simple_array",
        ),
        pytest.param(
            {
                "users[0].name": "Alice",
                "users[0].age": 30,
                "users[1].name": "Bob",
                "users[1].age": 25,
            },
            ".",
            {
                "users": [
                    {"name": "Alice", "age": 30},
                    {"name": "Bob", "age": 25},
                ]
            },
            id="array_of_objects",
        ),
        pytest.param(
            {
                "matrix[0][0]": 1,
                "matrix[0][1]": 2,
                "matrix[1][0]": 3,
                "matrix[1][1]": 4,
            },
            ".",
            {"matrix": [[1, 2], [3, 4]]},
            id="nested_arrays",
        ),
        pytest.param(
            {
                "data[0]": 1,
                "data[1].key": "value",
                "data[2][0]": 1,
                "data[2][1]": 2,
            },
            ".",
            {
                "data": [
                    1,
                    {"key": "value"},
                    [1, 2],
                ]
            },
            id="mixed_array_objects",
        ),
        # Empty containers
        pytest.param(
            {"empty[]": []},
            ".",
            {"empty": []},
            id="empty_array_marker",
        ),
        pytest.param(
            {"empty{}": {}},
            ".",
            {"empty": {}},
            id="empty_object_marker",
        ),
        pytest.param(
            {
                "empty_list[]": [],
                "empty_dict{}": {},
                "values[0]": 1,
                "values[1]": 2,
                "values[2]": 3,
            },
            ".",
            {
                "empty_list": [],
                "empty_dict": {},
                "values": [1, 2, 3],
            },
            id="mixed_empty_containers",
        ),
        # None and booleans
        pytest.param(
            {
                "a": None,
                "b.c": None,
            },
            ".",
            {"a": None, "b": {"c": None}},
            id="none_values",
        ),
        pytest.param(
            {
                "flag": False,
                "nested.enabled": True,
            },
            ".",
            {
                "flag": False,
                "nested": {"enabled": True},
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
                "🔑.🎯": "value",
                "café.naïve": "text",
            },
            ".",
            {
                "🔑": {"🎯": "value"},
                "café": {"naïve": "text"},
            },
            id="unicode_keys",
        ),
        # Custom separators
        pytest.param(
            {
                "user::name": "Alice",
                "user::address::city": "NYC",
            },
            "::",
            {
                "user": {
                    "name": "Alice",
                    "address": {"city": "NYC"},
                }
            },
            id="custom_separator",
        ),
        pytest.param(
            {"users[0]::name": "Alice"},
            "::",
            {"users": [{"name": "Alice"}]},
            id="custom_separator_arrays",
        ),
        # Deep nesting
        pytest.param(
            {"complex.nested.deep.data": "value"},
            ".",
            {"complex": {"nested": {"deep": {"data": "value"}}}},
            id="deeply_nested",
        ),
        # Empty dictionary
        pytest.param(
            {},
            ".",
            {},
            id="empty_dict",
        ),
    ),
)
def test_unflatten(
    flat: dict[str, json_types.JsonPrimitive], separator: str, expected: json_types.ImmutableJson
) -> None:
    """Test unflattening flat dictionaries with various inputs and separators."""
    result = json_types.unflatten_json(flat, separator=separator)
    assert result == expected


# Error cases


@pytest.mark.parametrize(
    "flat",
    (
        pytest.param(
            {
                "items[0]": 1,
                "items[2]": 3,  # Missing index 1
            },
            id="non_sequential_indices",
        ),
        pytest.param(
            {"items[5]": "value"},
            id="out_of_bounds_index",
        ),
    ),
)
def test_unflatten_invalid_array_indices(flat: dict[str, json_types.JsonPrimitive]) -> None:
    """Test that invalid array indices raise IndexError."""
    with pytest.raises(IndexError):
        json_types.unflatten_json(flat)


@pytest.mark.parametrize(
    "flat",
    (
        pytest.param(
            {"items[-1]": "value"},
            id="negative_index",
        ),
        pytest.param(
            {"items[abc]": "value"},
            id="non_numeric_index",
        ),
        pytest.param(
            {"items[0": "value"},
            id="malformed_bracket_syntax",
        ),
    ),
)
def test_unflatten_invalid_array_syntax(flat: dict[str, json_types.JsonPrimitive]) -> None:
    """Test that invalid array syntax raises ValueError."""
    with pytest.raises(ValueError):
        json_types.unflatten_json(flat)


def test_unflatten_type_conflict_array_object() -> None:
    """Test that type conflicts between array and object raise an error."""
    flat: dict[str, json_types.JsonPrimitive] = {
        "items[0]": 1,
        "items.key": "value",  # Conflicts with array
    }
    with pytest.raises(ValueError):
        json_types.unflatten_json(flat)
