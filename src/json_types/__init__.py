"""Type definitions and utilities for working with JSON in Python."""

from typing import Mapping, Optional, Sequence, TypeVar, Union, cast, overload

__version__ = "0.1.0"

__all__ = (
    "Json",
    "JsonObject",
    "JsonArray",
    "get_path",
)

T = TypeVar("T")

# https://www.json.org/json-en.html
Json = Optional[Union["JsonObject", "JsonArray", str, int, float, bool]]
JsonObject = Mapping[str, "Json"]
JsonArray = Sequence["Json"]


_SENTINEL = object()
_RAISE = object()


@overload
def get_path(obj: JsonObject, path: Sequence[str]) -> Json:
    ...


@overload
def get_path(obj: JsonObject, path: Sequence[str], default: T) -> Union[Json, T]:
    ...


def get_path(obj: JsonObject, path: Sequence[str], default: Union[T, object] = _RAISE) -> Union[Json, T]:
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
    new_json = cast(Json, json_or_sentinel)

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
