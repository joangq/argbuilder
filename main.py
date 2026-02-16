from argbuilder import Command, Field

class MyCommand(Command):
    threads: int = Field(['--threads', '{value}'], serializer=lambda x: str(x))
    verbose: bool = Field('{value}', serializer=lambda x: ['--verbose'] if x else [])

# print(MyCommand(verbose=True, threads=2).build()) # -> ['mycommand', '--verbose', '--threads', '2']
# print(MyCommand(verbose=False, threads=1).build()) # -> ['mycommand', '--threads', '1']

class OtherCommand(Command):
    def arg0(self) -> str:
        import platform
        
        match platform.system():
            case 'Windows': return 'foo.cmd'
            case 'Linux': return 'foo.sh'
            case _: return 'foo'

    verbose: bool = Field('--verbose')

# print(OtherCommand(verbose=True).build()) # -> ['foo.cmd', '--verbose]
# print(OtherCommand(verbose=False).build()) # -> ['foo.cmd']

class Echo(Command):
    arg0 = 'echo'

    message: str = Field('{value}')

command = Echo(message='hello')
command.run(pretty=True, verbose=False).stdout.decode().strip()
print(command.dump_json(indent=2))