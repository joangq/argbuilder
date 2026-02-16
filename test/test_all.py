# type: ignore
from argbuilder import Command, Field
from argbuilder.field import Field as CommandField
from argbuilder.exception import InvalidFieldError
import pytest

def test_no_annotation():
    with pytest.raises(InvalidFieldError):
        class NoAnn(Command):
            no_ann = Field('--no-anotation')

    class FieldAnn(Command):
        field_ann = Field('--field-ann', annotation=int)
    
    assert isinstance(FieldAnn, type)
    assert FieldAnn.__annotations__['field_ann'] == int

def test_build():
    class Foo(Command):
        verbose: bool = Field('--verbose')
        keyword_argument: str = Field('--keyword-argument {value}')
        equals_argument: int = Field(
            '--equals-argument={value}', 
            serializer=lambda x: str(x+1),
            annotation=int,
        )


    assert isinstance(Foo, type)
    class_fields = Foo.class_fields()
    assert 'verbose' in class_fields
    assert 'keyword_argument' in class_fields
    assert 'equals_argument' in class_fields

    for v in class_fields.values():
        assert isinstance(v, CommandField)
    
    args = dict(
        verbose = True,
        keyword_argument = 'a',
        equals_argument = 2
    )


    command = Foo(**args)
    command_from_dict = Foo._from_dict(args)

    assert command == command_from_dict
    
    with pytest.raises(KeyError):
        Foo(**(args|{'otherarg': 2}))

    build = command.build(with_self=False)
    assert build == command_from_dict.build(with_self=False)

    assert repr(command) == "Foo(verbose=True, keyword_argument=a, equals_argument=2)"

def test_inequality():
    class Foo(Command):
        x: int = Field(
            '--equals-argument={value}', 
            serializer=lambda x: str(x+1),
            annotation=int,
        )
    
    class OtherCommand(Command):
        x: int = Field(
            '--equals-argument={value}', 
            serializer=lambda x: str(x+1),
            annotation=int,
        )

    assert Foo(x=1) != OtherCommand(x=1)
    assert Foo(x=1) != {'x': 1}

def test_default():
    class Foo(Command):
        x: int = Field('...', default=2)

    assert Foo().x == 2

def test_list_field():
    class Foo(Command):
        command: list[str] = Field('prefix otherprefix {value} othersuffix suffix', serializer=lambda x: x)

    assert Foo(command=['foo', 'kw=2']).build(with_self=False) == ['prefix otherprefix', 'foo', 'kw=2', 'othersuffix suffix']
    
    class Foo(Command):
        kw: int = Field(['kw', '{value}'])

    assert Foo(kw=2).build(with_self=False) == ['kw', '2']

    
    class Foo(Command):
        files: list[str] = Field(['files', '[', '{value}', ']'], lambda x: x)

    assert Foo(files=['a', 'b']).build(with_self=False) == ['files', '[', 'a', 'b', ']']


def test_subcommands():
    class Top(Command):
        subcommand: 'Top.Sub | Top.Bus' = Field('{value}')
        arg: str = Field('--top-arg={value}')

        class Sub(Command):
            x: str = Field('--sub-x={value}')
        
        class Bus(Command):
            y: str = Field('--bus-y={value}')

    expected = ['top', '--top-arg=a', 'sub', '--sub-x=b']    
    assert (
        expected
        == Top(arg='a').Sub(x='b').build(with_self=True)
        == Top(arg='a').Sub._from_dict({'x': 'b'}).build(with_self=True)
        == Top._from_dict({'arg': 'a'}).Sub(x='b').build(with_self=True)
        == Top._from_dict({'arg': 'a'}).Sub._from_dict({'x': 'b'}).build(with_self=True)
        
    )

def test_arg0():
    class Foo(Command):
        def arg0(self) -> str:
            return 'bar'
        
    assert Foo().build(with_self=True) == ['bar']

    class Foo(Command): ...

    assert Foo().build(with_self=True) == ['foo']

    class Foo(Command):
        arg0 = 'bar'
    
    assert Foo().build(with_self=True) == ['bar']

    class Foo(Command):
        arg0 = 123
    
    with pytest.raises(TypeError):
        Foo().build(with_self=True)
        
def test_run():
    class Echo(Command):
        arg0 = 'echo'
        message: str = Field('{value}')

    command = Echo(message='hello')
    assert command.build(with_self=True) == ['echo', 'hello']
    
    import subprocess
    result = command.run()

    assert isinstance(result, subprocess.CompletedProcess)
    assert result.stdout == b'hello\n'
    assert result.stderr == b''
    assert result.returncode == 0

    class NonExistent(Command):
        arg0 = 'non-existent'

    result = NonExistent().run()
    assert result.returncode == 1
    assert result.stdout == b''

def test_default_serializers():
    import pathlib

    class Foo(Command):
        path: pathlib.Path = Field('--path={value}')
        verbose: bool = Field('--verbose')

    foopath = pathlib.Path('foo').resolve()
    full_foopath = str(foopath.resolve())
    command = Foo(path=foopath, verbose=True)
    assert command.build(with_self=False) == [f'--path={full_foopath}', '--verbose']

    command = Foo(path=foopath, verbose=False)
    assert command.build(with_self=False) == [f'--path={full_foopath}']

def test_dump_load():
    class Foo(Command):
        x: int = Field('{value}')
        y: str = Field('--y={value}')
    
    foo = Foo(x=1, y='hello')

    # roundtrip
    assert foo == Foo.loads(foo.dump_json())