# Auto Dict

A package for transforming between python objects and dicts, where the dicts
contain only python builtin objects.

A use case of `AutoDict` will be converting python objects to/from dict to
automatically support any kinds of serialization/deserialization, such as json
or yaml.

## Get started

A simple example may be like:

```python
import json

from auto_dict import dictable, AutoDict

@dictable
class Student:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    # for comparison
    def __eq__(self, other):
        return isinstance(other, Student) and \
            self.name == other.name and \
            self.age == other.age


# convert object to dict
student = Student('limo', 90)
student_dict = AutoDict.to_dict(student)

# if you want to serialize the object, just dump the dict
json_string = json.dumps(student_dict)
with open(..., 'w+') as f:
    f.write(json_string)

# convert dict back to object
recovered_student = AutoDict.from_dict(student_dict)
assert student == recovered_student
```

In the above code, we first mark the custom class as dictable by using
the `dictable` annotator. Once marked, you can call `AutoDict.to_dict` and
`AutoDict.from_dict` to transform between objects and dictionaries.

## Usages

### Mark in annotator style

`AutoDict` provides two ways to mark a custom class as dictable.

You can annotate your class as dictable:

```python
from auto_dict import dictable

@dictable
class Student:
   def __init__(self, name, age):
       self.name = name
       self.age = age
   ...
```

### Mark in derive style

Or, you can derive from the `AutoDictable` base class:

```python
from auto_dict import Dictable

class Student(Dictable):
    def __init__(self, name, age):
        self.name = name
        self.age = age
    ...
```

### Mark nested dictable

To support auto-dict recursively, you need provide field types in class
annotations.

```python
from typing import List

from auto_dict import dictable

...

@dictable
class Apartment:
    students: List[Student]
    
    def __init__(self, students):
        self.students = students
```

### Transform with embedded class info

During the transforming from object to dictionary, you can embed the
class name into the output dictionary, so that no explicit type required for the
reverse transformation.

```python
from auto_dict import AutoDict

...  # mark class Student as dictable

student = Student('limo', 90)
student_dict = AutoDict.to_dict(student)
o_student = AutoDict.from_dict(student_dict)
assert student == o_student
```

### Transform with explicit type

Or, you can strip out the class information from the output dictionary to make
it clean. In this case, when you transform from the dictionary back to the
object, you need to provide the type explicitly:

```python
from auto_dict import AutoDict

...  # mark class Student as dictable

student = Student('limo', 90)
student_dict = AutoDict.to_dict(student, with_cls=False)
o_student = AutoDict.from_dict(student_dict, cls=Student)
assert student == o_student
```

### Overwrite default transformation behavior

The default to_dict reads objects' field `__dict__` to generate dict structure.

On the other side, the default from_dict first tries to call class constructor
without any arg, and then assign the dictionary to the object's field
`__dict__`. If that failed, the default from_dict will call the class
constructor with the dictionary as the kwargs.

To overwrite the behavior in annotator style, you need to provide the transform
functions in the annotator's call interface:

```python
from auto_dict import dictable


def student_to_dict(student):
    return {
        'name-age': f'{student.name}.{student.age}'
    }


def student_from_dict(dic, cls):
    assert cls is Student
    return cls(dic['name-age'])


@dictable(to_dict=student_to_dict, from_dict=student_from_dict)
class Student:
    def __init__(self, name_age):
        self.name, self.age = name_age.rsplit('.', maxsplit=1)
```

As for overwriting in derive style, just override methods `_to_dict` and
`_from_dict`:

```python
from auto_dict import Dictable

class Student(Dictable):
    def __init__(self, name_age):
        self.name, self.age = name_age.rsplit('.', maxsplit=1)
    
    def _to_dict(self) -> dict:
        return {
            'name-age': f'{self.name}.{self.age}'
        }

    @classmethod
    def _from_dict(cls, dic: dict) -> 'Student':
        return Student(dic['name-age'])
```