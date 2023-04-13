from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class BaseTable(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)

    def __init__(self, id: int | None = None, *args, **kwargs):
        # All extra arguments must be handled before here
        _, _ = args, kwargs
        super().__init__()
        self.id = id

    """
    WARNING:
    THIS IS NOT STABLE
    SQLAlchemy uses __getattr__ methods for its functionality,
    so it must NOT be shadowed,
    or the implementation of BaseModel will NOT be set.
    A compromise alternative is to check whether the unfounded
    attribute is one of our keys and return None if true.
    """
    def __getattr__(self, name: str):
        if name in self.__mapper__.c.keys():
            return None
        raise AttributeError
