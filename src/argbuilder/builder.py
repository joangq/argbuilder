from .field import BuilderField, AnyField, NOT_SET, VALUE_TOKEN
from .exception import InvalidFieldError
from typing import Iterable, cast

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


class Builder:
    __builder_fields__: dict[str, AnyField]
    def __init_subclass__(cls):
        annotations = cls.__annotations__
        
        builder_fields = dict[str, AnyField]()
        for k,v in cls.__dict__.items():
            if not isinstance(v, BuilderField):
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
        
    def build(self, **args: str):
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
        
        ret = [*result, *args]
        return ret
    
    def __eq__(self, other: object):
        if not isinstance(other, Builder):
            return False
        
        return (
            self.fields() == other.fields()
            and self.class_fields() == other.class_fields()
        )