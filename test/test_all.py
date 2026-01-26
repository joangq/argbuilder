# type: ignore
from argbuilder import Builder, Field
from argbuilder.field import BuilderField
from argbuilder.exception import InvalidFieldError
import pytest

def test_no_annotation():
    with pytest.raises(InvalidFieldError):
        class NoAnn(Builder):
            no_ann = Field('--no-anotation')

    class FieldAnn(Builder):
        field_ann = Field('--field-ann', annotation=int)
    
    assert isinstance(FieldAnn, type)
    assert FieldAnn.__annotations__['field_ann'] == int

def test_build():
    class Command(Builder):
        verbose: bool = Field('--verbose')
        keyword_argument: str = Field('--keyword-argument {value}')
        equals_argument: int = Field(
            '--equals-argument={value}', 
            serializer=lambda x: str(x+1),
            annotation=int,
        )


    assert isinstance(Command, type)
    class_fields = Command.class_fields()
    assert 'verbose' in class_fields
    assert 'keyword_argument' in class_fields
    assert 'equals_argument' in class_fields

    for v in class_fields.values():
        assert isinstance(v, BuilderField)
    
    args = dict(
        verbose = True,
        keyword_argument = 'a',
        equals_argument = 2
    )


    command = Command(**args)
    command_from_dict = Command.from_dict(args)

    assert command == command_from_dict
    
    with pytest.raises(KeyError):
        Command(**(args|{'otherarg': 2}))

    build = command.build()
    assert build == command_from_dict.build()

    assert repr(command) == "Command(verbose=True, keyword_argument=a, equals_argument=2)"

def test_inequality():
    class Command(Builder):
        x: int = Field(
            '--equals-argument={value}', 
            serializer=lambda x: str(x+1),
            annotation=int,
        )
    
    class OtherCommand(Builder):
        x: int = Field(
            '--equals-argument={value}', 
            serializer=lambda x: str(x+1),
            annotation=int,
        )

    assert Command(x=1) != OtherCommand(x=1)
    assert Command(x=1) != {'x': 1}

def test_default():
    class Command(Builder):
        x: int = Field('...', default=2)

    assert Command().x == 2