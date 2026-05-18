"""Type definitions and utilities for working with JSON in Python."""

import sys
from collections import deque
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from typing import NewType, TypeVar, Union, cast, overload

if sys.version_info < (3, 11):
    from typing_extensions import assert_never
else:
    from typing import assert_never

__version__ = "0.2.0"

__all__ = (
    "ImmutableJson",
    "ImmutableJsonArray",
    "ImmutableJsonObject",
    "Json",
    "JsonArray",
    "JsonObject",
    "JsonPrimitive",
    "MutableJson",
    "MutableJsonArray",
    "MutableJsonObject",
    "flatten_json",
    "get_path",
    "unflatten_json",
)

T = TypeVar("T")

# https://www.json.org/json-en.html
JsonPrimitive = str | int | float | bool | None

ImmutableJson = Union["ImmutableJsonObject", "ImmutableJsonArray", str, int, float, bool, None]
ImmutableJsonObject = Mapping[str, "ImmutableJson"]
ImmutableJsonArray = Sequence["ImmutableJson"]

MutableJson = Union["MutableJsonObject", "MutableJsonArray", str, int, float, bool, None]
MutableJsonObject = MutableMapping[str, "MutableJson"]
MutableJsonArray = MutableSequence["MutableJson"]

Json = ImmutableJson
JsonObject = ImmutableJsonObject
JsonArray = ImmutableJsonArray

_Sentinel = NewType("_Sentinel", object)
_SENTINEL = _Sentinel(object())

_Raise = NewType("_Raise", object)
_RAISE = _Raise(object())


@overload
def get_path(obj: ImmutableJsonObject, path: Sequence[str]) -> ImmutableJson: ...


@overload
def get_path(obj: ImmutableJsonObject, path: Sequence[str], default: T) -> ImmutableJson | T: ...


def get_path(obj: ImmutableJsonObject, path: Sequence[str], default: T | object = _RAISE) -> ImmutableJson | T:
    """Get the value at `path` of the JSONObject `obj`."""
    # str is a Sequence[str], but is not an acceptable path
    if isinstance(path, str):
        msg = "path must not be a str"
        raise TypeError(msg)

    if len(path) == 0:
        return obj

    first, *rest = path

    json_or_sentinel = obj.get(first, _SENTINEL)
    if json_or_sentinel is _SENTINEL:
        if default is _RAISE:
            msg = "obj does not have element at path"
            raise ValueError(msg)
        # default is not _RAISE, so it must be T
        return cast(T, default)
    # default json_or_sentinel is not _SENTINEL, so it must be Json
    new_json = cast(ImmutableJson, json_or_sentinel)

    # if there are no remaining path components, we've found the result
    if not rest:
        return new_json

    if not isinstance(new_json, Mapping):
        if default is _RAISE:
            msg = "element along path was not a json object"
            raise ValueError(msg)
        # default is not _RAISE, so it must be T
        return cast(T, default)

    return get_path(
        new_json,
        rest,
        # the public API shouldn't know that default can be an object
        default,  # type: ignore[arg-type]
    )


def flatten_json(obj: ImmutableJson, separator: str = ".") -> ImmutableJsonObject:  # noqa: C901, PLR0912
    """Flatten a nested JSON object into a flat dictionary with dot-separated keys.

    Args:
        obj: The JSON object to flatten
        separator: The separator to use for nested keys (default: ".")

    Returns:
        A flat dictionary with keys like "user.name" for nested values

    Raises:
        ValueError: If paths are ambiguous or circular references are detected
        IndexError: If array indices are out of bounds
    """
    result: MutableJsonObject = {}
    visited: set[int] = set()

    # Use deque to maintain insertion order (FIFO)
    queue: deque[tuple[ImmutableJson, str]] = deque([(obj, "")])

    while queue:
        current, path_prefix = queue.popleft()

        # Handle primitive values at the root or leaf nodes
        if not isinstance(current, Mapping | Sequence) or isinstance(current, str):
            if path_prefix:
                result[path_prefix] = current
            continue

        # Detect circular references
        obj_id = id(current)
        if obj_id in visited:
            msg = "circular reference detected"
            raise ValueError(msg)
        visited.add(obj_id)

        if isinstance(current, Sequence):
            if len(current) == 0:
                # Empty array marker
                result[f"{path_prefix}[]"] = []
            else:
                for i, item in enumerate(current):
                    new_path = f"{path_prefix}[{i}]"
                    if isinstance(item, (Mapping, Sequence)) and not isinstance(item, str):
                        # Check for circular reference before adding to queue
                        if id(item) in visited:
                            msg = "circular reference detected"
                            raise ValueError(msg)
                        queue.append((item, new_path))
                    else:
                        result[new_path] = item
        elif isinstance(current, Mapping):
            if len(current) == 0:
                # Empty object marker
                result[f"{path_prefix}{{}}"] = {}
            else:
                for key, value in current.items():
                    if not isinstance(key, str):
                        msg = "dictionary keys must be strings"
                        raise ValueError(msg)

                    # Check for ambiguous paths
                    if separator in key:
                        msg = f"key contains separator: {key}"
                        raise ValueError(msg)

                    new_path = f"{path_prefix}{separator}{key}" if path_prefix else key

                    if isinstance(value, Mapping | Sequence) and not isinstance(value, str):
                        # Check for circular reference before adding to queue
                        if id(value) in visited:
                            msg = "circular reference detected"
                            raise ValueError(msg)
                        queue.append((value, new_path))
                    else:
                        result[new_path] = value
        else:
            assert_never(current)

    return result


def unflatten_json(flat_dict: ImmutableJsonObject, separator: str = ".") -> ImmutableJson:
    """Reconstruct a nested JSON object from a flat dictionary with dot-separated keys.

    Args:
        flat_dict: The flat dictionary to unflatten
        separator: The separator used for nested keys (default: ".")

    Returns:
        A nested JSON object reconstructed from the flat dictionary

    Raises:
        ValueError: If paths are malformed
        IndexError: If array indices are not sequential or out of order
    """

    result: MutableJsonObject = {}

    # Parse all keys and build a structure
    for flat_key, value in flat_dict.items():
        # Parse the path from the flat key
        path = _parse_path(flat_key, separator)

        # Set the value at this path
        _set_value_at_path(result, path, value)

    return result


def _parse_path(key: str, separator: str) -> list[str | int]:  # noqa: C901, PLR0912
    """Parse a flattened key into a path of keys and array indices.

    Returns a list where each element is either a string (dict key), int (array index),
    "[]" (empty array marker), or "{}" (empty object marker).
    """
    path: list[str | int] = []
    current = ""
    i = 0

    while i < len(key):
        # Check for array index syntax [n]
        if key[i] == "[":
            # First, add any accumulated key
            if current:
                path.append(current)
                current = ""

            # Find the closing bracket
            j = i + 1
            while j < len(key) and key[j] != "]":
                j += 1

            if j >= len(key):
                msg = "malformed bracket syntax: missing closing bracket"
                raise ValueError(msg)

            # Extract the index
            index_str = key[i + 1 : j]

            # Check for empty array marker
            if index_str == "":
                # Empty array marker []
                path.append("[]")
            else:
                # Validate it's a non-negative integer
                try:
                    index = int(index_str)
                    if index < 0:
                        msg = "negative array indices are not supported"
                        raise ValueError(msg)
                    path.append(index)
                except ValueError as e:
                    if "negative" in str(e):
                        raise
                    msg = f"invalid array index: {index_str}"
                    raise ValueError(msg) from e
            i = j + 1
        elif key[i] == "]":
            msg = "malformed bracket syntax: unexpected closing bracket"
            raise ValueError(msg)
        elif key[i : i + len(separator)] == separator:
            # Separator found
            if current:
                path.append(current)
                current = ""
            i += len(separator)
        elif key[i : i + 2] == "{}":
            # Empty object marker {}
            if current:
                path.append(current)
                current = ""
            path.append("{}")
            i += 2
        else:
            current += key[i]
            i += 1

    if current:
        path.append(current)

    return path


def _set_value_at_path(  # noqa: C901, PLR0912, PLR0915
    root: MutableJsonObject | MutableJsonArray,
    path: list[str | int],
    value: ImmutableJson,
) -> None:
    """Set a value at the given path in the root structure."""
    if not path:
        return

    # Handle empty markers specially
    _min_marker_path_len = 2
    if len(path) >= _min_marker_path_len and path[-1] in ("[]", "{}"):
        # The marker applies to the previous key
        # E.g., path ["empty", "[]"] with value [] means set root["empty"] = []
        final_key = path[-2]
        marker = path[-1]
        path_to_navigate = path[:-2]

        # Navigate to the parent
        current = root
        for _i, key in enumerate(path_to_navigate):
            if isinstance(key, int):
                if not isinstance(current, list):
                    msg = "type conflict: expected array"
                    raise ValueError(msg)
                while len(current) <= key:
                    current.append(None)
                if current[key] is None:
                    current[key] = {}
                current = current[key]
            else:
                if not isinstance(current, dict):
                    msg = "type conflict: expected dict"
                    raise ValueError(msg)
                if key not in current:
                    current[key] = {}
                current = current[key]

        # Set the final value using the marker
        if not isinstance(current, dict):
            msg = "type conflict: expected dict"
            raise ValueError(msg)
        if not isinstance(final_key, str):
            msg = "type conflict: expected string key before marker"
            raise ValueError(msg)

        if marker == "[]":
            current[final_key] = []
        else:  # marker == "{}"
            current[final_key] = {}
        _validate_arrays(root)
        return

    # Normal path handling
    # Navigate/create the structure
    current = root

    for i, key in enumerate(path[:-1]):
        if isinstance(key, int):
            # Array index
            if not isinstance(current, list):
                msg = "type conflict: expected array"
                raise ValueError(msg)

            # Extend array if needed
            while len(current) <= key:
                current.append(None)

            # Peek ahead to see what the next key is
            next_key = path[i + 1]
            if isinstance(next_key, int):
                # Next is also array index
                if current[key] is None:
                    current[key] = []
                current = current[key]
            else:
                # Next is a string key
                if current[key] is None:
                    current[key] = {}
                if not isinstance(current[key], dict):
                    msg = "type conflict: expected dict"
                    raise ValueError(msg)
                current = current[key]
        elif isinstance(current, dict):
            # String key (dict key)
            # Peek ahead to see what the next key is
            next_key = path[i + 1]
            if isinstance(next_key, int):
                # Next is array index
                if key not in current:
                    current[key] = []
                if not isinstance(current[key], list):
                    msg = "type conflict: expected array"
                    raise ValueError(msg)
                current = current[key]
            else:
                # Next is a string key
                if key not in current:
                    current[key] = {}
                if not isinstance(current[key], dict):
                    msg = "type conflict: expected dict"
                    raise ValueError(msg)
                current = current[key]
        elif isinstance(current, list):
            msg = "type conflict: expected dict for string key"
            raise ValueError(msg)
        else:
            msg = "type conflict: expected dict or array"
            raise ValueError(msg)

    # Set the final value
    final_key = path[-1]
    if isinstance(final_key, int):
        if not isinstance(current, list):
            msg = "type conflict: expected array"
            raise ValueError(msg)

        # Extend array if needed
        while len(current) <= final_key:
            current.append(None)

        # Check for gaps in array indices
        if final_key > 0 and current[final_key - 1] is None:
            # Check if there are any non-None values after this
            has_later_values = any(current[j] is not None for j in range(final_key + 1, len(current)))
            if not has_later_values and final_key > len([x for x in current[:final_key] if x is not None]):
                msg = "non-sequential array indices"
                raise IndexError(msg)

        current[final_key] = value
    else:
        if not isinstance(current, dict):
            msg = "type conflict: expected dict"
            raise ValueError(msg)
        current[final_key] = value

    # Validate array indices are sequential
    _validate_arrays(root)


def _validate_arrays(root: ImmutableJson) -> None:
    """Validate that all arrays have sequential indices starting from 0."""
    stack: list[ImmutableJson] = [root]

    while stack:
        current = stack.pop()

        if isinstance(current, list):
            # Check for None values (gaps)
            for i, item in enumerate(current):
                if item is None:
                    msg = f"non-sequential array indices at position {i}"
                    raise IndexError(msg)
                stack.append(item)
        elif isinstance(current, dict):
            for value in current.values():
                stack.append(value)
