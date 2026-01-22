from random import Random

from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from wwricu.domain.entity import Base
from wwricu.main import app


def show_ddl():
    sync_engine = create_engine('sqlite:///:memory:', echo=True)
    Base.metadata.create_all(sync_engine)


client = TestClient(app)
random = Random()
