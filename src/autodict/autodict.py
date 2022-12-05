import dataclasses
import enum
import inspect
from dataclasses import is_dataclass
# noinspection PyUnresolvedReferences,PyProtectedMember
from typing import Any, Callable, ForwardRef, List, Mapping, Optional, Tuple, \
    Type, TypeVar, Union, _GenericAlias, get_type_hints

from registry import Registry

from autodict.errors import UnableFromDict, UnableToDict
from autodict.mapping_factory import mapping_builder
from autodict.predefined import dataclass_from_dict, dataclass_to_dict, \
    default_from_dict, default_to_dict, enum_from_dict, enum_to_dict, \
    unable_from_dict, unable_to_dict
from autodict.types import T, inspect_generic_origin, \
    inspect_generic_templ_args, is_annotated_class, is_builtin, is_generic, \
    is_generic_collection, is_generic_literal, is_generic_union, stable_map


@dataclasses.dataclass
class Meta:
    name: str
    to_dict: Optional[Callable[[Any], dict]] = None
    from_dict: Optional[Callable[[Type[T], dict], T]] = None


def dictable(Cls: T = None, name=None, to_dict=None, from_dict=None) \
        -> T or Callable[[T], T]:
    """
    Annotate [Cls] as dictable.

    The default transformation behavior can be overwritten by providing custom
    implementations.

    :param Cls: The class want to be dictable.
    :param name: The annotation name that may be embedded into dict.
    :param to_dict: A custom function to transform an instance of class `Cls` to
      a dictionary, where the fields can be still objects. None for
      using :py:func:`default_to_dict`.
    :param from_dict: A custom function to transform a dictionary to an instance
      of class `Cls`, where the fields are already transformed.
    :return: the original type.
    """

    def inner(cls):
        if issubclass(cls, enum.Enum):
            to_dict_ = to_dict or enum_to_dict
            from_dict_ = from_dict or enum_from_dict
        else:
            to_dict_ = to_dict or default_to_dict
            from_dict_ = from_dict or default_from_dict

        name_ = name or cls.__name__
        AutoDict.register(
            name=name_, to_dict=to_dict_, from_dict=from_dict_)(cls)
        return cls

    return inner(Cls) if Cls else inner


def to_dictable(cls: T = None, name=None, to_dict=None) \
        -> T or Callable[[T], T]:
    """
    Annotate [cls] as to_dictable.

    :param cls: The class want to be dictable.
    :param name: The annotation name that may be embedded into dict.
    :param to_dict: A custom function to transform an instance of class `Cls` to
      a dictionary, where the fields can be still objects. None for
      using :py:func:`default_to_dict`.
    :return: the original type.
    """
    try:
        meta = AutoDict.meta_of(cls)
        from_dict = meta.from_dict or unable_from_dict
    except KeyError:
        from_dict = unable_from_dict
    return dictable(cls, name=name, to_dict=to_dict, from_dict=from_dict)


def from_dictable(cls: T = None, name=None, from_dict=None) \
        -> T or Callable[[T], T]:
    """
    Annotate [cls] as from_dictable.

    :param cls: The class want to be dictable.
    :param name: The annotation name that may be embedded into dict.
    :param from_dict: A custom function to transform a dictionary to an instance
      of class `Cls`, where the fields are already transformed.
    :return: the original type.
    """
    try:
        meta = AutoDict.meta_of(cls)
        to_dict = meta.to_dict or unable_to_dict
    except KeyError:
        to_dict = unable_to_dict
    return dictable(cls, name=name, to_dict=to_dict, from_dict=from_dict)


class Dictable:
    """
    Base class for these classes that want to be dictable.

    Any classes that derive this class will be automatically marked as dictable.
    The transformation behavior can be overwritten.
    """

    def __init_subclass__(cls, name=None, to_dict=None, from_dict=None):
        dictable(cls, name=name, to_dict=to_dict, from_dict=from_dict)

    def _to_dict(self) -> dict:
        """
        Transform self into a dictionary.

        The fields of this instance can be preserved as objects instead of
        dictionaries.

        :return: The transformed dictionary.
        """
        return default_to_dict(self)

    @classmethod
    def _from_dict(cls: Type[T], dic: dict) -> T:
        """
        Transform a dictionary to an instance of this class.

        The items/fields of the input dictionary should have already been
        transformed.

        :param dic: The dictionary.
        :return: An instance of this class.
        """
        return default_from_dict(cls, dic)

    def to_dict(self, with_cls: bool = True, strict=True) -> dict:
        """
        Transform self to a dictionary if its class is registered.

        :param with_cls: A boolean value indicating if embedding class path into
          the final dict or not.
        :param strict: If true, raise :py:exc:`UnToDictable` when there is
          non-builtin object is not to_dictable.
        :return: the transformed dictionary if the class of obj is registered;
          otherwise, just the original object.
        :raises UnToDictable: if there is non-builtin object is not to_dictable
        """
        return AutoDict.to_dict(self, with_cls=with_cls, strict=strict)

    @classmethod
    def from_dict(cls: Type[T], dic: dict, strict=True) -> T:
        """
        Instantiate an object from a dictionary.

        :param dic: The dictionary which contains necessary information for
          instantiation.
        :param cls: The class that is going to be instantiated against. If
          providing `None`, the real class will be inferred from the dictionary.
        :param strict: If true, raise :py:exc:`UnToDictable` when there is
          non-builtin object is not from_dictable.
        :return: the instantiated object of the given class.
        :raises UnFromDictable: if there is non-builtin object is not
          from_dictable.
        """
        return AutoDict.from_dict(dic, cls, cls.__module__, strict=strict)


class AutoDict(Registry[Meta]):
    CLS_ANNO_KEY = '@'

    @staticmethod
    def to_dict(obj, with_cls=True, recursively=True, strict=True):
        """
        Transform `obj` to a dictionary if its class is registered.

        :param obj: The object going to be transformed.
        :param with_cls: A boolean value indicating if embedding class path into
          the final dict or not.
        :param recursively: A boolean value indicating if transform recursively.
        :param strict: If true, raise :py:exc:`UnToDictable` when there is
          non-builtin object is not to_dictable.
        :return: the transformed dictionary if the class of obj is registered;
          otherwise, just the original object.
        :raises UnToDictable: if there is non-builtin object is not to_dictable
        """
        cls = type(obj)

        if obj and isinstance(obj, Dictable):
            # noinspection PyProtectedMember
            dic, is_pure_dataclass = obj._to_dict(), False
        elif AutoDict.registered(cls):
            dic, is_pure_dataclass = AutoDict.meta_of(cls).to_dict(obj), False
        elif dataclasses.is_dataclass(obj):
            dic, is_pure_dataclass = dataclass_to_dict(obj), True
        elif is_builtin(cls) or not strict:
            dic, is_pure_dataclass = obj, False
        else:
            raise UnableToDict(cls)

        if recursively:
            def fn_transform(obj_):
                return AutoDict.to_dict(obj_, with_cls=with_cls, strict=strict)

            dic = _items_to_dict(dic, fn_transform)

        AutoDict._embed_class(cls, dic, with_cls and not is_pure_dataclass)
        return dic

    @staticmethod
    def from_dict(dic: dict or T, cls: Type[T] = None, recursively=True,
                  strict=True) -> T:
        """
        Instantiate an object from a dictionary.

        :param dic: The dictionary which contains necessary information for
          instantiation.
        :param cls: The class that is going to be instantiated against. If
          providing `None`, the real class will be inferred from the dictionary.
        :param recursively: A boolean value indicating if transforms
          items/fields or not.
        :param strict: If true, raise :py:exc:`UnFromDictable` when there is
          non-builtin object is not from_dictable.
        :return: the instantiated object of the given class.
        :raises UnFromDictable: if there is non-builtin object is not
          from_dictable.
        """
        embedded_cls = AutoDict._extract_class(dic, strict)
        cls = embedded_cls or cls if is_generic_union(cls) else \
            cls or embedded_cls

        if recursively:
            def rec(item_dic, item_cls):
                return AutoDict.from_dict(item_dic, item_cls, strict=strict)

            dic = _items_from_dict(dic, cls, rec)

        if inspect.isclass(cls) and issubclass(cls, Dictable):
            obj = cls._from_dict(dic)
        elif AutoDict.registered(cls):
            obj = AutoDict.meta_of(cls).from_dict(cls, dic)
        elif dataclasses.is_dataclass(cls):
            obj = dataclass_from_dict(cls, dic)
        elif cls is None or is_builtin(cls) or not strict:
            obj = dic
        else:
            raise UnableFromDict(cls)

        return obj

    @staticmethod
    def _embed_class(typ: type, dic: dict, with_cls: bool):
        if with_cls and not is_builtin(typ) and isinstance(dic, Mapping):
            dic[AutoDict.CLS_ANNO_KEY] = AutoDict.meta_of(typ).name

    @staticmethod
    def _extract_class(dic, strict: bool):
        if not isinstance(dic, dict) or AutoDict.CLS_ANNO_KEY not in dic:
            return None

        cls_name = dic[AutoDict.CLS_ANNO_KEY]
        cls = AutoDict.query(name=cls_name)

        if cls is None:
            if strict:
                raise UnableFromDict(cls_name)
        else:
            del dic[AutoDict.CLS_ANNO_KEY]

        return cls


def _items_to_dict(obj, fn_transform):
    return stable_map(obj, lambda v, _: fn_transform(v))


def _items_from_dict(dic, cls, fn_transform):
    if is_dataclass(cls):
        return _items_from_dict_dataclass(dic, cls, fn_transform)

    if is_annotated_class(cls):
        return _items_from_dict_annotated_class(dic, cls, fn_transform)

    if is_generic_collection(cls):  # List, Set, Dict, Tuple, Mapping, etc
        return _items_from_dict_generic_collection(dic, cls, fn_transform)

    if is_generic(cls):  # Union including Optional,
        return _items_from_dict_generic_non_collection(dic, cls, fn_transform)

    return stable_map(dic, lambda v, _: fn_transform(v, None))


def _items_from_dict_dataclass(dic, cls, fn_transform):
    annotations = get_type_hints(cls)

    def transform_field(field_dic, field_name):
        field_cls = annotations.get(field_name)
        if inspect.isclass(field_cls) and \
                issubclass(field_cls, dataclasses.InitVar):
            field_cls = field_cls.type

        return fn_transform(field_dic, field_cls)

    return stable_map(dic, transform_field)


def _items_from_dict_annotated_class(dic, cls, fn_transform):
    annotations = get_type_hints(cls)

    def transform_field(field_dic, field_name):
        return fn_transform(field_dic, annotations.get(field_name))

    return stable_map(dic, transform_field)


def _items_from_dict_generic_non_collection(dic, cls, fn_transform):
    if is_generic_union(cls):
        cand_classes = inspect_generic_templ_args(cls, defaults=(Any,))
        cand_objects = dict()
        for cand_cls in cand_classes:
            # builtin-as dict should be an instance of the original builtin
            cand_orig_cls = inspect_generic_origin(cand_cls) or cand_cls
            if is_builtin(cand_orig_cls) and not isinstance(dic, cand_orig_cls):
                continue

            # noinspection PyBroadException
            try:
                obj = fn_transform(dic, cand_cls)
                cand_objects[cand_cls] = obj
            except Exception:
                continue

        if len(cand_objects) > 1:
            raise ValueError(f'Multiple union type matched: {cand_objects}')

        return cand_objects.popitem()[-1]

    if is_generic_literal(cls):
        cand_literals = inspect_generic_templ_args(cls)
        assert dic in cand_literals
        return dic

    return dic


def _items_from_dict_generic_collection(dic, cls, fn_transform):
    # infer item type from template args of typing._GenericAlias
    data_cls = inspect_generic_origin(cls)
    assert issubclass(data_cls, type(dic))

    if issubclass(data_cls, Mapping):
        key_cls, val_cls = inspect_generic_templ_args(cls, defaults=(Any, Any))
        data_cls = mapping_builder(data_cls)
        return data_cls((fn_transform(key, key_cls), fn_transform(val, val_cls))
                        for key, val in dic.items())

    if issubclass(data_cls, tuple):
        item_classes = inspect_generic_templ_args(cls, defaults=(Any, ...))
        if len(item_classes) == 2 and item_classes[-1] is ...:
            item_classes = (item_classes[0],) * len(dic)
        return data_cls(fn_transform(item, item_cls) for item, item_cls in
                        zip(dic, item_classes))

    if issubclass(data_cls, (list, set, frozenset)):
        item_cls, = inspect_generic_templ_args(cls, defaults=(Any,))
        return data_cls(fn_transform(item, item_cls) for item in dic)

    raise ValueError(f'Unhandled generic collection type: {data_cls}')
