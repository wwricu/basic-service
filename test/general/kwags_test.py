class Base:
    def __init__(
        self,
        a: int,
        *args,
        **kwargs
    ):
        print(args, kwargs)
        self.a = a


class Derive(Base):
    b: int
    pass


"""
key arguments not catch by derived class __init__
will be passed to the base class, which caused
invalid column key based to sqlalchemy base model.
"""
d = Derive(a=2, b=3, c=4)
