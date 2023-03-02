from __future__ import annotations
from pydantic import BaseModel


class ClassA(BaseModel):
    b: ClassB = None


class ClassB(BaseModel):
    a: ClassA = None


if __name__ == '__main__':
    b = ClassB()
    a = ClassA()
    b.a = a
    a.b = b
    print(a.dict())
