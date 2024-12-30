from sqlalchemy import create_engine, Engine
from wwricu.domain.entity import Base


def test_create_database():
    sync_engine: Engine = create_engine('sqlite:///wwr.sqlite3', echo=True)
    Base.metadata.create_all(sync_engine)
