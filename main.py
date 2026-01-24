from collections import namedtuple
from typing import Any, Callable
from dataclasses import dataclass

import pydantic

@dataclass
class BuilderField[T: type[Any]]:
    string: str
    annotation: None | T
    cls: None | type[Any]
    serializer: Callable[[T], str]

def Field[T: type[Any]](string: str, serializer: Callable[[T], str] = lambda x: str(x)):
    return BuilderField[T](
        string=string,
        annotation=None,
        cls=None,
        serializer=serializer
    )

class InvalidFieldError(Exception): ...

class Builder:
    __builder_fields__: dict[str, BuilderField]
    def __init_subclass__(cls) -> None:
        annotations = cls.__annotations__

        builder_fields = dict()
        for k,v in cls.__dict__.items():
            if not isinstance(v, BuilderField):
                continue

            if k not in annotations:
                raise InvalidFieldError(f'Field {k} is Field but has no type annotation.')
            
            v.cls = cls
            v.annotation = annotations[k]
            builder_fields[k] = v
        
        cls.__builder_fields__ = builder_fields
        

    def fields(self) -> dict:
        cls = type(self)
        return {
            k:v
            for k,v in self.__dict__.items()
            if k in cls.__builder_fields__
        }
    
    def class_fields(self):
        return type(self).__builder_fields__


    def __init__(self, **kwargs):
        cls = type(self)
        for k,v in kwargs.items():
            if k not in cls.__builder_fields__:
                raise KeyError(f'{k} is not a valid parameter.')
            setattr(self, k, v)

    def __repr__(self):
        cls = type(self)
        fields = ', '.join(f'{k}={v}' for k,v in self.fields().items())
        return f'{cls.__name__}({fields})'
    
    @classmethod
    def from_dict(cls, data: dict):
        params = {
            k:v
            for k,v in data.items()
            if k in cls.__builder_fields__
        }
        
        return cls(**params)
        

    def build(self, **args) -> list[str]:
        cls = type(self)
        result = list()
        for k,v in self.fields().items():
            field = cls.__builder_fields__[k]
            value=field.serializer(v)
            result.append(field.string.format(value=value))
        return result


 
class Pyright:
    create_sub = Field('--createstub {value}')
    