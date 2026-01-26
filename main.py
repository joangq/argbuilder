from argbuilder import Builder, Field
from pathlib import Path

class Command(Builder):
    x = Field('...', serializer=lambda x: str(x.resolve()), annotation=Path)