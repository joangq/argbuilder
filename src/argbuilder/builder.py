from .field import BuilderField, AnyField, NOT_SET
from .exception import InvalidFieldError
from typing import cast

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
            value=field.serializer(v)
            result.append(field.string.format(value=value))
        
        return [*result, *args]
    
    def __eq__(self, other: object):
        if not isinstance(other, Builder):
            return False
        
        return (
            self.fields() == other.fields()
            and self.class_fields() == other.class_fields()
        )