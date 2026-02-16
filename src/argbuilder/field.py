from typing import Any, Callable, Final, Iterable, Literal, cast
from dataclasses import dataclass, asdict

VALUE_TOKEN = "{value}"

class NotSet(object):
    def __repr__(self) -> str:
        return f'NOT_SET({hex(id(self))})'

NOT_SET = NotSet()

type Maybe[T] = T|NotSet
type TypeAnnotation[T] = Maybe[T]
type Default[T] = Maybe[T]

DATACLASS_OPTIONS = dict(
    init         = True,
    repr         = True,
    eq           = True,
    order        = False,
    unsafe_hash  = False,
    frozen       = False,
    match_args   = False,
    kw_only      = False,
    slots        = False,
    weakref_slot = False,
)

@dataclass(**DATACLASS_OPTIONS)
class Field[T: Any]:
    string: Iterable[str]
    cls: None | type[T]
    serializer: Callable[[T], Iterable[str]]
    default: Default[T] = NOT_SET
    annotation: TypeAnnotation[type[T]] = NOT_SET

    def dump(
        self, 
        mode: Literal['json', 'python'] = 'python', 
    ) -> dict:
        base = asdict(self)
        base.pop('cls')

        if mode == 'python':
            return base
        
        base.pop('serializer')
        base['annotation'] = base['annotation'].__name__

        if isinstance(base['default'], NotSet):
            base.pop('default')

        return base

DEFAULT_SERIALIZER: Final[Callable[[Any], str]] = lambda x: str(x)

def FieldSetter[T: Any](
    string: Iterable[str] | str, 
    serializer: Callable[[T], Iterable[str] | str] = DEFAULT_SERIALIZER,
    default: Default[T] = NOT_SET,
    annotation: TypeAnnotation[type[T]] = NOT_SET,
):
    string = [string] if isinstance(string, str) else string

    result = Field[T](
        string=string,
        annotation=annotation,
        cls=None,
        serializer=serializer,
        default=default
    )

    return cast(T, result)

type AnyField = Field[object]
