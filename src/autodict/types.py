from typing import Any, Callable, Collection, Mapping, TypeVar, Union

T = TypeVar("T")
M = TypeVar("M", bound=Mapping)
O = TypeVar("O", bool, int, float, str, list, set, tuple, dict, type(None))


def is_builtin(cls: type):
    return hasattr(cls, "__module__") and cls.__module__ in (
        object.__module__,
        "collections",
        "typing",
    )


def is_collection(cls: type):
    return issubclass(cls, (list, set, tuple, Mapping))


def is_annotated_class(cls: type):
    return hasattr(cls, "__annotations__")


def is_generic(cls: type):
    return hasattr(cls, "__origin__")


def is_generic_collection(cls: type):
    if is_generic(cls):
        origin = inspect_generic_origin(cls)
        try:
            return origin is not None and issubclass(origin, Collection)
        except TypeError:
            pass

    return False


def is_generic_union(cls):
    return is_generic(cls) and cls.__origin__ is Union


def is_generic_optional(cls):
    return is_generic_union(cls) and type(None) in inspect_generic_templ_args(cls)


def is_generic_literal(cls):
    try:
        from typing import Literal

        return is_generic(cls) and cls.__origin__ is Literal
    except ModuleNotFoundError:
        return False


def is_namedtuple(cls):
    return issubclass(cls, tuple) and hasattr(cls, "_fields")


def strip_hidden_member_prefix(cls: type, key: str):
    """
    Demangle the private field name.

    A private field is declared being prefixed with a single underscore.
    It will be mangled to _<class_name>__<field_name> during runtime
    for preventing the access.

    :param cls: The class that declares the field.
    :param key: The field name.
    :return: The declared field name.
    """
    if not key.startswith("_"):
        return key

    if "__" in key:
        # strip private prefix for fields defined in this class
        prefix = f"_{cls.__name__}__"
        if key.startswith(prefix):
            return key[len(prefix) :]

        # strip private prefix for fields defined in base classes
        for parent_cls in cls.__bases__:
            strip_key = strip_hidden_member_prefix(parent_cls, key)
            if len(strip_key) + 1 < len(key):
                return strip_key

    return key[1:]


def stable_map(obj, mapper: Callable[[Any, Any], Any]):
    """
    Map stably keeping the original collection class.

    :param obj: A collection object.
    :param mapper: A transform function.
    """
    cls = obj.__class__

    if issubclass(cls, Mapping):
        from autodict.mapping_factory import mapping_factory

        return mapping_factory(
            cls, ((key, mapper(item, key)) for key, item in obj.items())
        )

    if is_namedtuple(cls):
        return cls(*(mapper(item, i) for i, item in enumerate(obj)))

    if issubclass(cls, (list, set, frozenset, tuple)):
        return cls(mapper(item, i) for i, item in enumerate(obj))

    return obj


def inspect_generic_templ_args(cls: type, defaults=()):
    if hasattr(cls, "_special") and cls._special:
        return defaults

    return getattr(cls, "__args__", None) or defaults


def inspect_generic_origin(cls: type):
    return getattr(cls, "__extra__", None) or getattr(cls, "__origin__", None)
