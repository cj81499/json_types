"""Roundtrip tests for flatten_json and unflatten_json."""

import pytest

import json_types


@pytest.mark.parametrize(
    "original",
    (
        pytest.param(
            {"a": 1, "b": 2},
            id="simple_object",
        ),
        pytest.param(
            {
                "user": {
                    "name": "Alice",
                    "address": {"city": "NYC", "zip": 10001},
                }
            },
            id="nested_object",
        ),
        pytest.param(
            {
                "users": [
                    {"name": "Alice", "age": 30},
                    {"name": "Bob", "age": 25},
                ]
            },
            id="with_arrays",
        ),
        pytest.param(
            {
                "empty_list": [],
                "empty_dict": {},
                "values": [1, 2, 3],
            },
            id="with_empty_containers",
        ),
        pytest.param(
            {
                "string": "hello",
                "int": 42,
                "float": 3.14,
                "bool_true": True,
                "bool_false": False,
                "null": None,
                "nested": {
                    "array": [1, 2, {"key": "value"}],
                },
            },
            id="with_all_types",
        ),
        pytest.param(
            {"complex": {"nested": {"deep": {"data": [1, 2, {"final": "value"}]}}}},
            id="complex_structure",
        ),
    ),
)
def test_roundtrip(original: json_types.ImmutableJson) -> None:
    """Test that flatten->unflatten preserves the original structure."""
    flattened = json_types.flatten_json(original)
    unflattened = json_types.unflatten_json(flattened)
    assert unflattened == original
