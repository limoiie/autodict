import dataclasses
import enum
import pathlib
from collections import namedtuple
from typing import List, Tuple, Union

import pytest

from autodict import AutoDict, dictable
from autodict.autodict import Dictable, from_dictable, to_dictable
from autodict.errors import UnableFromDict, UnableToDict
from autodict.options import Options
from conftest import support_literals


@dictable
class Normal:
    def __init__(self, str_value, int_value):
        self.str_value = str_value
        self.int_value = int_value

    def __eq__(self, other):
        return isinstance(other, Normal) and \
            self.str_value == other.str_value and \
            self.int_value == other.int_value

    def __str__(self):
        return f'({self.str_value}, {self.int_value})'


@dictable(name='SomeA')
class CustomName:
    def __init__(self, str_value, int_value):
        self.str_value = str_value
        self.int_value = int_value

    def __eq__(self, other):
        return isinstance(other, CustomName) and \
            self.str_value == other.str_value and \
            self.int_value == other.int_value


class Unregistered:
    def __init__(self, str_value, int_value):
        self.str_value = str_value
        self.int_value = int_value

    def __eq__(self, other):
        return isinstance(other, Unregistered) and \
            self.str_value == other.str_value and \
            self.int_value == other.int_value


@dictable
class WithEmptyConstructor:
    def __init__(self):
        self._protected_value = ''
        self.__private_value = 0

    @staticmethod
    def create(protected_value, private_value):
        self = WithEmptyConstructor()
        self._protected_value = protected_value
        self.__private_value = private_value
        return self

    def __eq__(self, other):
        return isinstance(other, WithEmptyConstructor) and \
            self._protected_value == other._protected_value and \
            self.__private_value == other.__private_value


@dictable
class WithComplexConstructor:
    def __init__(self, a, b, c=10, *d, e, f=20, **g):
        self.a, self.b, self.c, self.d, self.e, self.f, self.g = \
            a, b, c, d, e, f, g

    def __eq__(self, other):
        return isinstance(other, WithComplexConstructor) and \
               self.a, self.b, self.c, self.d, self.e, self.f, self.g == \
               other.a, other.b, other.c, other.d, other.e, other.f, other.g


@dictable
class WithIncompleteConstructor:
    def __init__(self, int_value1, int_value2):
        self.int_value1 = int_value1
        self.int_value2 = int_value2
        self.int_value3 = int_value1 + int_value2

    def __eq__(self, other):
        return isinstance(other, WithIncompleteConstructor) and \
            self.int_value1 == other.int_value1 and \
            self.int_value2 == other.int_value2 and \
            self.int_value3 == other.int_value3


@dictable
class WithHiddenMember:
    def __init__(self, protected_value, private_value):
        self._protected_value = protected_value
        self.__private_value = private_value

    def __eq__(self, other):
        return isinstance(other, WithHiddenMember) and \
            self._protected_value == other._protected_value and \
            self.__private_value == other.__private_value


@dictable
class WithInheritedHiddenMember(WithHiddenMember):
    def __init__(self, protected_value, private_value):
        super().__init__(protected_value, private_value)


@dictable
class NestDictable:
    a: Normal

    def __init__(self, a, count):
        self.a = a
        self.count = count

    def __eq__(self, other):
        return self.a == other.a and self.count == other.count


@dictable
class NestUnDictable:
    a: Unregistered

    def __init__(self, a, count):
        self.a = a
        self.count = count

    def __eq__(self, other):
        return isinstance(other, NestUnDictable) and \
            self.a == other.a and \
            self.count == other.count


class UnDictableNest:
    a: Normal

    def __init__(self, a, count):
        self.a = a
        self.count = count

    def __eq__(self, other):
        return isinstance(other, UnDictableNest) and \
            self.a == other.a and \
            self.count == other.count


@dictable
class AnnotatedList:
    b_list: List[NestDictable]

    def __init__(self, b_list, count):
        self.b_list = b_list
        self.count = count

    def __eq__(self, other):
        return isinstance(other, AnnotatedList) and \
            self.b_list == other.b_list and \
            self.count == other.count


@dictable
class AnnotatedTuple:
    value: Tuple[int, str]

    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return isinstance(other, AnnotatedTuple) and \
            self.value == other.value


@dictable
class AnnotatedUnion:
    union_value: Union[str, Normal, List[str]]

    def __init__(self, union_value):
        self.union_value = union_value

    def __eq__(self, other):
        return isinstance(other, AnnotatedUnion) and \
            self.union_value == other.union_value


@dictable
class AnnotatedListUnion:
    value: List[Union[str, Normal, List[str]]]

    def __init__(self, value):
        self.value = value

    def __eq__(self, other) -> bool:
        return isinstance(other, AnnotatedListUnion) and \
            self.value == other.value


if support_literals():
    from typing import Literal


    @dictable
    class AnnotatedLiteral:
        value: Literal['w+', 'r+']

        def __init__(self, value):
            self.value = value

        def __eq__(self, other):
            return isinstance(other, AnnotatedLiteral) and \
                self.value == other.value

else:
    @dictable
    class AnnotatedLiteral:
        value: str

        def __init__(self, value):
            self.value = value

        def __eq__(self, other):
            return isinstance(other, AnnotatedLiteral) and \
                self.value == other.value


@dictable
class AnnotatedRef:
    b: 'NestDictable'
    b_list: List['NestDictable']

    def __init__(self, b, b_list, count):
        self.b = b
        self.b_list = b_list
        self.count = count

    def __eq__(self, other):
        return isinstance(other, AnnotatedRef) and \
            self.b == other.b and \
            self.b_list == other.b_list and \
            self.count == other.count


@dictable
class Color(enum.Enum):
    Black = 1
    Red = 2


@dictable
class AnnotatedSpecialStd:
    path: pathlib.Path
    color: Color

    def __init__(self, path, color):
        self.path = path
        self.color = color

    def __eq__(self, other):
        return isinstance(other, AnnotatedSpecialStd) and \
            self.path == other.path and \
            self.color == other.color


@dataclasses.dataclass
class NativeDataclass:
    str_value: str
    list_value: List[int]


@dataclasses.dataclass
class DataclassWithField:
    init_value: str
    init_variable: dataclasses.InitVar[int] = 0
    post_init_value: int = dataclasses.field(init=False)
    default_value: int = dataclasses.field(default=10)

    def __post_init__(self, init_variable):
        self.post_init_value = self.default_value + init_variable


GoodCase = namedtuple('GoodCase', 'ins,obj,opts,name')

BadCase = namedtuple('BadCase', 'ins,obj,cls,opts,exc,raises,name')


def generate_good_cases() -> List[GoodCase]:
    return [
        GoodCase(
            name='with embedded class info',
            ins=Normal(str_value='limo', int_value=10),
            obj={'str_value': 'limo', 'int_value': 10, '@': 'Normal', },
            opts=Options(with_cls=True, strict=True),
        ),
        GoodCase(
            name='without embedded class info',
            ins=Normal(str_value='limo', int_value=10),
            obj={'str_value': 'limo', 'int_value': 10, },
            opts=Options(with_cls=False, strict=True),
        ),
        GoodCase(
            name='with embedded class info but customized name',
            ins=CustomName(str_value='limo', int_value=10),
            obj={'str_value': 'limo', 'int_value': 10, '@': 'SomeA', },
            opts=Options(with_cls=True, strict=True),
        ),
        GoodCase(
            name='allow un-dictable without embedding class info',
            ins=Unregistered(str_value='limo', int_value=10),
            obj=Unregistered(str_value='limo', int_value=10),
            opts=Options(with_cls=False, strict=False),
        ),
        GoodCase(
            name='allow un-dictable with embedded class info',
            ins={'str_value': 'limo', 'int_value': 10, '@': 'Unregistered'},
            obj={'str_value': 'limo', 'int_value': 10, '@': 'Unregistered'},
            opts=Options(with_cls=True, strict=False),
        ),
        GoodCase(
            name='when target is a dict itself',
            ins={'str_value': 'limo', 'int_value': 10},
            obj={'str_value': 'limo', 'int_value': 10},
            opts=Options(with_cls=True, strict=True),
        ),
        GoodCase(
            name='when has incomplete constructor',
            ins=WithIncompleteConstructor(int_value1=1, int_value2=2),
            obj={'int_value1': 1, 'int_value2': 2, 'int_value3': 3},
            opts=Options(with_cls=False, strict=True),
        ),
        GoodCase(
            name='when has complex constructor',
            ins=WithComplexConstructor(1, 2, 3, 4, 5, e=6, f=7, g=8, h=9, i=0),
            obj={'a': 1, 'b': 2, 'c': 3, 'd': (4, 5), 'e': 6, 'f': 7,
                 'g': {'g': 8, 'h': 9, 'i': 0}},
            opts=Options(with_cls=False, strict=True),
        ),
        GoodCase(
            name='when has hidden fields while constructor has no arg',
            ins=WithEmptyConstructor.create('limo', 20),
            obj={'_protected_value': 'limo',
                 '_WithEmptyConstructor__private_value': 20,
                 '@': 'WithEmptyConstructor'},
            opts=Options(with_cls=True, strict=True),
        ),
        GoodCase(
            name='when has hidden fields while constructor has args',
            ins=WithHiddenMember('limo', 20),
            obj={'_protected_value': 'limo',
                 '_WithHiddenMember__private_value': 20,
                 '@': 'WithHiddenMember'},
            opts=Options(with_cls=True, strict=True),
        ),
        GoodCase(
            name='when has inherited hidden fields while constructor has args',
            ins=WithInheritedHiddenMember('limo', 20),
            obj={'_protected_value': 'limo',
                 '_WithHiddenMember__private_value': 20,
                 '@': 'WithInheritedHiddenMember'},
            opts=Options(with_cls=True, strict=True),
        ),
        GoodCase(
            name='nested dictable with class annotation',
            ins=NestDictable(a=Normal(str_value='limo', int_value=10),
                             count=20),
            obj={'a': {'str_value': 'limo', 'int_value': 10, '@': 'Normal'},
                 'count': 20,
                 '@': 'NestDictable'},
            opts=Options(with_cls=True, strict=True),
        ),
        GoodCase(
            name='nested dictable with generic list',
            ins=AnnotatedList(b_list=[
                NestDictable(a=Normal(str_value='limo', int_value=20),
                             count=3)],
                count=4),
            obj={'@': 'AnnotatedList',
                 'b_list': [{'@': 'NestDictable',
                             'a': {'@': 'Normal', 'int_value': 20,
                                   'str_value': 'limo'},
                             'count': 3}],
                 'count': 4},
            opts=Options(with_cls=True, strict=False),
        ),
        GoodCase(
            name='nested dictable with tuple',
            ins=AnnotatedTuple(value=(1, 'limo')),
            obj={'@': 'AnnotatedTuple', 'value': (1, 'limo')},
            opts=Options(with_cls=True, strict=True),
        ),
        GoodCase(
            name='nested dictable with generic union - 1',
            ins=AnnotatedUnion(union_value='string value'),
            obj={'union_value': 'string value'},
            opts=Options(with_cls=False, strict=False),
        ),
        GoodCase(
            name='nested dictable with generic union - 2',
            ins=AnnotatedUnion(union_value=Normal(str_value='o', int_value=0)),
            obj={'union_value': {'str_value': 'o',
                                 'int_value': 0}},
            opts=Options(with_cls=False, strict=False),
        ),
        GoodCase(
            name='nested dictable with generic union - 3',
            ins=AnnotatedUnion(union_value=['string', 'value']),
            obj={'union_value': ['string', 'value']},
            opts=Options(with_cls=False, strict=False),
        ),
        GoodCase(
            name='nested dictable with generic list union',
            ins=AnnotatedListUnion(
                value=['string', Normal(str_value='o', int_value=0),
                       ['string', 'value']]),
            obj={'value': ['string',
                           {'str_value': 'o',
                            'int_value': 0},
                           ['string', 'value']]},
            opts=Options(with_cls=False, strict=False),
        ),
        GoodCase(
            name='nested dictable with generic literal',
            ins=AnnotatedLiteral(value='w+'),
            obj={'value': 'w+'},
            opts=Options(with_cls=False, strict=False),
        ),
        GoodCase(
            name='nested dictable with class annotation string',
            ins=AnnotatedRef(
                b=NestDictable(a=Normal(str_value='limo', int_value=10),
                               count=2),
                b_list=[NestDictable(a=Normal(str_value='limo', int_value=20),
                                     count=3)],
                count=4),
            obj={'@': 'AnnotatedRef',
                 'b': {'@': 'NestDictable',
                       'a': {'@': 'Normal', 'int_value': 10,
                             'str_value': 'limo'},
                       'count': 2},
                 'b_list': [{'@': 'NestDictable',
                             'a': {'@': 'Normal', 'int_value': 20,
                                   'str_value': 'limo'},
                             'count': 3}],
                 'count': 4},
            opts=Options(with_cls=True, strict=False),
        ),
        GoodCase(
            name='allow dictable has a non-dictable field',
            ins=NestUnDictable(a=Unregistered(str_value='limo', int_value=10),
                               count=20),
            obj={
                'a': Unregistered(str_value='limo', int_value=10),
                'count': 20,
                '@': 'NestUnDictable'
            },
            opts=Options(with_cls=True, strict=False),
        ),
        GoodCase(
            name='allow non-dictable has a dictable field',
            ins=UnDictableNest(a=Normal(str_value='limo', int_value=10),
                               count=2),
            obj=UnDictableNest(a=Normal(str_value='limo', int_value=10),
                               count=2),
            opts=Options(with_cls=True, strict=False),
        ),
        GoodCase(
            name='nested dictable with special std types',
            ins=AnnotatedSpecialStd(path=pathlib.Path('/home/limo/.bashrc'),
                                    color=Color.Red),
            obj={'@': 'AnnotatedSpecialStd',
                 'path': '/home/limo/.bashrc',
                 'color': {
                     '@': 'Color',
                     'value': Color.Red.value,
                     'name': Color.Red.name
                 }},
            opts=Options(with_cls=True, strict=False),
        ),
        GoodCase(
            name='native support to dataclass',
            ins=NativeDataclass(str_value='limo', list_value=[10, 20]),
            obj={'str_value': 'limo',
                 'list_value': [10, 20]},
            opts=Options(with_cls=False, strict=True),
        ),
        GoodCase(
            name='dataclass with fields',
            ins=DataclassWithField(init_value='A', init_variable=10,
                                   default_value=20),
            obj={'init_value': 'A', 'post_init_value': 30, 'default_value': 20},
            opts=Options(with_cls=False, strict=True),
        )
    ]


def generate_bad_cases():
    return [
        BadCase(
            name='unable to_dict in strict mode',
            ins=Unregistered(str_value='limo', int_value=10),
            obj=None,
            cls=None,
            opts=Options(with_cls=True, strict=True),
            exc=UnableToDict,
            raises=dict(match='.*Unregistered.*'),
        ),
        BadCase(
            name='unable from_dict in strict mode without embedded class info',
            ins=None,
            obj={'str_value': 'limo', 'int_value': 10},
            cls=Unregistered,
            opts=Options(strict=True),
            exc=UnableFromDict,
            raises=dict(match='.*Unregistered.*'),
        ),
        BadCase(
            name='unable from_dict in strict mode with embedded class info',
            ins=None,
            obj={'str_value': 'limo', 'int_value': 10, '@': 'Unregistered'},
            cls=None,
            opts=Options(strict=True),
            exc=UnableFromDict,
            raises=dict(match='.*Unregistered.*'),
        ),
        BadCase(
            name='panic if nested un-dictable when to_dict(.., strict)',
            ins=NestUnDictable(Unregistered(str_value='limo', int_value=10),
                               count=20),
            obj=None,
            cls=None,
            opts=Options(with_cls=True, strict=True),
            exc=UnableToDict,
            raises=dict(match='.*Unregistered.*'),
        ),
        BadCase(
            name='panic if nested un-dictable when from_dict(.., strict, cls)',
            ins=None,
            obj={
                'a': {'str_value': 'limo', 'int_value': 10},
                'count': 10,
            },
            cls=NestUnDictable,
            opts=Options(strict=True),
            exc=UnableFromDict,
            raises=dict(match='.*Unregistered.*'),
        ),
        BadCase(
            name='panic if nested un-dictable when from_dict(.., strict)',
            ins=None,
            obj={
                'a': {'str_value': 'limo', 'int_value': 10,
                      '@': 'Unregistered'},
                'count': 10,
                '@': 'NestUnDictable'
            },
            cls=None,
            opts=Options(strict=True),
            exc=UnableFromDict,
            raises=dict(match='.*Unregistered.*'),
        ),
        BadCase(
            name='panic if wrapped un-dictable when to_dict(.., strict)',
            ins=UnDictableNest(Normal(str_value='limo', int_value=10),
                               count=20),
            obj=None,
            cls=None,
            opts=Options(with_cls=True, strict=True),
            exc=UnableToDict,
            raises=dict(match='.*UnDictableNest.*'),
        ),
        BadCase(
            name='panic if wrapped un-dictable when from_dict(.., strict, cls)',
            ins=None,
            obj={
                'a': {'str_value': 'limo', 'int_value': 10},
                'count': 10,
            },
            cls=UnDictableNest,
            opts=Options(strict=True),
            exc=UnableFromDict,
            raises=dict(match='.*UnDictableNest.*'),
        ),
        BadCase(
            name='panic if wrapped un-dictable when from_dict(.., strict)',
            ins=None,
            obj={
                'a': {'str_value': 'limo', 'int_value': 10, '@': 'Normal'},
                'count': 10,
                '@': 'UnDictableNest'
            },
            cls=None,
            opts=Options(strict=True),
            exc=UnableFromDict,
            raises=dict(match='.*UnDictableNest.*'),
        ),
    ]


def case_name(case):
    return case.name


class TestAnnotate:
    @pytest.mark.parametrize('case', generate_good_cases(), ids=case_name)
    def test_to_dict(self, case: GoodCase):
        assert AutoDict.to_dict(case.ins, case.opts) == case.obj

    @pytest.mark.parametrize('case', generate_good_cases(), ids=case_name)
    def test_from_dict(self, case: GoodCase):
        cls = None if case.opts.with_cls else type(case.ins)
        output_obj = AutoDict.from_dict(case.obj, cls, case.opts)
        assert output_obj == case.ins

    @pytest.mark.parametrize('case', generate_bad_cases(), ids=case_name)
    def test_failed_to_or_from_dict(self, case: BadCase):
        with pytest.raises(case.exc, **case.raises):
            if case.obj is None:
                AutoDict.to_dict(case.ins, case.opts)
            elif case.ins is None:
                AutoDict.from_dict(case.obj, case.cls, case.opts)

    @to_dictable
    class PartialTo:
        def __init__(self, str_value, int_value):
            self.str_value = str_value
            self.int_value = int_value

    def test_to_dictable_to_dict(self):
        f = TestAnnotate.PartialTo(str_value='limo', int_value=10)
        dict_f = AutoDict.to_dict(f)

        assert dict_f == {'str_value': 'limo', 'int_value': 10,
                          '@': 'PartialTo'}

    def test_to_dictable_from_dict(self):
        dict_f = {'str_value': 'limo', 'int_value': 10, '@': 'PartialTo'}

        with pytest.raises(UnableFromDict, match='.*PartialTo.*'):
            AutoDict.from_dict(dict_f)

    @from_dictable
    class PartialFrom:
        def __init__(self, str_value, int_value):
            self.str_value = str_value
            self.int_value = int_value

        def __eq__(self, other):
            return isinstance(other, TestAnnotate.PartialFrom) and \
                self.str_value == other.str_value and \
                self.int_value == other.int_value

    def test_from_dictable_from_dict(self):
        dict_g = {'str_value': 'limo', 'int_value': 10, '@': 'PartialFrom'}

        g = AutoDict.from_dict(dict_g, TestAnnotate.PartialFrom)
        assert g == TestAnnotate.PartialFrom(str_value='limo', int_value=10)

    def test_from_dictable_to_dict(self):
        g = TestAnnotate.PartialFrom(str_value='limo', int_value=10)

        with pytest.raises(UnableToDict, match='.*PartialFrom.*'):
            AutoDict.to_dict(g)

    @to_dictable
    @from_dictable
    class PartialBoth:
        def __init__(self, str_value, int_value):
            self.str_value = str_value
            self.int_value = int_value

        def __eq__(self, other):
            return isinstance(other, TestAnnotate.PartialBoth) and \
                self.str_value == other.str_value and \
                self.int_value == other.int_value

    def test_to_from_dictable(self):
        h = TestAnnotate.PartialBoth(str_value='limo', int_value=10)
        dict_h = AutoDict.to_dict(h)

        assert dict_h == {'str_value': 'limo', 'int_value': 10,
                          '@': 'PartialBoth'}
        output_h = AutoDict.from_dict(dict_h)
        assert h == output_h


class TestDerive:
    class General(Dictable):
        def __init__(self, str_value, int_value):
            self.str_value = str_value
            self.int_value = int_value

        def __eq__(self, other):
            return isinstance(other, TestDerive.General) and \
                self.str_value == other.str_value and \
                self.int_value == other.int_value

    def test_derive_without_overwritten(self):
        f = TestDerive.General(str_value='limo', int_value=10)

        dict_f = AutoDict.to_dict(f)
        assert dict_f == {
            'str_value': 'limo', 'int_value': 10, '@': 'General'
        }

        output_f = AutoDict.from_dict(dict_f, TestDerive.General)
        assert f == output_f

    class CustomName(Dictable, name='SomeF'):
        def __init__(self, str_value, int_value):
            self.str_value = str_value
            self.int_value = int_value

        def __eq__(self, other):
            return isinstance(other, TestDerive.CustomName) and \
                self.str_value == other.str_value and \
                self.int_value == other.int_value

    def test_derive_without_overwritten_but_customized_name(self):
        f = TestDerive.CustomName(str_value='limo', int_value=10)

        dict_f = AutoDict.to_dict(f)
        assert dict_f == {
            'str_value': 'limo', 'int_value': 10, '@': 'SomeF'
        }

        output_f = AutoDict.from_dict(dict_f, TestDerive.General)
        assert f == output_f

    class OverrideBoth(Dictable):
        def __init__(self):
            self.str_value = ''
            self.int_value = 0

        def __eq__(self, other):
            return isinstance(other, TestDerive.OverrideBoth) and \
                self.str_value == other.str_value and \
                self.int_value == other.int_value

        @classmethod
        def _from_dict(cls, obj: dict, _: Options) -> 'TestDerive.OverrideBoth':
            g = TestDerive.OverrideBoth()
            g.str_value = obj['str_value']
            g.int_value = obj['int_value']
            return g

        def _to_dict(self, _: Options) -> dict:
            return {
                'str_value': self.str_value,
                'int_value': self.int_value
            }

    def test_derive_with_overwritten(self):
        g = TestDerive.OverrideBoth()
        g.str_value = 'limo'
        g.int_value = 10

        dict_g = AutoDict.to_dict(g)
        assert dict_g == {
            'str_value': 'limo', 'int_value': 10, '@': 'OverrideBoth'
        }

        output_g = AutoDict.from_dict(dict_g, TestDerive.OverrideBoth)
        assert g == output_g

    class NestedOverride(Dictable):
        g: 'TestDerive.OverrideBoth'

        def __init__(self):
            self.g = TestDerive.OverrideBoth()
            self.count = 0

        def __eq__(self, other):
            return self.g == other.g and \
                self.count == other.count

        @classmethod
        def _from_dict(cls, obj: dict, _) -> 'TestDerive.NestedOverride':
            h = TestDerive.NestedOverride()
            h.g = obj['g']
            h.count = obj['count']
            return h

        def _to_dict(self, _: Options) -> dict:
            return {
                'g': self.g,
                'count': self.count
            }

    def test_nested_derive_with_overwritten(self):
        h = TestDerive.NestedOverride()
        h.g = TestDerive.OverrideBoth()
        h.g.str_value = 'limo'
        h.g.int_value = 10
        h.count = 20

        dict_h = AutoDict.to_dict(h)
        assert dict_h == {
            'g': {'str_value': 'limo', 'int_value': 10, '@': 'OverrideBoth'},
            'count': 20,
            '@': 'NestedOverride'
        }

        output_h = AutoDict.from_dict(dict_h, TestDerive.NestedOverride)
        assert h == output_h
