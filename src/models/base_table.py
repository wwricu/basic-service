from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class BaseTable(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)

    def __init__(self, id: int | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = id
