"""
class Chainable:
    def __init__(self, **kwargs):
        self._parent = None
        self._data = kwargs

    def __getattribute__(self, name):
        try:
            attr = super().__getattribute__(name)
        except AttributeError:
            raise

        if isinstance(attr, type) and issubclass(attr, Chainable):
            return BoundChild(attr, self)
        return attr

    def unwrap(self):
        parts = []
        node = self
        while node:
            cls = type(node).__name__
            for k, v in node._data.items():
                parts.append(f"{cls}.{k}={v}")
            node = node._parent
        return ", ".join(reversed(parts))


class BoundChild:
    def __init__(self, cls, parent):
        self.cls = cls
        self.parent = parent

    def __call__(self, **kwargs):
        child = self.cls(**kwargs)
        child._parent = self.parent
        return child

class Outer(Chainable):
    ...
    
class A(Outer):
    class B(Outer):
        class C(Outer):
            ...

print(A(x=1).B(y=2).C(z=3).unwrap())
"""

from argbuilder import Builder, FieldSetter

class A(Builder):
    x: int = FieldSetter('--A-x={value}')

    class B(Builder):
        y: int = FieldSetter('--B-y={value}')


print(A(x=1).B(y=2).build(with_self=True))