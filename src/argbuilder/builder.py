import subprocess
from .field import Field, AnyField, NOT_SET, VALUE_TOKEN
from .exception import InvalidFieldError
from typing import Any, cast
from operator import add
from functools import reduce as foldl
from warnings import deprecated

def find_all(
        x: str, 
        sub: str, 
        start: int = 0, 
        indices: list[int] | None = None
) -> list[int]:
    if indices is None:
        indices = []

    index = x.find(sub, start)

    if index == -1:
        return indices

    indices.append(index)
    return find_all(x, sub, index + len(sub), indices)

def split_by(x: str, sub: str) -> list[str]:
    indices = find_all(x, sub)
    n = len(sub)

    parts = list[str]()
    last = 0

    for left in indices:
        right = left + n

        if last < left:
            parts.append(x[last:left])

        parts.append(x[left:right])
        last = right

    if last < len(x):
        parts.append(x[last:])

    return parts


def get_command_name(x: object|type) -> str:
    if not isinstance(x, type):
        return get_command_name(type(x))
    else:
        name = x.__name__
        if '_' not in name:
            result = name
        else:
            result = name.rsplit('_', 1)[1]
        
        return result.lower()

class Chainable:
    def __init__(self, **kwargs: object):
        self._parent = None
        self._data = kwargs
    
    def __getattribute__(self, name: str) -> 'Bound|Any':
        try:
            attr = super().__getattribute__(name)
        except AttributeError:
            raise
        
        if (isinstance(attr, type) and 
            issubclass(attr, Chainable)):
            return Bound(attr, self)
        
        return cast(Any, attr)


class Command(Chainable):
    __builder_fields__: dict[str, AnyField]
    def __init_subclass__(cls):
        annotations = cls.__annotations__
        
        builder_fields = dict[str, AnyField]()
        for k,v in cls.__dict__.items():
            if not isinstance(v, Field):
                continue
            
            v = cast(AnyField, v)

            if v.annotation is not NOT_SET:
                annotations[k] = v.annotation

            if k not in annotations:
                raise InvalidFieldError(f'Field {k} is Field but has no type annotation.')
            
            v.cls = cls
            v.annotation = annotations[k]
            builder_fields[k] = v
        
        cls.__builder_fields__ = builder_fields
        
    def arg0(self) -> str:
        """Returns the string used as first argument when with_self=True. Override to customize."""
        return get_command_name(type(self))

    def fields(self):
        return {
            k:v
            for k,v in self.__dict__.items()
            if k in self.class_fields()
        }
    
    @classmethod
    def class_fields(cls):
        return cls.__builder_fields__

    def __init__(self, **kwargs: object):
        super().__init__()
        defaults = {
            k:v.default
            for k,v in self.class_fields().items()
            if v.default is not NOT_SET
        }

        kwargs = (defaults|kwargs)
        for k,v in kwargs.items():
            if k not in self.class_fields():
                raise KeyError(f'{k} is not a valid parameter.')
            setattr(self, k, v)

    def __repr__(self):
        cls = type(self)
        fields = ', '.join(f'{k}={v}' for k,v in self.fields().items())
        return f'{cls.__name__}({fields})'
    
    @classmethod
    def from_dict(cls, data: dict[str, object]):
        params = {
            k:v
            for k,v in data.items()
            if k in cls.__builder_fields__
        }
        
        return cls(**params)
    
    def _build_fields(self, with_self: bool, extra: dict[str, str]):
        result = list[str]()
        for k,v in self.fields().items():
            field = self.class_fields()[k]
            value = field.serializer(v)

            if isinstance(value, str):
                if isinstance(field.string, str):
                    result.append(field.string.format(value=value))
                else:
                    for x in field.string:
                        result.append(x.format(value=value))
            else: # isinstance(value, Iterable[str])
                if isinstance(field.string, str):
                    for part in split_by(field.string, VALUE_TOKEN):
                        if part == VALUE_TOKEN:
                            for x in value:
                                result.append(x)
                        else:
                            result.append(part.strip())
                else:
                    for part in field.string:
                        if part == VALUE_TOKEN:
                            for x in value:
                                result.append(x)
                        else:
                            result.append(part.strip())
        
        ret = list[str]()
        if with_self:
            arg0 = getattr(type(self), 'arg0')
            if isinstance(arg0, str):
                ret.append(arg0)
            elif callable(arg0):
                ret.append(arg0(self))
            else:
                raise TypeError(
                    f"'arg0' can be of type either 'str' or '(self) -> str', but got '{type(arg0).__name__}'"
                )
        
        ret.extend(result)
        ret.extend(extra)
        #ret = [*result, *args]
        return ret
        
    def build(self, with_self: bool = True, **args: str):
        has_parent = (
            hasattr(self, '_parent')
            and self._parent is not None
        )

        if has_parent:
            parts = list[Any]()
            node = self
            while node:
                parts.append(node._build_fields(
                    with_self=with_self,
                    extra={},
                ))
                node = node._parent
            
            return foldl(add, reversed(parts))
        
        return self._build_fields(
            with_self=with_self,
            extra=args
        )

    def run(self, **kwargs: object) -> subprocess.CompletedProcess[str]:
        """Runs the built command via subprocess.run. Kwargs are passed through."""
        DEFAULT_KWARGS = dict(
            text=False,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        kwargs = DEFAULT_KWARGS | kwargs
        return subprocess.run(self.build(), **kwargs)
    
    def __eq__(self, other: object):
        if not isinstance(other, type(self)):
            return False
        
        return (
            self.fields() == other.fields()
            and self.class_fields() == other.class_fields()
        )

class Bound:
    def __init__(self, cls: type[Command], parent: object):
        self.cls = cls
        self.parent = parent

    def __call__(self, **kwargs: object):
        child = self.cls(**kwargs)
        child._parent = self.parent
        return child
    
    
    def from_dict(self, data: dict[str, object]):
        child = self.cls.from_dict(data)
        child._parent = self.parent
        return child
    
@deprecated("Deprecated, use 'Command' instead.")
class Builder(Command): ...