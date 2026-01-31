from argbuilder import Command, Field
from functools import partial

type LogLevel = str
class Celery(Command):
    app: str = Field(['-A', '{value}'])
    worker_name: str = Field('{value}')
    log_level: LogLevel = Field('--loglevel={value}')

class Uv(Command):
    type subcommands = object
    
    command: 'Uv.subcommands' = Field('{value}', partial(Command.build, with_self=True))
    upgrade: bool = Field('-U')

    class run(Command):
        module: Command = Field('{value}', partial(Command.build, with_self=True))
    
    class add(Command):
        dependencies: list[str] = Field('{value}')

celery = Celery(
    app = 'foobar.celery_app.celery_app',
    worker_name = 'worker',
    log_level = 'info'
)

command = Uv(upgrade=False).run(module=celery)

print(command.build(with_self=True))