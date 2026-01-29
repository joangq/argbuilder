from typing import Any, Callable, Iterable, cast
from dataclasses import dataclass

VALUE_TOKEN = "{value}"

class NotSet(object): ...
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
class BuilderField[T: Any]:
    string: Iterable[str] | str
    cls: None | type[T]
    serializer: Callable[[T], Iterable[str] | str]
    default: Default[T] = NOT_SET
    annotation: TypeAnnotation[type[T]] = NOT_SET

def Field[T: Any](
    string: Iterable[str] | str, 
    serializer: Callable[[T], Iterable[str] | str] = lambda x: str(x),
    default: Default[T] = NOT_SET,
    annotation: TypeAnnotation[type[T]] = NOT_SET,
):

    result = BuilderField[T](
        string=string,
        annotation=annotation,
        cls=None,
        serializer=serializer,
        default=default
    )

    return cast(T, result)

type AnyField = BuilderField[object]
