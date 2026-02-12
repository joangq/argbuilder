# Argbuilder — Declarative subprocess interfaces

Argbuilder is a library that allows to integrate commandline apps into Python via declarative interfaces. It serves as a more robust alternative to `subprocess.run`.

### Usage

```python
from argbuilder import Command, Field

class MyCommand(Command):
    threads: int = Field(['--threads', '{value}'], serializer=lambda x: str(x))
    verbose: bool = Field('{value}', serializer=lambda x: ['--verbose'] if x else [])

print(MyCommand(verbose=True, threads=2).build()) # -> ['mycommand', '--verbose', '--threads', '2']
print(MyCommand(verbose=False, threads=1).build()) # -> ['mycommand', '--threads', '1']

class OtherCommand(Command):
    def arg0(self) -> str:
        import platform
        
        match platform.system():
            case 'Windows': return 'foo.cmd'
            case 'Linux': return 'foo.sh'
            case _: return 'foo'

    verbose: bool = Field(
        '--verbose={value}',
        serializer=lambda x: str(x).lower()
    )

print(OtherCommand().build()) # -> ['foo.cmd']
print(OtherCommand(verbose=False).build()) # -> ['foo.cmd', '--verbose=false']
```


